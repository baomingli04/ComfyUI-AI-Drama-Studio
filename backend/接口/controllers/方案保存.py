# -*- coding: utf-8 -*-
"""方案保存控制器：POST api/方案/保存。/script/plan 的方案卡写库（生成结果 / 手改 / 选定共用）。

body: { 剧id, 方案们: [{id?, 版本号?, 候选卡:{标题,故事线,题材,基调,结局,驱动,风险}}], 选定id? }
策略：带 id 的行更新（只动候选卡/版本号）；不带 id 的新插；库里多余的行删除（全量对齐前端）；
选定id 只在一行上置 是否选定=1，其余清零。
"""
import traceback

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.方案 import 方案
from 接口.controllers.方案列表 import 方案_to_dict
from 接口.返回.错误 import 取错误位置

卡字段 = ('标题', '故事线', '题材', '基调', '结局', '驱动', '风险')

版本名 = ['方案一', '方案二', '方案三', '方案四', '方案五', '方案六',
          '方案七', '方案八', '方案九', '方案十']


def _洗候选卡(源):
    """只保留七个字段且都是字符串，多余字段丢弃。"""
    源 = 源 if isinstance(源, dict) else {}
    return {键: str(源.get(键) or '') for 键 in 卡字段}


@api_view(['POST'])
def 方案保存(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            剧id = int(请求.data.get('剧id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        一剧 = 剧.objects.filter(id=剧id, 用户id=请求.user.id).first()
        if 一剧 is None:
            return Response({'ok': False, 'error': '剧不存在或无权保存。'}, status=status.HTTP_404_NOT_FOUND)

        方案们 = 请求.data.get('方案们')
        if not isinstance(方案们, list) or not 方案们:
            return Response({'ok': False, 'error': '方案们 不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        if len(方案们) > 10:
            return Response({'ok': False, 'error': '一次最多保存 10 个方案。'}, status=status.HTTP_400_BAD_REQUEST)

        选定id = 请求.data.get('选定id')
        try:
            选定id = int(选定id) if 选定id else 0
        except (TypeError, ValueError):
            选定id = 0

        现在 = timezone.now()
        # 2026-11-04：三步写（对齐行 → 清选定 → 置选定）包进事务，
        # 中途异常不再留下"删了旧方案又没写进新方案"的半删脏状态
        with transaction.atomic():
            提交ids = []
            结果行 = []
            for 序, 项 in enumerate(方案们):
                if not isinstance(项, dict):
                    continue
                卡 = _洗候选卡(项.get('候选卡'))
                版本 = (str(项.get('版本号') or '').strip()
                        or (版本名[序] if 序 < len(版本名) else '方案' + str(序 + 1)))
                行id = 项.get('id')
                try:
                    行id = int(行id) if 行id else 0
                except (TypeError, ValueError):
                    行id = 0

                if 行id:
                    一行 = 方案.objects.filter(id=行id, 剧id=剧id).first()
                    if 一行 is None:
                        continue
                    一行.版本号 = 版本
                    一行.候选卡 = 卡
                    一行.更新时间 = 现在
                    一行.save(update_fields=['版本号', '候选卡', '更新时间'])
                else:
                    一行 = 方案.objects.create(
                        剧id=剧id, 版本号=版本, 是否选定=False, 候选卡=卡,
                        创建时间=现在, 更新时间=现在,
                    )
                提交ids.append(一行.id)
                结果行.append(一行)

            if not 结果行:
                return Response({'ok': False, 'error': '没有可保存的方案。'}, status=status.HTTP_400_BAD_REQUEST)

            # 删掉前端已不存在的行（重新生成时全量对齐）
            方案.objects.filter(剧id=剧id).exclude(id__in=提交ids).delete()

            # 选定：只留一行 =1；未指定时定在提交顺序的第一行
            方案.objects.filter(剧id=剧id).update(是否选定=False)  # 先全清
            if 选定id and 选定id in 提交ids:
                方案.objects.filter(id=选定id).update(是否选定=True)
            else:
                选定id = 结果行[0].id
                方案.objects.filter(id=选定id).update(是否选定=True)

        行 = 方案.objects.filter(剧id=剧id).order_by('id')
        return Response({'ok': True, '选定id': 选定id, '列表': [方案_to_dict(一) for 一 in 行]})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
