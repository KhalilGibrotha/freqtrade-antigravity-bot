from freqtrade.strategy import IStrategy, merge_informative_pair
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from datetime import datetime, timedelta
from freqtrade.persistence import Trade
import logging

logger = logging.getLogger(__name__)

class CombinedStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Hyperopt-derived ROI
    # We leave this as a final failsafe, but rely primarily on the trailing stop
    minimal_roi = {
        "0": 0.093,
        "17": 0.075,
        "60": 0.011,
        "165": 0
    }
    
    # Hyperopt-derived Stoploss (Hard floor)
    stoploss = -0.248
    
    # --- NEW: Trailing Stoploss ---
    trailing_stop = True
    # Start trailing only when we reach 1% profit
    trailing_stop_positive = 0.01  
    # Trail 2% behind the maximum profit reached
    trailing_stop_positive_offset = 0.02  
    trailing_only_offset_is_reached = True

    # Core timeframe
    timeframe = '5m'
    
    # Higher timeframe for regime filter
    informative_timeframe = '1h'

    # Ensure we download enough historical data to calculate the 1h 200 EMA
    startup_candle_count: int = 2400

    # Flag to enable custom stake sizing logic 
    use_custom_stoploss = False

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.informative_timeframe) for pair in pairs]
        return informative_pairs

    def custom_stake_amount(self, dataframe: DataFrame, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float, max_stake: float,
                            leverage: float, entry_tag: str, side: str,
                            **kwargs) -> float:
        lookback_days = 7
        start_date = current_time - timedelta(days=lookback_days)
        
        trades = Trade.get_trades([
            Trade.is_open.is_(False),
            Trade.close_date >= start_date
        ]).all()
        
        if len(trades) < 5:
            return proposed_stake
            
        winning_trades = len([t for t in trades if t.close_profit > 0])
        win_rate = winning_trades / len(trades)
        
        if win_rate > 0.60:
            new_stake = proposed_stake
            logger.info(f"Global Win Rate high ({win_rate:.2%}). Aggressive sizing: {new_stake}")
        elif win_rate < 0.40:
            new_stake = proposed_stake * 0.50
            logger.info(f"Global Win Rate low ({win_rate:.2%}). Defensive sizing applied: {new_stake}")
        else:
            new_stake = proposed_stake * 0.75
            logger.info(f"Global Win Rate average ({win_rate:.2%}). Normal sizing applied: {new_stake}")
            
        return max(min_stake, min(new_stake, max_stake))

    # --- NEW: Custom Exit Pricing ---
    def custom_exit_price(self, pair: str, trade: Trade,
                          current_time: datetime, proposed_rate: float,
                          current_profit: float, exit_tag: str, **kwargs) -> float:
        """
        Dynamically calculate limit configurations for sells based on the live orderbook.
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        
        # 1. Ask the exchange for the live orderbook
        try:
            orderbook = self.dp.orderbook(pair, 1)
        except Exception:
            # If exchange API hiccups, fallback to the strategy's standard proposed rate
            return proposed_rate

        bids = orderbook['bids']
        asks = orderbook['asks']

        # Ensure orderbook came back populated
        if not bids or not asks:
            return proposed_rate

        # Get top bid/ask (index 0 is [price, volume])
        best_bid_price = bids[0][0]
        best_ask_price = asks[0][0]

        # 2. Logic: If we are exiting via a Trailing Stop (market is dropping)
        # We need to get out fast. We price our limit deeply on the bid side to guarantee a fill.
        if exit_tag == 'trailing_stop_loss':
            logger.info(f"Trailing Stop triggered for {pair}. Slamming bid at {best_bid_price}")
            return best_bid_price
            
        # 3. Logic: If we are hitting our standard ROI or Exit Signal (taking profit)
        # We are greedy. Let's aim closer to the Ask price since volume is heavily on our side.
        if exit_tag in ('roi', 'exit_signal'):
            greedy_price = best_ask_price * 0.9999 # Just barely under the ask
            logger.info(f"Profit Take triggered for {pair}. Pushing greedy limit at {greedy_price}")
            return greedy_price

        # Fallback default
        return proposed_rate

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)
        informative['ema_200'] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, self.informative_timeframe, ffill=True)

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_200_1h = dataframe[f"ema_200_{self.informative_timeframe}"]
        
        dataframe.loc[
            (
                (dataframe['close'] > ema_200_1h) &
                (dataframe['rsi'] < 18) &
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    (dataframe['rsi'] > 89) |
                    (dataframe['close'] > dataframe['bb_upperband'])
                ) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
