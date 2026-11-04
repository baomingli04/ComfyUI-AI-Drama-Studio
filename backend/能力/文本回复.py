# -*- coding: utf-8 -*-
"""文本回复能力：系统提示词 + 正向提示词 → LLM → 写 task.回复。

提示词原样透传，禁止后端拼接（docs/08）。
2026-11-04：改流式调用，已生成的部分文本周期性写回 task.回复，
前端轮询（任务面板/各生成页）即可实时看到逐步增长的内容。
"""
import time

from django.utils import timezone

from 能力.LLM调用 import 调用LLM流式
from 能力.提交并等待 import 记日志, _置状态, 标记失败


def 执行文本回复(任务id):
    """执行一条文本回复任务。开始时间 = 真正调用 LLM 的时刻。"""
    from 接口.models.task import task
    任务 = task.objects.get(id=任务id)
    _置状态(任务id, '生成中', 开始时间=timezone.now(), 回复='')
    记日志(任务id, '[开始] 调用 LLM（文本回复，流式）')

    消息 = []
    if 任务.系统提示词:
        消息.append({'role': 'system', 'content': 任务.系统提示词})
    消息.append({'role': 'user', 'content': 任务.正向提示词 or ''})
    记日志(任务id, '[请求] 系统提示词 %d 字 / 正向提示词 %d 字'
           % (len(任务.系统提示词 or ''), len(任务.正向提示词 or '')))

    # 节流：每 1.5 秒最多落库一次部分文本，避免长生成时高频写库
    上次写 = [0.0]

    def _进度(累计文本):
        此刻 = time.time()
        if 此刻 - 上次写[0] < 1.5:
            return
        上次写[0] = 此刻
        try:
            _置状态(任务id, '生成中', 回复=累计文本)
        except Exception:
            pass

    try:
        回复 = 调用LLM流式(消息, 超时=300, on增量=_进度)
    except Exception as 异常:
        标记失败(任务id, 异常)
        return

    _置状态(任务id, '成功', 回复=回复, 结束时间=timezone.now())
    记日志(任务id, '[完成] 回复 %d 字' % len(回复 or ''))
