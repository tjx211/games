import os
import yaml

class ConfigManager:
    _config = None

    @classmethod
    def load(cls):
        if cls._config is None:
            # 自动定位到根目录的 config.yaml
            config_path = os.path.join(os.path.dirname(__file__), '../../config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._config = yaml.safe_load(f)
        return cls._config

    @classmethod
    def get(cls, section, subsection=None):
        cfg = cls.load()
        if subsection:
            return cfg.get(section, {}).get(subsection, {})
        return cfg.get(section, {})