# -*- coding: utf-8 -*-
"""后端启动互斥：同一时间只允许一个后端实例占用 8001。

背景（2026-09-29 任务 94 / 95 重复提交）：
    每跑起一个后端进程，`接口/apps.py ready()` 就会 `启动执行器()`（Comfy / LLM 两个工作线程）。
    以前可以同时存在多棵 runserver（例如上一轮会话遗留的进程没关，又新起一棵），
    多个执行器都会去抢同一条 `状态='已创建'` 的任务，同一个任务被重复提交给 ComfyUI。
    这里在启动前先做「端口占用互斥」：8001 已被占用就直接拒绝启动。

调用位置：`manage.py` 里、`django.setup()` 之前。
    这样被拒绝的进程连数据库都不会连、执行器线程也不会起，干净退出。
    autoreload 派生的子进程（RUN_MAIN=true）跳过检查 —— 否则子进程会把自己的
    父进程当成占用者，把热重载直接打死。
"""
import os
import socket
import subprocess
import sys

# 本项目后端固定 8001（见 后端/settings.py 顶部「分端口（后端 8001）」）。
# 不传 addrport 时 Django 默认是 8000，而 8000 属于另一个项目，这里不碰。
默认端口 = 8001


def 解析地址端口(addrport):
    """从 runserver 的 addrport 参数里取 (主机, 端口)。取不到就用默认。"""
    主机, 端口 = '0.0.0.0', 默认端口
    if addrport:
        块 = addrport.rsplit(':', 1)
        if len(块) == 2:
            if 块[0]:
                主机 = 块[0].strip('[]')
            try:
                端口 = int(块[1])
            except ValueError:
                pass
    return 主机, 端口


def _监听者pid(端口):
    """用 netstat 找出监听该端口的 PID；拿不到就返回 None（只用于报错提示）。"""
    try:
        出 = subprocess.run(['netstat', '-ano', '-p', 'tcp'],
                            capture_output=True, timeout=5)
    except Exception:
        return None
    for 行 in 出.stdout.decode('gbk', 'ignore').splitlines():
        块 = 行.split()
        if len(块) >= 5 and 块[0].upper() == 'TCP' and 块[3].upper() == 'LISTENING':
            if 块[1].rsplit(':', 1)[-1] == str(端口):
                return 块[4]
    return None


def 占用者(端口, 主机='0.0.0.0'):
    """端口已被占用则返回占用者 PID 字符串，否则返回 None。"""
    被占 = False

    # ① 自己试着独占绑一次：绑得上说明没人占。
    #    Windows 上必须加 SO_EXCLUSIVEADDRUSE —— 普通 bind 允许多个 socket 共用同一端口
    #    （runserver 自己就开了 SO_REUSEADDR），不独占根本探不出占用。
    探测 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            探测.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            探测.bind((主机, 端口))
        except OSError:
            被占 = True
    finally:
        探测.close()

    # ② 再连一次回环：覆盖「占用者绑在 0.0.0.0、我们要绑 127.0.0.1」这种 ① 探不到的情况
    if not 被占:
        探测 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        探测.settimeout(0.5)
        try:
            探测.connect(('127.0.0.1', 端口))
            被占 = True
        except OSError:
            pass
        finally:
            探测.close()

    if not 被占:
        return None
    return _监听者pid(端口) or '未知'


def _取addrport(argv):
    """从命令行里取 runserver 的 addrport（支持位置参数和 --addrport 两种写法）。"""
    结果 = ''
    for 序号, 参数 in enumerate(argv[2:], start=2):
        if 参数.startswith('--addrport='):
            结果 = 参数.split('=', 1)[1]
        elif 参数 == '--addrport':
            if 序号 + 1 < len(argv):
                结果 = argv[序号 + 1]
        elif not 参数.startswith('-'):
            结果 = 参数
    return 结果


def 启动前检查(argv):
    """是 runserver 且端口已被占用时，打印原因并以退出码 1 结束进程。"""
    if len(argv) < 2 or argv[1] != 'runserver':
        return
    if os.environ.get('RUN_MAIN') == 'true':
        # autoreload 的子进程：父进程已经检查过，不能再查
        return

    主机, 端口 = 解析地址端口(_取addrport(argv))
    谁 = 占用者(端口, 主机)
    if 谁:
        sys.stderr.write(
            '\n[启动互斥] 端口 %s:%s 已被占用（占用者 PID=%s），拒绝启动第二个后端。\n'
            '[启动互斥] 后端同一时间只允许跑一个实例；要重启请先结束现有后端进程。\n\n'
            % (主机, 端口, 谁)
        )
        sys.exit(1)
