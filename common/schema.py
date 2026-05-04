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



class ConfigSchema:
    '''
    ConfigSchema 定义的是你程序最终想要访问的接口形状
    1. 需要与settings.toml中的配置项一一对应
    2. 它与setting.toml层级不同
    3. 在_apply_bindings做了层级转换, 方便直接调用子层级
    4. 方便 IDE 补全, 是按ConfigSchema节点来引用的
    '''
    #全局变量区
    PERIOD: List[str]
    EXCHANGE: List[str]
    SHORT: int
    MID: int
    LONG: int
    TARGET_BLOCK_NAME: str
    YEAR_DAYS: float
    # 普通节点区，注意基础路径和派生路径
    base_path: Dict[str, Path]
    inferred_path: Dict[str, Path]
    tushare: Dict[str, str]
    params: Dict[str, Any]
    stock_csvtype: Dict[str, str]
    sector_type: Dict[str, str]
    # 节点区：DATAFRAME映射表区，将被转换为DATAFRAME,枚举为Key
    src_dir: Dict[DATAFRAME, str]
    file_extension: Dict[DATAFRAME, str]
    tdx_data_path: Dict[DATAFRAME, Path]
    date_fmt: Dict[DATAFRAME, str]
    #节点区：DATAFEED映射表区，将被转换为DATAFEED, 枚举为Key
