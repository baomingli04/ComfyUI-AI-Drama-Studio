# -*- coding: utf-8 -*-
"""图片解析能力：输入图1 → LLM 多模态识图 → 写 task.回复。"""
from django.conf import settings
from django.utils import timezone

from 能力.LLM调用 import 调用LLM, 图片转数据URI
from 能力.提交并等待 import 记日志, _置状态, 标记失败


def 执行图片解析(任务id):
    from 接口.models.task import task
    任务 = task.objects.get(id=任务id)

    if not 任务.输入图1:
        标记失败(任务id, RuntimeError('图片解析必须上传输入图1。'))
        return

    _置状态(任务id, '生成中', 开始时间=timezone.now())
    记日志(任务id, '[开始] 调用 LLM（图片解析）图=%s' % 任务.输入图1)

    文件 = settings.RESOURCE_DIR / 任务.输入图1
    if not 文件.is_file():
        标记失败(任务id, RuntimeError('输入图文件不存在：%s' % 文件))
        return
    数据URI = 图片转数据URI(str(文件))

    消息 = []
    if 任务.系统提示词:
        消息.append({'role': 'system', 'content': 任务.系统提示词})
    消息.append({
        'role': 'user',
        'content': [
            {'type': 'image_url', 'image_url': {'url': 数据URI}},
            {'type': 'text', 'text': 任务.正向提示词 or '请解析这张图片。'},
        ],
    })

    try:
        回复 = 调用LLM(消息)
    except Exception as 异常:
        标记失败(任务id, 异常)
        return

    _置状态(任务id, '成功', 回复=回复, 结束时间=timezone.now())
    记日志(任务id, '[完成] 回复 %d 字' % len(回复 or ''))
