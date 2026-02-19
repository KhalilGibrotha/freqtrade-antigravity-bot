from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class SniperStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # 1. ROI: We aim for larger moves since we pick bottoms
    minimal_roi = {
        "0": 0.10,  # Aim for 10%
        "40": 0.05, # Settling for 5% after 40 mins
        "80": 0.02  # Settling for 2% after 80 mins
    }
    
    # 2. Stoploss: Tighter than usual because if we are wrong about the "bottom", we bail
    stoploss = -0.05
    
    timeframe = '5m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Volume Moving Average (for detecting spikes)
        dataframe['volume_mean_30'] = dataframe['volume'].rolling(window=30).mean()
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # Condition 1: Extreme Oversold (RSI < 20)
                (dataframe['rsi'] < 20) &
                
                # Condition 2: Volume moves (2x average) - Panic Selling / Capituluation
                (dataframe['volume'] > (dataframe['volume_mean_30'] * 2)) &
                
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Standard exit on RSI recovery or ROI
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
