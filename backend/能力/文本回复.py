# -*- coding: utf-8 -*-
"""文本回复能力：系统提示词 + 正向提示词 → LLM → 写 task.回复。

提示词原样透传，禁止后端拼接（docs/08）。
"""
from django.utils import timezone

from 能力.LLM调用 import 调用LLM
from 能力.提交并等待 import 记日志, _置状态, 标记失败


def 执行文本回复(任务id):
    """执行一条文本回复任务。开始时间 = 真正调用 LLM 的时刻。"""
    from 接口.models.task import task
    任务 = task.objects.get(id=任务id)
    _置状态(任务id, '生成中', 开始时间=timezone.now())
    记日志(任务id, '[开始] 调用 LLM（文本回复）')

    消息 = []
    if 任务.系统提示词:
        消息.append({'role': 'system', 'content': 任务.系统提示词})
    消息.append({'role': 'user', 'content': 任务.正向提示词 or ''})
    记日志(任务id, '[请求] 系统提示词 %d 字 / 正向提示词 %d 字'
           % (len(任务.系统提示词 or ''), len(任务.正向提示词 or '')))

    try:
        回复 = 调用LLM(消息)
    except Exception as 异常:
        标记失败(任务id, 异常)
        return

    _置状态(任务id, '成功', 回复=回复, 结束时间=timezone.now())
    记日志(任务id, '[完成] 回复 %d 字' % len(回复 or ''))
