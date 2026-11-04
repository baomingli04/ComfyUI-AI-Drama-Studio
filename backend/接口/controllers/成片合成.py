# -*- coding: utf-8 -*-
"""成片合成接口：GET api/成片/列表 + POST api/成片/合成 + GET api/成片/合成状态。

2026-11-04 异步化（原为同步 ffmpeg 长操作，会阻塞 dev server 工作线程）：
- POST 合成 → 校验后创建「成片合成」任务行（剧id/集号/字幕开关存系统提示词 JSON）
  并入队，立刻返回任务 id，由 能力/成片合成.py 在本地计算线程里执行；
- GET 合成状态?任务id= → 轮询任务状态（前端 2 秒一次）；
- GET 列表 → 成片文件列表（文件落盘即出现，保持原口径不变）。

GET  {剧id, 集号}                  → 本集已有的成片文件列表（新在前）
POST {剧id, 集号, 字幕}            → 建任务：返回 {任务id}
GET  {任务id}                      → {状态, 错误信息, url, 回复}
"""
import datetime
import json
import os

from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分镜 import 分镜
from 接口.models.分镜视频 import 分镜视频
from 接口.models.task import task
from 接口.返回.错误 import 取错误位置


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

        # ---------------- POST：建异步合成任务 ----------------
        # 快速校验（与执行器同口径：有任何镜头缺失都拒绝，不让用户白等轮询后看到任务失败）
        镜们 = 分镜.objects.filter(剧id=剧id, 集号=集号)
        if not 镜们.exists():
            return Response({'ok': False, 'error': '本集还没有分镜。'}, status=status.HTTP_400_BAD_REQUEST)
        版本们 = (分镜视频.objects.filter(剧id=剧id, 集号=集号, 选中=True).exclude(url='')
                 .order_by('-id'))
        选中表 = {}
        for 版 in 版本们:
            if 版.镜号 not in 选中表:
                选中表[版.镜号] = 版
        缺 = []
        for 镜 in 镜们:
            版 = 选中表.get(镜.镜号)
            if not 版 or not os.path.isfile(
                    os.path.join(str(settings.RESOURCE_DIR), 版.url.replace('/', os.sep))):
                缺.append(镜.镜号)
        if 缺:
            return Response({'ok': False,
                             'error': '有 %d 个镜头没有可用的正式使用视频：%s' % (
                                 len(缺), '、'.join(str(镜号) for 镜号 in 缺[:6]))},
                            status=status.HTTP_400_BAD_REQUEST)

        # 元数据借 系统提示词 存 JSON（task 表无 剧/集 列，不动表结构）
        任务 = task.objects.create(
            类型='成片合成', 状态='已创建', 创建人id=请求.user, 创建时间=timezone.now(),
            正向提示词='剧%d 集%d 成片合成' % (剧id, 集号),
            系统提示词=json.dumps({'剧id': 剧id, '集号': 集号,
                                  '字幕': bool(参数.get('字幕'))}, ensure_ascii=False),
        )
        from 能力.提交并等待 import 入队
        入队(任务.id)
        return Response({'ok': True, '任务id': 任务.id,
                         '提示': '合成任务已创建，正在后台执行'})

    except Exception as 异常:
        return Response({'ok': False, 'error': '合成失败：' + str(取错误位置(异常))},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def 成片合成状态(请求):
    """GET api/成片/合成状态?任务id= → 轮询合成任务状态。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            任务id = int(请求.query_params.get('任务id') or 0)
        except (TypeError, ValueError):
            任务id = 0
        if not 任务id:
            return Response({'ok': False, 'error': '缺少任务 id。'}, status=status.HTTP_400_BAD_REQUEST)
        任务 = task.objects.filter(id=任务id).first()
        if 任务 is None or 任务.创建人id_id != 请求.user.id:
            return Response({'ok': False, 'error': '任务不存在。'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'ok': True,
            '状态': 任务.状态,
            '错误信息': 任务.错误信息 or '',
            'url': 任务.产物视频1 or '',
            '回复': 任务.回复 or '',
        })
    except Exception as 异常:
        位置 = 取错误位置(异常)
        return Response({'ok': False, 'error': str(异常), 'file': 位置['file'],
                         'line': 位置['line'], 'func': 位置['func']},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
