import logging
from functools import reduce
from typing import Dict, Any, Optional

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import freqtrade.vendor.qtpylib.indicators as qtpylib

logger = logging.getLogger(__name__)

class FreqAIStrategy(IStrategy):
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.093, "17": 0.075, "60": 0.011, "165": 0}
    stoploss = -0.248
    timeframe = '5m'
    informative_timeframe = '1h'
    use_custom_stoploss = False

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.informative_timeframe) for pair in pairs]

    def feature_engineering_expand_all(self, dataframe: DataFrame, period: int, metadata: Dict[str, Any], **kwargs):
        dataframe[f"%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=period, stds=2)
        dataframe[f"%-bb_lowerband-period"] = bollinger["lower"]
        dataframe[f"%-bb_upperband-period"] = bollinger["upper"]
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: DataFrame, metadata: Dict[str, Any], **kwargs):
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-volume"] = dataframe["volume"]
        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, metadata: Dict[str, Any], **kwargs):
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)
        informative['ema_200'] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, self.informative_timeframe, ffill=True)
        col = f"ema_200_{self.informative_timeframe}"
        if col in dataframe.columns:
            dataframe[f"%-{col}"] = dataframe[col]
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: Dict[str, Any], **kwargs):
        label_period = self.freqai_info.get("feature_parameters", {}).get("label_period_candles", 20)
        dataframe["&target"] = (
            dataframe["close"].shift(-label_period) / dataframe["close"] - 1
        )
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        informative = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)
        informative['ema_200'] = ta.EMA(informative, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, informative, self.timeframe, self.informative_timeframe, ffill=True)

        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        col = f"ema_200_{self.informative_timeframe}"
        ema_200_1h = dataframe[col] if col in dataframe.columns else 0
        
        enter_long_conditions = [
            dataframe.get("do_predict", 0) == 1,
            dataframe.get("&target", 0) > 0.01,
            dataframe['close'] > ema_200_1h,
            dataframe['volume'] > 0
        ]
        
        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                "enter_long",
            ] = 1
            
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_long_conditions = [
            dataframe.get("do_predict", 0) == 1,
            dataframe.get("&target", 0) < -0.01,
            dataframe['volume'] > 0
        ]
        
        if exit_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, exit_long_conditions),
                "exit_long",
            ] = 1
            
        return dataframe

    def custom_stake_amount(self, pair: str, current_time, current_rate: float,
                            proposed_stake: float, min_stake: Optional[float], max_stake: float,
                            leverage: float, entry_tag: Optional[str], side: str,
                            **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is not None and len(dataframe) > 0:
            last_candle = dataframe.iloc[-1].squeeze()
            predicted_return = last_candle.get("&target", 0)
            if predicted_return > 0.03:
                return proposed_stake
            elif predicted_return > 0.02:
                return proposed_stake * 0.75
            elif predicted_return > 0.01:
                return proposed_stake * 0.50
        return proposed_stake
