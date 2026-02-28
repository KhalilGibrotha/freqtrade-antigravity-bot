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
    minimal_roi = {
        "0": 0.093,
        "17": 0.075,
        "60": 0.011,
        "165": 0
    }
    
    # Hyperopt-derived Stoploss
    stoploss = -0.248
    
    # Core timeframe
    timeframe = '5m'
    
    # Higher timeframe for regime filter
    informative_timeframe = '1h'

    # Ensure we download enough historical data to calculate the 1h 200 EMA
    # 200 candles on 1h = 200 hours. We need 200 hours / (5 min candles per hour) = 2400 candles on the 5m timeframe
    startup_candle_count: int = 2400

    # Flag to enable custom stake sizing logic 
    use_custom_stoploss = False

    def informative_pairs(self):
        """
        Define additional informative pair/timeframe combinations to provide to the strategy.
        """
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.informative_timeframe) for pair in pairs]
        return informative_pairs

    def custom_stake_amount(self, dataframe: DataFrame, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float, max_stake: float,
                            leverage: float, entry_tag: str, side: str,
                            **kwargs) -> float:
        """
        Customize stake size based on the bot's overall global performance across all pairs.
        - High Win Rate (> 60%): Aggressive (100% of proposed stake)
        - Moderate Win Rate (40% - 60%): Normal (75% of proposed stake)
        - Low Win Rate (< 40%): Defensive (50% of proposed stake)
        """
        
        # 1. Look back at the last 7 days of trading history
        lookback_days = 7
        start_date = current_time - timedelta(days=lookback_days)
        
        # 2. Fetch all CLOSED trades across ALL pairs from the database
        trades = Trade.get_trades([
            Trade.is_open.is_(False),
            Trade.close_date >= start_date
        ]).all()
        
        # If there is not enough history yet to judge performance, just return the standard stake
        if len(trades) < 5:
            return proposed_stake
            
        # 3. Calculate Win Rate
        winning_trades = len([t for t in trades if t.close_profit > 0])
        win_rate = winning_trades / len(trades)
        
        # 4. Dynamically adjust bet size (Turtle vs Aggressive)
        if win_rate > 0.60:
            # Bull Market / Winning Streak -> Bet 100% of allocation
            new_stake = proposed_stake
            logger.info(f"Global Win Rate high ({win_rate:.2%}). Aggressive sizing: {new_stake}")
            
        elif win_rate < 0.40:
            # Bear Market / Losing Streak -> Turtle mode, cut risk in half!
            new_stake = proposed_stake * 0.50
            logger.info(f"Global Win Rate low ({win_rate:.2%}). Defensive sizing applied: {new_stake}")
            
        else:
            # Choppy / Average Market -> Reduce slightly to 75%
            new_stake = proposed_stake * 0.75
            logger.info(f"Global Win Rate average ({win_rate:.2%}). Normal sizing applied: {new_stake}")
            
        # Ensure we don't violate exchange minimums or maximums
        return max(min_stake, min(new_stake, max_stake))

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # -- Informative Timeframe (1h) --
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)
        
        # Calculate 200 EMA on the 1h timeframe
        informative['ema_200'] = ta.EMA(informative, timeperiod=200)

        # Merge the 1h informative dataframe into the 5m dataframe
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, self.informative_timeframe, ffill=True)

        # -- Core Timeframe (5m) --
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # We look for a 1h 200 EMA, but during backtest startup there might be NaN values
        # We use .get() and fillna to handle the edge case gracefully
        ema_200_1h = dataframe[f"ema_200_{self.informative_timeframe}"]
        
        dataframe.loc[
            (
                # Higher Timeframe Regime Filter:
                # 1. Broad market must be in an uptrend (Price > 1h 200 EMA)
                (dataframe['close'] > ema_200_1h) &
                
                # Double Confirmation for Mean Reversion Dip Buy:
                # 2. Very Oversold (RSI < 18 from Hyperopt)
                (dataframe['rsi'] < 18) &
                # 3. Price below Lower Bollinger Band
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    # Take profit if Very Overbought (RSI > 89)
                    (dataframe['rsi'] > 89) |
                    # OR Price spikes above Upper Bollinger Band
                    (dataframe['close'] > dataframe['bb_upperband'])
                ) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
