# -*- coding: utf-8 -*-
"""方案分区保存控制器：POST api/方案/分区保存。/script/detail 方案详情页写库。

body: { 方案id, 分区们: { 时空背景|故事线|爽点矩阵|商业卖点|结局设计: 内容 } }
策略：只覆盖传来的分区键（单区 PATCH），其他分区一律不动（C2 手改保护）；
每次写库顺带刷新该行 更新时间。内容必须是可 JSON 序列化的结构（对象/数组/字符串/null）。
"""
import traceback

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.方案 import 方案
from 接口.返回.错误 import 取错误位置

允许分区 = ('时空背景', '故事线', '爽点矩阵', '商业卖点', '结局设计')


def _可序列化(值):
    """只放行 JSON 安全类型，防垃圾数据进库。"""
    if 值 is None or isinstance(值, (str, int, float, bool)):
        return True
    if isinstance(值, list):
        return all(_可序列化(项) for 项 in 值)
    if isinstance(值, dict):
        return all(isinstance(键, str) and _可序列化(项) for 键, 项 in 值.items())
    return False


@api_view(['POST'])
def 方案分区保存(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            方案id = int(请求.data.get('方案id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少方案 id。'}, status=status.HTTP_400_BAD_REQUEST)

        分区们 = 请求.data.get('分区们')
        if not isinstance(分区们, dict) or not 分区们:
            return Response({'ok': False, 'error': '分区们 不能为空。'}, status=status.HTTP_400_BAD_REQUEST)

        一行 = 方案.objects.filter(id=方案id).first()
        if 一行 is None:
            return Response({'ok': False, 'error': '方案不存在。'}, status=status.HTTP_404_NOT_FOUND)

        if not 剧.objects.filter(id=一行.剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '方案不存在或无权保存。'}, status=status.HTTP_404_NOT_FOUND)

        更新字段 = []
        for 键, 内容 in 分区们.items():
            if 键 not in 允许分区:
                return Response({'ok': False, 'error': '未知分区键：' + str(键)},
                                status=status.HTTP_400_BAD_REQUEST)
            if not _可序列化(内容):
                return Response({'ok': False, 'error': '分区「' + 键 + '」的内容不是可保存的结构。'},
                                status=status.HTTP_400_BAD_REQUEST)
            setattr(一行, 键, 内容)
            更新字段.append(键)

        一行.更新时间 = timezone.now()
        更新字段.append('更新时间')
        一行.save(update_fields=更新字段)

        return Response({'ok': True, '方案id': 一行.id, '已保存分区': 更新字段[:-1]})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
