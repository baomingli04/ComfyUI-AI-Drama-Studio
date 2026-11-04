# -*- coding: utf-8 -*-
"""音色合成执行器：Edge-TTS 把台词文本合成音色 mp3（2026-11-04 新增，借 MoneyPrinterTurbo）。

- 入参：任务.正向提示词 = 要合成的台词文本；任务.模式 = Edge 音色名
  （如 zh-CN-XiaoxiaoNeural，缺省 晓晓）。
- 依赖：edge-tts（requirements.txt 已列；走微软免费接口，需要联网）。
  依赖缺失时任务失败并给出安装提示，不自动装。
- 产物：资源/产物/音色/task_<id>.mp3。
  注意：task 表没有「产物音频」列（不动表结构），音频路径暂存 任务.产物视频1，
  前端按普通媒体地址播放即可（媒体服务按扩展名识别 mp3）。
"""
import asyncio
import os

from django.conf import settings
from django.utils import timezone

from 接口.models.task import task
from 能力.提交并等待 import _置状态, 标记失败, 记日志

缺省音色 = 'zh-CN-XiaoxiaoNeural'


def 执行音色合成(任务id):
    """「音色合成」任务执行入口，由 能力/提交并等待._本地计算线程 调用。"""
    任务 = task.objects.get(id=任务id)
    文本 = (任务.正向提示词 or '').strip()
    if not 文本:
        标记失败(任务id, ValueError('音色合成需要台词文本（正向提示词），当前为空。'))
        return
    音色 = (任务.模式 or '').strip() or 缺省音色
    if len(文本) > 2000:
        文本 = 文本[:2000]
        记日志(任务id, '[音色] 文本超 2000 字，已截断')

    _置状态(任务id, '生成中', 开始时间=timezone.now())
    记日志(任务id, '[音色] 音色=%s，文本 %d 字' % (音色, len(文本)))

    try:
        import edge_tts
    except ImportError:
        标记失败(任务id, RuntimeError(
            'edge-tts 未安装：请在后端虚拟环境执行 pip install edge-tts 后重试。'))
        return

    目录 = os.path.join(str(settings.RESOURCE_DIR), '产物', '音色')
    os.makedirs(目录, exist_ok=True)
    产物 = os.path.join(目录, 'task_%s.mp3' % 任务id)

    try:
        async def _合成():
            通信 = edge_tts.Communicate(文本, 音色)
            await 通信.save(产物)

        asyncio.run(_合成())
    except Exception as 异常:
        # 常见失败：音色名写错 / 断网 / 微软接口限流，把原始原因带回去
        标记失败(任务id, 异常)
        return

    if not os.path.isfile(产物) or os.path.getsize(产物) == 0:
        标记失败(任务id, RuntimeError('Edge-TTS 返回了空音频文件，请检查网络后重试。'))
        return

    _置状态(任务id, '成功', 结束时间=timezone.now(),
            产物视频1='产物/音色/task_%s.mp3' % 任务id)
    记日志(任务id, '[音色] 完成：%s（%d 字节）' % (产物, os.path.getsize(产物)))
