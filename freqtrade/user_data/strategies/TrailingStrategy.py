from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class TrailingStrategy(IStrategy):
    INTERFACE_VERSION = 3
    
    # ROI: We set high ROI targets because we want the trailing stop to close the trade
    minimal_roi = {
        "0": 0.5  # 50% profit target (unlikely to hit, lets trailing stop work)
    }
    
    # 1. Stoploss: Initial hard stop
    stoploss = -0.10
    
    # 2. Trailing Stop: Logic to lock in gains
    trailing_stop = True
    trailing_stop_positive = 0.01  # trailing stop jumps to 1% behind price
    trailing_stop_positive_offset = 0.02  # ...but only after 2% profit is reached
    trailing_only_offset_is_reached = True # Only trail once the offset is reached
    
    timeframe = '5m'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSIs
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # Use same conservative entry as CombinedStrategy
                (dataframe['rsi'] < 30) & # Relaxed slightly from 18 to get more trades for testing
                (dataframe['close'] < dataframe['bb_lowerband']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # We primarily rely on Trailing Stop, but keep the "Overbought" safety net
        dataframe.loc[
            (
                (dataframe['rsi'] > 85) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1
        return dataframe
