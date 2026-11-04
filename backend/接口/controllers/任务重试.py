# -*- coding: utf-8 -*-
"""任务重试控制器：POST api/任务/重试 {id}。

失败/中断/已取消的任务一键重提：把原任务行的全部生成参数复制成一条新的
「已创建」任务（同类型同参数，产物/错误/时间戳清空，保留原 seed 便于复现），
入队后由对应执行器按标准链路重跑。只允许重试自己创建的任务。
"""
import datetime
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置

# 数字/布尔类字段
复制数值字段 = ['图片宽', '图片高', '视频宽', '视频高', '一采MP', '二采MP',
                '视频时长', 'cfg', 'seed', '生成声音', '步数',
                '组1时长', '组2时长', '组3时长', '组4时长']


def _要复制的字段名们():
    名们 = ['类型', '正向提示词', '反向提示词', '比例', '模式', '水印',
            '底膜精度', '系统提示词',
            '组1提示词', '组2提示词', '组3提示词', '组4提示词']
    名们 += ['输入图%d' % i for i in range(1, 10)]
    名们 += ['输入视频%d' % i for i in range(1, 4)]
    名们 += ['输入音频%d' % i for i in range(1, 4)]
    名们 += 复制数值字段
    return 名们


@api_view(['POST'])
def 任务重试(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            原id = int(请求.data.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少任务 id。'}, status=status.HTTP_400_BAD_REQUEST)

        原 = task.objects.filter(id=原id, 创建人id=请求.user.id).first()
        if 原 is None:
            return Response({'ok': False, 'error': '任务不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        if 原.状态 not in ('失败', '中断', '已取消'):
            return Response({'ok': False, 'error': '只有 失败/中断/已取消 的任务可以重试，当前状态：' + 原.状态},
                            status=status.HTTP_400_BAD_REQUEST)

        此刻 = datetime.datetime.now()
        新 = task(状态='已创建', 创建人id=请求.user.id, 创建时间=此刻)
        for 名 in _要复制的字段名们():
            setattr(新, 名, getattr(原, 名))
        新.save()

        # 原任务标记来源，任务面板能看到重试链
        原.错误信息 = ((原.错误信息 or '') + '\n[已重试为任务 ' + str(新.id) + ']').strip()
        原.save(update_fields=['错误信息'])

        from 能力.提交并等待 import 入队
        入队(新.id)

        return Response({'ok': True, '新任务id': 新.id, '类型': 新.类型})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
