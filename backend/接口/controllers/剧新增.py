# -*- coding: utf-8 -*-
"""剧新增控制器：POST 剧/新增。P0 立项落库（/script/new 提交）。"""
import traceback

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 剧新增(请求):
    """新建剧：剧名全局查重；集数 2~100；创意 ≥20 字才放行（手册细则三.1）。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        剧名 = (请求.data.get('剧名') or '').strip()
        集数 = 请求.data.get('集数')
        题材 = (请求.data.get('题材') or '').strip()
        创意 = (请求.data.get('创意') or '').strip()
        起点方式 = (请求.data.get('起点方式') or '原创').strip()
        封面图片 = (请求.data.get('封面图片') or '').strip() or None
        保存地址 = (请求.data.get('保存地址') or '').strip() or None

        if not 剧名:
            return Response({'ok': False, 'error': '剧名不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        if len(剧名) > 100:
            return Response({'ok': False, 'error': '剧名不能超过 100 字。'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            集数 = int(集数)
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '集数必须是数字。'}, status=status.HTTP_400_BAD_REQUEST)
        if not (2 <= 集数 <= 100):
            return Response({'ok': False, 'error': '集数须在 2~100 之间。'}, status=status.HTTP_400_BAD_REQUEST)
        if not 题材:
            return Response({'ok': False, 'error': '题材不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        if len(创意) < 20:
            return Response({'ok': False, 'error': '创意至少写 20 个字，它是一句生成方案的种子。'},
                            status=status.HTTP_400_BAD_REQUEST)

        if 剧.objects.filter(剧名=剧名).exists():
            return Response({'ok': False, 'error': '剧名「' + 剧名 + '」已存在，换一个名字。'},
                            status=status.HTTP_400_BAD_REQUEST)

        现在 = timezone.now()
        一行 = 剧.objects.create(
            用户id=请求.user.id,
            剧名=剧名, 集数=集数, 题材=题材, 创意=创意,
            起点方式=起点方式 if 起点方式 in ('原创', '模板', '灵感启发') else '原创',
            封面图片=封面图片, 保存地址=保存地址,
            状态='草稿', 创作进度=0, 视频进度=0,
            创建时间=现在, 更新时间=现在,
        )
        return Response({'ok': True, 'id': 一行.id, '剧名': 一行.剧名})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
