from freqtrade.strategy import IStrategy, merge_informative_pair
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

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

    def informative_pairs(self):
        """
        Define additional informative pair/timeframe combinations to provide to the strategy.
        """
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.informative_timeframe) for pair in pairs]
        return informative_pairs

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
