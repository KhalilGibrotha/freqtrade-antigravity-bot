from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class RSIHyperoptStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Minimal ROI - Will be optimized
    minimal_roi = { "0": 0.1 }
    
    # Stoploss - Will be optimized
    stoploss = -0.25
    
    timeframe = '5m'

    # Hyperopt parameters
    buy_rsi = IntParameter(10, 40, default=25, space="buy")
    sell_rsi = IntParameter(50, 90, default=55, space="sell")
    
    # Optional: Optimize stoploss and ROI (requires specific configuration, 
    # but we can set up the strategy class to handle it logic-wise if needed)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
