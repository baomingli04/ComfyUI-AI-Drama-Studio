# -*- coding: utf-8 -*-
"""成片合成执行器：本机 CPU 线程跑 ffmpeg，把本集各镜「正式使用」视频归一拼接成片。

2026-11-04 由 接口/controllers/成片合成.py 的同步实现迁移（同步长操作会阻塞
dev server 工作线程，见 docs/10 任务清单），改为「成片合成」任务类型走任务状态机：

- 入参：任务.系统提示词 存 JSON 元数据 {"剧id": x, "集号": y, "字幕": bool}
  （task 表没有 剧/集 列，不动表结构，借用 TextField 存元数据）
- 产物：资源/产物/成片/剧<id>_集<集>_<时间戳>.mp4 → 任务.产物视频1
- 汇总：任务.回复 存 JSON {"片段数": n, "时长秒": s, "url": 相对路径}
- 可选字幕（2026-11-04 新增，借 MoneyPrinterTurbo 思路）：字幕=true 时按
  分镜.台词 逐镜烧录——每镜生成一个 srt（0 → 该镜时长），随归一转码一次烧进，
  不增加额外编码遍数。

实现要点（沿用原控制器）：
- 每个输入先 ffprobe 探测宽高/帧率/有无音轨，全部归一到第一个有视频输入的
  宽高与帧率（scale+pad+fps+setsar），音频统一 44.1k 立体声 aac；
  没有音轨的输入补 anullsrc 静音轨，保证 concat 拼接流布局一致。
- 归一产物放系统临时目录，拼完即删；成片文件按时间戳命名留在 资源/产物/成片/。
"""
import datetime
import json
import os
import shutil
import subprocess
import tempfile

from django.conf import settings
from django.utils import timezone

from 接口.models.task import task
from 能力.提交并等待 import _置状态, 标记失败, 记日志


def 找可执行(名):
    import shutil as _shutil
    路径 = _shutil.which(名)
    if not 路径:
        路径 = _shutil.which(名 + '.exe')
    return 路径


def 跑ffmpeg(命令):
    # timeout（2026-11-04 补丁）：ffmpeg 偶发挂死时若无超时会永久阻塞执行线程。
    # 1800 秒对齐 能力/音频剪辑.py 的既有口径；超时由 subprocess.run 负责杀掉子进程。
    try:
        结果 = subprocess.run(命令, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=1800)
    except subprocess.TimeoutExpired:
        raise RuntimeError('ffmpeg 执行超过 1800 秒未结束，已强制终止')
    if 结果.returncode != 0:
        尾 = (结果.stderr or '').strip().splitlines()
        raise RuntimeError((尾[-1] if 尾 else 'ffmpeg 执行失败')[:300])


def 探测视频(路径, ffprobe):
    """返回 {宽, 高, fps, 有音}；探不出宽高按 720p 30fps 兜底。"""
    宽, 高, fps, 有音 = 0, 0, 0.0, False
    try:
        输出 = subprocess.run([
            ffprobe, '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,avg_frame_rate',
            '-of', 'csv=p=0', 路径
        ], capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60).stdout.strip()
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
        ], capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60).stdout.strip()
        有音 = bool(音输出)
    except Exception:
        pass
    return {'宽': 宽 or 720, '高': 高 or 1280, 'fps': fps if fps > 0 else 30.0, '有音': 有音}


def 时长秒(路径, ffprobe):
    try:
        输出 = subprocess.run([
            ffprobe, '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', 路径
        ], capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60).stdout.strip()
        return float(输出.split(',')[0]) if 输出 else 0.0
    except Exception:
        return 0.0


def _字幕时间(t):
    毫 = int(round(max(t, 0) * 1000))
    时, 毫 = divmod(毫, 3600000)
    分, 毫 = divmod(毫, 60000)
    秒, 毫 = divmod(毫, 1000)
    return '%02d:%02d:%02d,%03d' % (时, 分, 秒, 毫)


def _写镜字幕(srt路径, 文本, 时长):
    """一镜一个 srt：整镜显示该镜台词。台词为空不写。"""
    正文 = (文本 or '').strip().replace('\r', ' ').replace('\n', ' ')
    if not 正文:
        return False
    with open(srt路径, 'w', encoding='utf-8') as 写:
        写.write('1\n%s --> %s\n%s\n' % (_字幕时间(0), _字幕时间(max(时长, 0.5)), 正文))
    return True


def 字幕滤镜(srt路径):
    """构造 subtitles 滤镜串；路径里的 : 要转义（Windows 盘符），值用单引号包住。

    force_style：黑边白字、微软雅黑、底部留 40px，漫剧竖屏可读性优先。
    """
    转义 = str(srt路径).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")
    样式 = ('FontName=Microsoft YaHei,FontSize=22,PrimaryColour=&H00FFFFFF,'
            'OutlineColour=&H00000000,BorderStyle=1,Outline=1,Shadow=0,MarginV=40')
    return "subtitles=filename='%s':force_style='%s'" % (转义, 样式)


def 执行成片合成(任务id):
    """「成片合成」任务执行入口，由 能力/提交并等待._本地计算线程 调用。"""
    from 接口.models.分镜 import 分镜
    from 接口.models.分镜视频 import 分镜视频

    任务 = task.objects.get(id=任务id)
    try:
        元数据 = json.loads(任务.系统提示词 or '{}')
    except ValueError:
        元数据 = {}
    剧id = int(元数据.get('剧id') or 0)
    集号 = int(元数据.get('集号') or 0)
    烧字幕 = bool(元数据.get('字幕'))
    if not 剧id or not 集号:
        标记失败(任务id, ValueError('任务缺少 剧id/集号 元数据（系统提示词应为 JSON）'))
        return

    _置状态(任务id, '生成中', 开始时间=timezone.now())
    记日志(任务id, '[成片] 剧%d 集%d，烧字幕=%s' % (剧id, 集号, 烧字幕))

    ffmpeg = 找可执行('ffmpeg')
    ffprobe = 找可执行('ffprobe')
    if not ffmpeg or not ffprobe:
        标记失败(任务id, RuntimeError('服务器上没找到 ffmpeg/ffprobe，请先安装并加入 PATH。'))
        return

    # 按镜头顺序取「正式使用」版本
    镜们 = list(分镜.objects.filter(剧id=剧id, 集号=集号).order_by('排序', 'id'))
    版本们 = (分镜视频.objects.filter(剧id=剧id, 集号=集号, 选中=True).exclude(url='')
             .order_by('-id'))
    选中表 = {}
    for 版 in 版本们:
        if 版.镜号 not in 选中表:  # 同镜取最新一条选中版
            选中表[版.镜号] = 版
    台词表 = {镜.镜号: (镜.台词 or '').strip() for 镜 in 镜们}

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
        标记失败(任务id, ValueError('有 %d 个镜头没有可用的正式使用视频：%s' % (
            len(缺), '、'.join('%s(%s)' % (d['镜号'], d['原因']) for d in 缺[:6]))))
        return

    # 归一参数：取第一个输入的宽高与帧率
    首探 = 探测视频(片们[0]['源'], ffprobe)
    宽 = 首探['宽'] - 首探['宽'] % 2
    高 = 首探['高'] - 首探['高'] % 2
    fps = 首探['fps']
    vf = ('scale=%d:%d:force_original_aspect_ratio=decrease,'
          'pad=%d:%d:(ow-iw)/2:(oh-ih)/2,fps=%.4f,setsar=1') % (宽, 高, 宽, 高, fps)

    临时目录 = tempfile.mkdtemp(prefix='aicg_chengpian_')
    try:
        归一件们 = []
        字幕目录 = os.path.join(临时目录, 'srt')
        os.makedirs(字幕目录, exist_ok=True)
        for 序, 片 in enumerate(片们):
            # 每镜之间检查取消：已取消是终态，这里提前收尾省掉白跑的转码
            当前 = task.objects.filter(id=任务id).first()
            if 当前 is not None and 当前.状态 == '已取消':
                记日志(任务id, '[成片] 任务已取消，停止合成')
                return
            归一 = os.path.join(临时目录, 'norm_%03d.mp4' % 序)
            探 = 探测视频(片['源'], ffprobe)
            vf镜 = vf
            if 烧字幕 and 台词表.get(片['镜号']):
                srt路径 = os.path.join(字幕目录, 'clip_%03d.srt' % 序)
                if _写镜字幕(srt路径, 台词表[片['镜号']], 时长秒(片['源'], ffprobe)):
                    vf镜 = vf + ',' + 字幕滤镜(srt路径)
                    记日志(任务id, '[成片] 镜 %s 烧录字幕' % 片['镜号'])
            if 探['有音']:
                命令 = [ffmpeg, '-y', '-v', 'error', '-i', 片['源'],
                        '-filter_complex',
                        '[0:v]%s,format=yuv420p[v];[0:a]aresample=44100,aformat=channel_layouts=stereo[a]' % vf镜,
                        '-map', '[v]', '-map', '[a]']
            else:
                # 无音轨输入补静音轨，保证 concat 拼接流布局一致（含第一个输入）
                命令 = [ffmpeg, '-y', '-v', 'error',
                        '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                        '-i', 片['源'],
                        '-filter_complex',
                        '[1:v]%s,format=yuv420p[v];[0:a]atrim=duration=%s,asetpts=PTS-STARTPTS[a]' % (
                            vf镜, max(时长秒(片['源'], ffprobe), 0.1)),
                        '-map', '[v]', '-map', '[a]']
            命令 += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                     '-c:a', 'aac', '-b:a', '128k', '-shortest', 归一]
            跑ffmpeg(命令)
            归一件们.append(归一)
            记日志(任务id, '[成片] 归一 %d/%d：%s' % (序 + 1, len(片们), 片['镜号']))

        # concat 拼接（归一后编码参数一致，直接流复制）
        列表文件 = os.path.join(临时目录, 'list.txt')
        with open(列表文件, 'w', encoding='utf-8') as 写:
            for 件 in 归一件们:
                写.write("file '%s'\n" % 件.replace('\\', '/').replace("'", "'\\''"))

        成片目录 = os.path.join(str(settings.RESOURCE_DIR), '产物', '成片')
        os.makedirs(成片目录, exist_ok=True)
        文件名 = '剧%d_集%d_%s.mp4' % (剧id, 集号, datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        成片路径 = os.path.join(成片目录, 文件名)
        跑ffmpeg([ffmpeg, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 列表文件,
                  '-c', 'copy', '-movflags', '+faststart', 成片路径])
        时长 = 时长秒(成片路径, ffprobe)
    finally:
        shutil.rmtree(临时目录, ignore_errors=True)

    _置状态(任务id, '成功', 结束时间=timezone.now(),
            产物视频1='产物/成片/' + 文件名,
            回复=json.dumps({'片段数': len(片们), '时长秒': round(时长, 1),
                             'url': '产物/成片/' + 文件名}, ensure_ascii=False))
    记日志(任务id, '[成片] 完成：%s（%d 片段，%.1f 秒）' % (文件名, len(片们), 时长))
