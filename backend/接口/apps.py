# -*- coding: utf-8 -*-
"""接口 app 配置。"""
import os
import sys
import traceback

from django.apps import AppConfig


class 接口配置(AppConfig):
    """平台后端唯一 app：所有模型、控制器、路由都在这里。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = '接口'
    verbose_name = '平台接口'

    def ready(self):
        """启动任务执行器（Comfy / LLM / 本地计算工作线程）。重复调用无害。"""
        # 只在真正对外服务请求的进程里启动（2026-11-04 审查补丁）：
        # runserver 带热重载时有父（文件监视）子（服务）两个进程，django.setup()
        # 两边都会执行 ready()（django/core/management/__init__.py 的
        # ManagementUtility.execute），执行器若两边都起就是两套线程并发认领任务
        # ——领取行锁在事务提交时不迁移状态，防不住同一任务被认领两次。
        # 热重载子进程 RUN_MAIN=true；--noreload 时没有子进程，直接启动；
        # 非 runserver 命令（shell/migrate）一律不起执行器，避免静态分析时误领任务。
        if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
            在服务进程 = (
                os.environ.get('RUN_MAIN') == 'true'
                or '--noreload' in sys.argv
            )
            if 在服务进程:
                # 启动对账（2026-11-04 崩溃恢复补丁）：把残留过程态任务判「中断」
                try:
                    from 能力.提交并等待 import 启动对账
                    启动对账()
                except Exception:
                    traceback.print_exc()
                from 能力.提交并等待 import 启动执行器
                启动执行器()
