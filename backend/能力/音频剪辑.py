# -*- coding: utf-8 -*-
"""音频剪辑能力：本地 ffmpeg 同步处理（不进 Comfy/LLM 队列、不落 task 表）。

对外入口（任意处 import 即用）：
- 提取音频(视频相对路径, 格式, 采样率) → {路径, 时长, 采样率, 声道}
- 合成音频(源相对路径, 片段列表, 模式, 格式) → {路径} 或 {路径列表}
- 取音频信息(相对路径) → {时长, 采样率, 声道}

约定：
- 入参路径是「相对 资源/ 的路径」（上传/xxx.mp4、产物/音频_xxx.wav），与 task 表存法一致。
- 产物一律写 资源/产物/，返回相对路径。
- ffmpeg 用 settings.FFMPEG_EXE（本机 PATH 里没有 ffmpeg）。
- imageio-ffmpeg 只带 ffmpeg、不带 ffprobe，所以信息解析走 `ffmpeg -i` 的 stderr。
"""
import re
import subprocess
import uuid
from pathlib import Path

from django.conf import settings

允许格式 = ('wav', 'mp3')
最多片段 = 50
ffmpeg超时秒 = 1800


def _ffmpeg路径():
    """取 ffmpeg 可执行文件路径；文件不在就报明确错误（改 settings.FFMPEG_EXE）。"""
    路径 = Path(str(settings.FFMPEG_EXE))
    if not 路径.is_file():
        raise RuntimeError('ffmpeg 不存在：%s（改 backend/后端/settings.py 的 FFMPEG_EXE）' % 路径)
    return str(路径)


def _绝对路径(相对路径):
    """相对 资源/ 的路径 → 绝对路径；防穿越 + 文件必须存在。"""
    根 = settings.RESOURCE_DIR.resolve()
    目标 = (根 / str(相对路径)).resolve()
    if not str(目标).startswith(str(根)):
        raise RuntimeError('路径越界：' + str(相对路径))
    if not 目标.is_file():
        raise RuntimeError('文件不存在：' + str(相对路径))
    return 目标


def _跑ffmpeg(参数, 超时=ffmpeg超时秒):
    """跑一次 ffmpeg（-y 覆盖），失败抛异常并带 stderr 末尾几行。"""
    命令 = [_ffmpeg路径(), '-hide_banner', '-y'] + [str(项) for 项 in 参数]
    try:
        结果 = subprocess.run(命令, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=超时)
    except subprocess.TimeoutExpired:
        raise RuntimeError('ffmpeg 超时（%d 秒）' % 超时)
    if 结果.returncode != 0:
        文本 = 结果.stderr.decode('utf-8', 'ignore').strip().splitlines()
        raise RuntimeError('ffmpeg 失败（退出码 %d）：%s' % (结果.returncode, ' | '.join(文本[-6:])))
    return 结果.stderr.decode('utf-8', 'ignore')


def _解析信息(文本):
    """从 `ffmpeg -i` 的 stderr 里取 时长/采样率/声道。"""
    时长 = 0.0
    匹配 = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', 文本)
    if 匹配:
        时长 = int(匹配.group(1)) * 3600 + int(匹配.group(2)) * 60 + float(匹配.group(3))

    采样率 = 0
    声道 = 0
    音频行 = ''
    for 行 in 文本.splitlines():
        if 'Audio:' in 行:
            音频行 = 行
            break
    if 音频行:
        匹配 = re.search(r'(\d+)\s*Hz', 音频行)
        if 匹配:
            采样率 = int(匹配.group(1))
        匹配 = re.search(r'Hz,\s*([^,]+)', 音频行)
        if 匹配:
            描述 = 匹配.group(1).strip()
            if 描述 == 'mono':
                声道 = 1
            elif 描述 == 'stereo':
                声道 = 2
            else:
                匹配 = re.search(r'(\d+)\s*channels', 描述)
                声道 = int(匹配.group(1)) if 匹配 else 0

    return {'时长': round(时长, 3), '采样率': 采样率, '声道': 声道}


def 取音频信息(相对路径):
    """读音频/视频的 时长/采样率/声道（只探测，不产出文件）。"""
    源 = _绝对路径(相对路径)
    结果 = subprocess.run([_ffmpeg路径(), '-hide_banner', '-i', str(源)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    信息 = _解析信息(结果.stderr.decode('utf-8', 'ignore'))
    if 信息['时长'] <= 0:
        raise RuntimeError('读不到时长，可能不是音视频文件：' + str(相对路径))
    return 信息


def _输出参数(格式, 采样率=0):
    """编码参数：wav 走 pcm_s16le，mp3 走 libmp3lame。"""
    参数 = []
    if 采样率:
        参数 += ['-ar', int(采样率)]
    if 格式 == 'wav':
        参数 += ['-acodec', 'pcm_s16le']
    else:
        参数 += ['-acodec', 'libmp3lame', '-q:a', '2']
    return 参数


def _校验片段(片段列表):
    """片段列表 → [(开始, 结束)]，顺便卡数量与时间合法性。"""
    if not isinstance(片段列表, list) or not 片段列表:
        raise RuntimeError('片段列表为空。')
    if len(片段列表) > 最多片段:
        raise RuntimeError('片段最多 %d 段。' % 最多片段)
    干净 = []
    for 序号, 片段 in enumerate(片段列表, 1):
        try:
            开始 = float(片段.get('开始'))
            结束 = float(片段.get('结束'))
        except Exception:
            raise RuntimeError('第 %d 段的开始/结束不是数字。' % 序号)
        if 开始 < 0 or 结束 <= 开始:
            raise RuntimeError('第 %d 段的时间不对：开始 %s / 结束 %s' % (序号, 开始, 结束))
        干净.append((round(开始, 3), round(结束, 3)))
    return 干净


def 提取音频(视频相对路径, 格式='wav', 采样率=0):
    """从视频里抽音轨 → 资源/产物/音频_<uuid>.<格式>，返回相对路径 + 音频信息。"""
    格式 = (格式 or 'wav').strip().lower()
    if 格式 not in 允许格式:
        raise RuntimeError('不支持的输出格式：' + 格式)
    源 = _绝对路径(视频相对路径)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    新名 = '音频_' + uuid.uuid4().hex + '.' + 格式
    目标 = settings.OUTPUT_DIR / 新名
    参数 = ['-i', str(源), '-vn'] + _输出参数(格式, 采样率) + [str(目标)]
    _跑ffmpeg(参数)

    结果 = {'路径': '产物/' + 新名}
    结果.update(取音频信息('产物/' + 新名))
    return 结果


def 合成音频(源相对路径, 片段列表, 模式='合并', 格式='wav'):
    """按片段列表出音频：模式=合并 出一条；模式=分别 每段一个文件。"""
    格式 = (格式 or 'wav').strip().lower()
    if 格式 not in 允许格式:
        raise RuntimeError('不支持的输出格式：' + 格式)
    模式 = (模式 or '合并').strip()
    if 模式 not in ('合并', '分别'):
        raise RuntimeError('不支持的导出模式：' + 模式)

    源 = _绝对路径(源相对路径)
    片段 = _校验片段(片段列表)
    总时长 = 取音频信息(源相对路径)['时长']
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if 模式 == '合并':
        新名 = '音频剪辑_' + uuid.uuid4().hex + '.' + 格式
        目标 = settings.OUTPUT_DIR / 新名
        链 = []
        for 序号, (开始, 结束) in enumerate(片段):
            链.append('[0:a]atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS[a%d]'
                      % (开始, min(结束, 总时长), 序号))
        链.append(''.join('[a%d]' % 序号 for 序号 in range(len(片段)))
                  + 'concat=n=%d:v=0:a=1[out]' % len(片段))
        参数 = ['-i', str(源), '-filter_complex', ';'.join(链), '-map', '[out]']
        参数 += _输出参数(格式)
        参数 += [str(目标)]
        _跑ffmpeg(参数)
        return {'路径': '产物/' + 新名, '时长': 取音频信息('产物/' + 新名)['时长']}

    路径列表 = []
    for 序号, (开始, 结束) in enumerate(片段, 1):
        新名 = '音频片段_%02d_' % 序号 + uuid.uuid4().hex[:8] + '.' + 格式
        目标 = settings.OUTPUT_DIR / 新名
        参数 = ['-ss', '%.3f' % 开始, '-i', str(源), '-t', '%.3f' % (min(结束, 总时长) - 开始)]
        参数 += ['-vn'] + _输出参数(格式) + [str(目标)]
        _跑ffmpeg(参数)
        路径列表.append('产物/' + 新名)
    return {'路径列表': 路径列表}
