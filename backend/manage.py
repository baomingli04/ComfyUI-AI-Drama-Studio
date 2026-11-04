#!/usr/bin/env python
"""命令行管理入口：python manage.py <子命令>"""
import os
import sys


def 主函数():
    """设置默认配置模块，并交给 Django 命令行执行。"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
    # 端口占用互斥：放在 django.setup() 之前，被拒绝的进程连数据库都不会连、
    # 执行器线程也不会起（多个执行器抢同一条任务 = 重复提交给 ComfyUI）。
    from 接口.启动互斥 import 启动前检查
    启动前检查(sys.argv)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as 导入异常:
        raise ImportError(
            '导入 Django 失败，请确认已激活 backend/.venv 虚拟环境。'
        ) from 导入异常
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    主函数()
