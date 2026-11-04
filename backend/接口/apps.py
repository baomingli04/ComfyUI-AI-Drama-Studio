"""接口 app 配置。"""
from django.apps import AppConfig


class 接口配置(AppConfig):
    """平台后端唯一 app：所有模型、控制器、路由都在这里。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = '接口'
    verbose_name = '平台接口'

    def ready(self):
        """启动任务执行器（Comfy / LLM 两个工作线程）。重复调用无害。"""
        from 能力.提交并等待 import 启动执行器
        启动执行器()
