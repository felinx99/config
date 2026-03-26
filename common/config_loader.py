import tomllib
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# 定位公共目录
BASE_DIR = Path(__file__).parent.absolute()

class PathConfig(BaseModel):
    # 使用 Field 设置默认值或描述
    tdx_raw: str = Field(default="D:/data/tdx", description="通达信原始数据路径")
    parquet_store: str = Field(..., description="必须提供的 Parquet 存储路径")

    @field_validator("tdx_raw")
    @classmethod
    def check_path_exists(cls, v: str) -> str:
        # 校验器逻辑：如果路径不存在，打印警告或报错
        if not Path(v).exists():
            print(f"警告: 路径 {v} 目前不存在")
        return v

class BacktestConfig(BaseModel):
    initial_cash: float = 100000.0
    default_slippage: float = 0.001

class MasterConfig(BaseModel):
    paths: PathConfig
    backtest: BacktestConfig
    # 允许扩展其他 Section

class SecretSettings(BaseModel):
    supabase_key: str
    binance_api_secret: str

    class Config:
        env_file = ".env"  # 告诉 Pydantic 自动去 .env 找这些变量
        env_file_encoding = "utf-8"


def load_settings(local_override: Optional[Path] = None) -> MasterConfig:
    def _load_toml(p: Path) -> dict:
        with open(p, "rb") as f:
            return tomllib.load(f)

    def _deep_update(dst: dict, src: dict) -> dict:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                _deep_update(dst[k], v)
            else:
                dst[k] = v
        return dst

    # 1) 加载主配置（兼容历史文件名）
    candidates = [BASE_DIR / "config.toml", BASE_DIR / "common_config.toml"]
    base_path = next((p for p in candidates if p.exists()), None)
    if base_path is None:
        raise FileNotFoundError(f"未找到配置文件：{', '.join([str(p) for p in candidates])}")

    raw = _load_toml(base_path)

    # 2) 如果项目有私有配置，则覆盖（进阶技巧）
    if local_override and local_override.exists():
        raw_override = _load_toml(local_override)
        raw = _deep_update(raw, raw_override)

    # 3) 将不同结构的 TOML 统一成 MasterConfig 结构
    # 期望结构: {paths: {tdx_raw, parquet_store, checkpoints}, backtest: {initial_cash, default_slippage}}
    paths = raw.get("paths", {}) if isinstance(raw, dict) else {}
    params = raw.get("params", {}) if isinstance(raw, dict) else {}
    backtest_section = raw.get("backtest", {}) if isinstance(raw, dict) else {}

    # 首选已是目标字段名；否则尝试从 common_config.toml 的字段名映射
    def pick_path(*keys: str, default: str = "") -> str:
        for key in keys:
            if key in paths and paths[key] is not None:
                return str(paths[key])
        return default

    initial_cash = (
        backtest_section.get("initial_cash")
        if isinstance(backtest_section, dict) and "initial_cash" in backtest_section
        else params.get("initial_cash", 100000.0)
    )
    default_slippage = (
        backtest_section.get("default_slippage")
        if isinstance(backtest_section, dict) and "default_slippage" in backtest_section
        else params.get("default_slippage", 0.001)
    )

    config_dict = {
        "paths": {
            "tdx_raw": pick_path("tdx_raw", "TDX_RAW", "DATA_PATH"),
            "parquet_store": pick_path("parquet_store", "PARQUET_STORE", "RESULT_PATH"),
            "checkpoints": pick_path("checkpoints", "CHECKPOINTS_PATH", "STOCKLIST_PATH", "RESULT_PATH"),
        },
        "backtest": {
            "initial_cash": float(initial_cash),
            "default_slippage": float(default_slippage),
        },
    }

    return MasterConfig(**config_dict)

CONFIG = load_settings()