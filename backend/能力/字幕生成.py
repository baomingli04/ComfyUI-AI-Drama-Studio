# -*- coding: utf-8 -*-
"""字幕生成执行器：faster-whisper 把视频语音转写字幕（2026-11-04 新增，借 MoneyPrinterTurbo）。

- 入参：任务.输入视频1 = 要转写的视频/音频（资源相对路径）；任务.模式 = 模型规格
  （tiny/base/small，缺省 base；首次运行会自动下载模型，需联网）。
- 依赖：faster-whisper（较重，含 ctranslate2，不随主 requirements 自动安装）。
  依赖缺失时任务失败并给出安装提示。
- 产物：srt 文本写入 任务.回复（前端可直接预览/下载），
  同时落盘 资源/产物/字幕/task_<id>.srt（路径记入任务日志）。
"""
import os
import traceback

from django.conf import settings
from django.utils import timezone

from 接口.models.task import task
from 能力.提交并等待 import _置状态, 标记失败, 记日志

缺省模型 = 'base'


def _秒转srt时间(t):
    毫 = int(round(max(t, 0) * 1000))
    时, 毫 = divmod(毫, 3600000)
    分, 毫 = divmod(毫, 60000)
    秒, 毫 = divmod(毫, 1000)
    return '%02d:%02d:%02d,%03d' % (时, 分, 秒, 毫)


def 执行字幕生成(任务id):
    """「字幕生成」任务执行入口，由 能力/提交并等待._本地计算线程 调用。"""
    任务 = task.objects.get(id=任务id)
    源相对 = (任务.输入视频1 or '').strip()
    if not 源相对:
        标记失败(任务id, ValueError('字幕生成需要输入视频1（资源相对路径），当前为空。'))
        return
    源 = os.path.join(str(settings.RESOURCE_DIR), 源相对.replace('/', os.sep))
    if not os.path.isfile(源):
        标记失败(任务id, ValueError('输入视频文件不存在：%s' % 源相对))
        return
    模型规格 = (任务.模式 or '').strip() or 缺省模型

    _置状态(任务id, '生成中', 开始时间=timezone.now())
    记日志(任务id, '[字幕] 源=%s，模型=%s（首次运行会自动下载模型）' % (源相对, 模型规格))

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        标记失败(任务id, RuntimeError(
            'faster-whisper 未安装：请在后端虚拟环境执行 '
            'pip install faster-whisper 后重试（首次使用会自动下载模型）。'))
        return

    记日志(任务id, '[字幕] 加载模型 %s …' % 模型规格)
    try:
        模型 = WhisperModel(模型规格, device='cpu', compute_type='int8')
        段落们, 信息 = 模型.transcribe(源, language='zh', vad_filter=True)
        记日志(任务id, '[字幕] 转写中（语言=%s）…' % (信息.language or 'zh'))

        行们 = []
        for 段 in 段落们:
            行们.append('%d\n%s --> %s\n%s\n' % (
                len(行们) + 1,
                _秒转srt时间(段.start), _秒转srt时间(段.end),
                (段.text or '').strip()))
        srt文本 = '\n'.join(行们)
    except Exception as 异常:
        标记失败(任务id, 异常)
        return

    if not srt文本.strip():
        标记失败(任务id, RuntimeError('没有识别到任何语音内容。'))
        return

    目录 = os.path.join(str(settings.RESOURCE_DIR), '产物', '字幕')
    os.makedirs(目录, exist_ok=True)
    srt路径 = os.path.join(目录, 'task_%s.srt' % 任务id)
    with open(srt路径, 'w', encoding='utf-8') as 写:
        写.write(srt文本)

    _置状态(任务id, '成功', 结束时间=timezone.now(), 回复=srt文本)
    记日志(任务id, '[字幕] 完成：%s（%d 行）' % (srt路径, len(行们)))
