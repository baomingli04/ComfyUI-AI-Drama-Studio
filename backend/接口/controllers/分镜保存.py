# -*- coding: utf-8 -*-
"""分镜保存控制器：POST api/分镜/保存。/video/shot 拆分分镜页落库。

请求体 {剧id, 集号, 镜们:[{镜号, 场次, 景别, 运镜, 画面, 台词, 时长, 视频状态}]}：
字段白名单校验 + 按列长截断；事务内全量替换该剧该集的分镜行（按传参顺序写 排序）。
镜们 传空数组 = 清空该集分镜（清空重拆用）。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import datetime
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分镜 import 分镜
from 接口.返回.错误 import 取错误位置

# 白名单：列名 → 最大长度（None = text 不限）
分镜字段 = {
    '镜号': 20, '场次': 100, '景别': 20, '运镜': 50,
    '画面': None, '台词': None, '时长': 16, '视频状态': 16,
    '生成方式': 50, '生成提示词': None,
}


def 截断(值, 长):
    文 = '' if 值 is None else str(值)
    if 长 and len(文) > 长:
        return 文[:长]
    return 文


@api_view(['POST'])
def 分镜保存(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        剧id = 请求.data.get('剧id')
        try:
            剧id = int(剧id)
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        try:
            集号 = int(请求.data.get('集号'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少有效集号。'}, status=status.HTTP_400_BAD_REQUEST)
        if 集号 < 1:
            return Response({'ok': False, 'error': '集号必须 ≥ 1。'}, status=status.HTTP_400_BAD_REQUEST)

        镜们 = 请求.data.get('镜们')
        if not isinstance(镜们, list):
            return Response({'ok': False, 'error': '镜们必须是数组。'}, status=status.HTTP_400_BAD_REQUEST)

        准备们 = []
        见过的镜号 = set()
        for 序, 镜 in enumerate(镜们):
            if not isinstance(镜, dict):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个镜不是对象。'},
                                status=status.HTTP_400_BAD_REQUEST)
            行 = {列: 截断(镜.get(列), 分镜字段[列]) for 列 in 分镜字段}
            if not 行['镜号'].strip():
                行['镜号'] = 'SH%03d' % (序 + 1)
            if 行['镜号'] in 见过的镜号:
                return Response({'ok': False, 'error': '镜号 ' + 行['镜号'] + ' 重复。'},
                                status=status.HTTP_400_BAD_REQUEST)
            见过的镜号.add(行['镜号'])
            if not 行['画面'].strip():
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个镜缺少画面描述。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not 行['视频状态'].strip():
                行['视频状态'] = '待生成'
            行['排序'] = 序
            准备们.append(行)

        此刻 = datetime.datetime.now()
        with transaction.atomic():
            分镜.objects.filter(剧id=剧id, 集号=集号).delete()
            for 行 in 准备们:
                分镜.objects.create(剧id=剧id, 集号=集号, 创建时间=此刻, 更新时间=此刻, **行)

        return Response({'ok': True, '剧id': 剧id, '集号': 集号, '镜数': len(准备们)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
