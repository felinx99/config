import tomllib
from pathlib import Path
from .schema import DATAFRAME, ConfigSchema

def load_settings(ConfigSchema):
    _instance = None

    def __new__(cls):
        #单例模式，
        if cls._instance is None:
            cls._instance = super(load_settings, cls).__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _deep_merge(self, base, user):
        """合并用户配置"""
        for key, value in user.items():
            if isinstance(value, dict) and key in base:
                base[key].update(value)
            else:
                base[key] = value

    def _apply_bindings(self, data):
        """核心：全自动绑定逻辑"""
        # 定义需要将字符串 Key ("0", "1") 转为 DATAFRAME 枚举的集合
        enum_mapped_keys = {'src_dir', 'file_extension', 'dst_dir', 'date_fmt'}

        for key, value in data.items():
            # A. 处理特定的枚举映射字典
            if key in enum_mapped_keys and isinstance(value, dict):
                processed = {}
                for k, v in value.items():
                    try:
                        enum_k = DATAFRAME(int(k))
                        # 如果是目标路径，转为 Path 对象
                        processed[enum_k] = Path(v) if key == 'dst_dir' else v
                    except:
                        processed[k] = v
                setattr(self, key, processed)

            # B. 处理 data_frame 列表（将 [0, 1] 转为 [DATAFRAME.DAY, ...]）
            elif key == 'data_frame' and isinstance(value, list):
                setattr(self, key, [DATAFRAME(i) for i in value])

            # C. 普通项（paths, params, tushare, SHORT, etc.）
            else:
                setattr(self, key, value)

    def _init_loader(self):
        # 定位公共目录, 允许项目使用自定义配置
        BASE_DIR = Path(__file__).parent.absolute()
        base_toml = BASE_DIR / "settings.toml"
        user_toml = BASE_DIR / "user_settings.toml"

        if not base_toml.exists():
            raise FileNotFoundError(f"Base config missing: {base_toml}")

        # 1. 加载 & 合并配置
        with open(base_toml, "rb") as f:
            final_data = tomllib.load(f)

        if user_toml.exists():
            with open(user_toml, "rb") as f:
                user_data = tomllib.load(f)
            self._deep_merge(final_data, user_data)

        # 2. 动态绑定属性
        self._apply_bindings(final_data)

CONFIG = load_settings()