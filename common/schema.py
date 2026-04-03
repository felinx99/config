from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Any

#定义了 DATAFRAME 等枚举，用于程序理解数据的逻辑结构
class DATAFRAME(IntEnum):
    DAY = 0
    MINUTE5 = 1
    MINUTE1 = 2


class DATAFEED(IntEnum):
    TDX = 0
    AKSHARE = 1

# 定义类型注解，方便 IDE 补全，需要与settings.toml中的配置项一一对应
class ConfigSchema:
    # 路径类
    paths: Dict[str, str]
    # 外部服务
    tushare: Dict[str, str]
    # 回测参数
    params: Dict[str, Any]
    # 基础列表
    PERIOD: List[str]
    EXCHANGE: List[str]
    # 周期参数
    SHORT: int
    MID: int
    LONG: int
    # 映射表（将被转换为 DATAFRAME 枚举为 Key）
    src_dir: Dict[DATAFRAME, str]
    file_extension: Dict[DATAFRAME, str]
    dst_dir: Dict[DATAFRAME, Path]
    date_fmt: Dict[DATAFRAME, str]
    # 列表（枚举值）
    data_frame: List[DATAFRAME]
    # 其它字典
    stock_csvtype: Dict[str, str]
    sector_type: Dict[str, str]