import tomllib
import typing

from . import schema
from .schema import ConfigSchema
from pathlib import Path

class ConfigLoader(ConfigSchema):
    _instance = None

    def __new__(cls):
        #单例模式，
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._init_loader()
        return cls._instance
    
    def _deep_merge(self, base, user):
        """合并用户配置"""
        for key, value in user.items():
            if isinstance(value, dict) and key in base:
                base[key].update(value)
            else:
                base[key] = value

    def _resolve_paths(self, data: dict):
        """解析路径占位符"""
        # 1. 获取基础路径（从 paths 节点获取）
        base_vars = data.get('base_path', {})
        derived_node = data.get('derived_path', {})
        
        if not base_vars or not derived_node:
            return

        # 构造替换映射表
        replacements = {f"{{{k}}}": str(v) for k, v in base_vars.items()}

        def _recursive_replace(item):
            if isinstance(item, str):
                if '{' in item and '}' in item:
                    for placeholder, real_val in replacements.items():
                        item = item.replace(placeholder, real_val)
                return item
            
            elif isinstance(item, dict):
                return {k: _recursive_replace(v) for k, v in item.items()}
            
            elif isinstance(item, list):
                return [_recursive_replace(i) for i in item]
            
            return item

        # 执行解析并写回
        data['derived_path'] = _recursive_replace(derived_node)

    def _apply_bindings(self, data:dict):
        """核心：全自动绑定逻辑"""
        # --- 收集所有待处理节点 ---
        all_configs = {}
        
        # 基础节点
        for k, v in data.items():
            if k not in ('base_path', 'derived_path'):
                all_configs[k] = v
        

        all_configs['base_path'] = data.get('base_path', {})

        # 派生节点扁平化,取消派出节点层级，直接访问子层级
        derived_node = data.get('derived_path', {})
        for sub_k, sub_v in derived_node.items():
            all_configs[sub_k] = sub_v

        # --- 动态映射与绑定 ---
        type_hints = typing.get_type_hints(ConfigSchema)
        for key, value in all_configs.items():
            hint = type_hints.get(key)
            
            # --- 场景 A：处理字典类型的映射 (如 dst_dir, dst_output_dir) ---
            if hint and typing.get_origin(hint) is dict and isinstance(value, dict):
                # 提取字典定义的 Key 类型 (例如 DATAFRAME)
                args = typing.get_args(hint)
                key_type, val_type = args[0], args[1]

                # 如果 Key 是一个枚举类 (如 DATAFRAME 或 DATAFEED)
                if isinstance(key_type, type) and issubclass(key_type, int):
                    processed_dict = {}
                    for k, v in value.items():
                        try:
                            # 自动根据注解类型进行转换 (IntEnum 用 int(k), 字符串枚举直接传)
                            e_key = key_type(int(k))
                            # 如果注解要求是 Path，则转换
                            processed_val = Path(v) if val_type is Path else v
                            processed_dict[e_key] = processed_val
                        except (ValueError, TypeError):
                            processed_dict[k] = v
                    setattr(self, key, processed_dict)
                    continue

                # --- 场景 B：处理单个路径 (如 base_path 下的内容) ---
                if val_type is Path:
                    setattr(self, key, {k: Path(v) for k, v in value.items()})
                    continue
            
            # --- 场景 C：普通绑定 ---
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

        # 2. 进行路径的自适应解析
        self._resolve_paths(final_data)

        # 3. 动态绑定属性
        self._apply_bindings(final_data)

CONFIG = ConfigLoader()