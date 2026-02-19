from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class ShortStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # Futures config
    can_short = True
    
    # ROI (Shorts profit when price goes down)
    minimal_roi = {
        "0": 0.05,  # Take 5% profit
        "30": 0.02, # Take 2% profit after 30 mins
        "60": 0.01
    }
    
    stoploss = -0.10
    timeframe = '5m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ENTER SHORT when Overbought and Price > Upper Band
        dataframe.loc[
            (
                (dataframe['rsi'] > 75) & 
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['volume'] > 0)
            ),
            'enter_short'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EXIT SHORT when Oversold (cover position)
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &
                (dataframe['volume'] > 0)
            ),
            'exit_short'] = 1
        return dataframe
