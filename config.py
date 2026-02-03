# -*- coding: utf-8 -*-
"""
配置管理模块
从环境变量加载敏感配置
"""
import os
from pathlib import Path
from typing import Dict, Optional
import json
import yaml
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

class Config:
    """配置类"""

    # Telegram配置
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    CHAT_ID: str = os.getenv('CHAT_ID', '')

    # 代理配置
    PROXY_HOST: str = os.getenv('PROXY_HOST', '127.0.0.1')
    PROXY_PORT: str = os.getenv('PROXY_PORT', '7897')

    @property
    def PROXIES(self) -> Dict[str, str]:
        """获取代理配置"""
        return {
            'http': f'http://{self.PROXY_HOST}:{self.PROXY_PORT}',
            'https': f'http://{self.PROXY_HOST}:{self.PROXY_PORT}'
        }

    @property
    def telegram_enabled(self) -> bool:
        """检查Telegram是否配置"""
        return bool(self.BOT_TOKEN and self.CHAT_ID)

    def load_yaml_config(self, yaml_file: str = 'config/config.yaml') -> Dict:
        """加载YAML配置文件"""
        yaml_path = Path(__file__).parent / yaml_file
        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def validate(self) -> bool:
        """验证配置是否完整"""
        if not self.BOT_TOKEN:
            print("警告: BOT_TOKEN未设置")
            return False
        if not self.CHAT_ID:
            print("警告: CHAT_ID未设置")
            return False
        return True

# 全局配置实例
config = Config()

# 导出常量（保持向后兼容）
BOT_TOKEN = config.BOT_TOKEN
CHAT_ID = config.CHAT_ID
PROXIES = config.PROXIES
