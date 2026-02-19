from freqtrade.strategy import IStrategy
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
    
    timeframe = '5m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # Double Confirmation:
                # 1. Very Oversold (RSI < 18 from Hyperopt)
                (dataframe['rsi'] < 18) &
                # 2. Price below Lower Bollinger Band
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
