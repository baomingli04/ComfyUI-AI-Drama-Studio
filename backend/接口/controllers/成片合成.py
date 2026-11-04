# -*- coding: utf-8 -*-
"""成片合成接口：GET api/成片/列表 + POST api/成片/合成。

把本集各镜「正式使用」（分镜视频.选中=1 且有 url）的视频按镜头顺序用 ffmpeg
重新编码归一（统一宽高/帧率/音频）后拼接，输出一个成片 mp4 到 资源/产物/成片/。

GET  {剧id, 集号}                  → 本集已有的成片文件列表（新在前）
POST {剧id, 集号}                  → 合成：返回 {url, 片段数, 时长秒}

实现要点：
- 每个输入先 ffprobe 探测宽高/帧率/有无音轨，全部归一到第一个有视频输入的
  宽高与帧率（scale+pad+fps+setsar），音频统一 44.1k 立体声 aac；
  没有音轨的输入补 anullsrc 静音轨，保证 concat 拼接流布局一致。
- 归一产物放系统临时目录，拼完即删；成片文件按时间戳命名留在 资源/产物/成片/。
- ffmpeg/ffprobe 从 PATH 找，找不到报 500 并说明装法。
"""
import datetime
import os
import shutil
import subprocess
import tempfile

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分镜 import 分镜
from 接口.models.分镜视频 import 分镜视频
from 接口.返回.错误 import 取错误位置


def _找可执行(名):
    路径 = shutil.which(名)
    if not 路径:
        win = shutil.which(名 + '.exe')
        路径 = win
    return 路径


def _跑(命令):
    结果 = subprocess.run(命令, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if 结果.returncode != 0:
        尾 = (结果.stderr or '').strip().splitlines()
        raise RuntimeError((尾[-1] if 尾 else 'ffmpeg 执行失败')[:300])


def _探测(路径, ffprobe):
    """返回 {宽, 高, fps, 有音}；探不出宽高按 720p 30fps 兜底。"""
    宽, 高, fps, 有音 = 0, 0, 0.0, False
    try:
        输出 = subprocess.run([
            ffprobe, '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,avg_frame_rate',
            '-of', 'csv=p=0', 路径
        ], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout.strip()
        if 输出:
            段 = 输出.split(',')[0:3]
            宽 = int(float(段[0])) if 段 and 段[0] else 0
            高 = int(float(段[1])) if len(段) > 1 and 段[1] else 0
            if len(段) > 2 and 段[2] and ':' in 段[2]:
                分, 母 = 段[2].split(':')[:2]
                if float(母) > 0:
                    fps = float(分) / float(母)
        音输出 = subprocess.run([
            ffprobe, '-v', 'error', '-select_streams', 'a',
            '-show_entries', 'stream=index', '-of', 'csv=p=0', 路径
        ], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout.strip()
        有音 = bool(音输出)
    except Exception:
        pass
    return {'宽': 宽 or 720, '高': 高 or 1280, 'fps': fps if fps > 0 else 30.0, '有音': 有音}


@api_view(['GET', 'POST'])
def 成片合成接口(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if 请求.method == 'GET':
            参数 = 请求.GET
        else:
            参数 = 请求.data if isinstance(请求.data, dict) else {}

        try:
            剧id = int(参数.get('剧id'))
            集号 = int(参数.get('集号'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id 或集号。'}, status=status.HTTP_400_BAD_REQUEST)
        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        成片目录 = os.path.join(str(settings.RESOURCE_DIR), '产物', '成片')
        if 请求.method == 'GET':
            列表 = []
            if os.path.isdir(成片目录):
                前缀 = '剧%d_集%d_' % (剧id, 集号)
                for 名 in os.listdir(成片目录):
                    if 名.endswith('.mp4') and 名.startswith(前缀):
                        列表.append({
                            '文件名': 名,
                            'url': '产物/成片/' + 名,
                            '时间': datetime.datetime.fromtimestamp(
                                os.path.getmtime(os.path.join(成片目录, 名))
                            ).strftime('%Y-%m-%d %H:%M:%S'),
                            '大小': os.path.getsize(os.path.join(成片目录, 名)),
                        })
            列表.sort(key=lambda 行: 行['时间'], reverse=True)
            return Response({'ok': True, '成片们': 列表})

        # ---------------- POST：合成 ----------------
        ffmpeg = _找可执行('ffmpeg')
        ffprobe = _找可执行('ffprobe')
        if not ffmpeg or not ffprobe:
            return Response({'ok': False, 'error': '服务器上没找到 ffmpeg/ffprobe，请先安装并加入 PATH。'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 按镜头顺序取「正式使用」版本
        镜们 = list(分镜.objects.filter(剧id=剧id, 集号=集号).order_by('排序', 'id'))
        if not 镜们:
            return Response({'ok': False, 'error': '本集还没有分镜。'}, status=status.HTTP_400_BAD_REQUEST)
        版本们 = 分镜视频.objects.filter(剧id=剧id, 集号=集号, 选中=True).exclude(url='').order_by('-id')
        选中表 = {}
        for 版 in 版本们:
            if 版.镜号 not in 选中表:  # 同镜取最新一条选中版
                选中表[版.镜号] = 版

        缺 = []
        片们 = []
        for 镜 in 镜们:
            版 = 选中表.get(镜.镜号)
            if not 版:
                缺.append({'镜号': 镜.镜号, '原因': '没有「正式使用」版本'})
                continue
            源 = os.path.join(str(settings.RESOURCE_DIR), 版.url.replace('/', os.sep))
            if not os.path.isfile(源):
                缺.append({'镜号': 镜.镜号, '原因': '视频文件不存在'})
                continue
            片们.append({'镜号': 镜.镜号, '源': 源})
        if 缺:
            return Response({'ok': False,
                             'error': '有 %d 个镜头没有可用的正式使用视频：%s' % (
                                 len(缺), '、'.join('%s(%s)' % (d['镜号'], d['原因']) for d in 缺[:6]))},
                            status=status.HTTP_400_BAD_REQUEST)

        # 归一参数：取第一个输入的宽高与帧率
        首探 = _探测(片们[0]['源'], ffprobe)
        宽 = 首探['宽'] - 首探['宽'] % 2
        高 = 首探['高'] - 首探['高'] % 2
        fps = 首探['fps']
        vf = 'scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=%.4f,setsar=1,format=yuv420p' % (宽, 高, 宽, 高, fps)

        临时目录 = tempfile.mkdtemp(prefix='aicg_chengpian_')
        try:
            归一件们 = []
            for 序, 片 in enumerate(片们):
                归一 = os.path.join(临时目录, 'norm_%03d.mp4' % 序)
                探 = _探测(片['源'], ffprobe)
                if 探['有音']:
                    命令 = [ffmpeg, '-y', '-v', 'error', '-i', 片['源'],
                            '-filter_complex', '[0:v]%s[v];[0:a]aresample=44100,aformat=channel_layouts=stereo[a]' % vf,
                            '-map', '[v]', '-map', '[a]']
                else:
                    # 无音轨输入补静音轨，保证 concat 拼接流布局一致（含第一个输入）
                    命令 = [ffmpeg, '-y', '-v', 'error',
                            '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                            '-i', 片['源'],
                            '-filter_complex', '[1:v]%s[v];[0:a]atrim=duration=%s,asetpts=PTS-STARTPTS[a]' % (
                                vf, max(_时长秒(片['源'], ffprobe), 0.1)),
                            '-map', '[v]', '-map', '[a]']
                命令 += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                         '-c:a', 'aac', '-b:a', '128k', '-shortest', 归一]
                _跑(命令)
                归一件们.append(归一)

            # concat 拼接（归一后编码参数一致，直接流复制）
            列表文件 = os.path.join(临时目录, 'list.txt')
            with open(列表文件, 'w', encoding='utf-8') as 写:
                for 件 in 归一件们:
                    写.write("file '%s'\n" % 件.replace('\\', '/').replace("'", "'\\''"))

            os.makedirs(成片目录, exist_ok=True)
            文件名 = '剧%d_集%d_%s.mp4' % (剧id, 集号, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            成片路径 = os.path.join(成片目录, 文件名)
            _跑([ffmpeg, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 列表文件,
                 '-c', 'copy', '-movflags', '+faststart', 成片路径])
            时长 = _时长秒(成片路径, ffprobe)
        finally:
            shutil.rmtree(临时目录, ignore_errors=True)

        return Response({'ok': True, 'url': '产物/成片/' + 文件名,
                         '片段数': len(片们), '时长秒': round(时长, 1)})
    except Exception as 异常:
        return Response({'ok': False, 'error': '合成失败：' + str(取错误位置(异常))},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _时长秒(路径, ffprobe):
    try:
        输出 = subprocess.run([
            ffprobe, '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', 路径
        ], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout.strip()
        return float(输出.split(',')[0]) if 输出 else 0.0
    except Exception:
        return 0.0
