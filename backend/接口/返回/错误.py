# -*- coding: utf-8 -*-
"""错误工具：统一取真实文件路径、行号、函数名。"""
import traceback


def 取错误位置(异常):
    """从异常栈取真实位置：文件绝对路径、行号、函数名。"""
    栈 = traceback.extract_tb(异常.__traceback__)
    if not 栈:
        return {'file': __file__, 'line': 0, 'func': '未知'}
    帧 = 栈[-1]
    return {'file': 帧.filename, 'line': 帧.lineno, 'func': 帧.name}
