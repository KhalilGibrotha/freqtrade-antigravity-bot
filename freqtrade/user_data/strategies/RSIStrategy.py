from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class RSIStrategy(IStrategy):
    INTERFACE_VERSION = 3
    minimal_roi = { "0": 0.1 }
    stoploss = -0.25
    timeframe = '5m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Buy when deeply oversold
        dataframe.loc[
            (
                (dataframe['rsi'] < 25) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Sell when overbought
        dataframe.loc[
            (
                (dataframe['rsi'] > 55) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
