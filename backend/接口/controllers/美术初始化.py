# -*- coding: utf-8 -*-
"""美术初始化控制器：POST api/美术/初始化 {剧id, 集号}。/video/art 首次进入自动建定装。

为该集每个还没有美术定装行的资产行创建一行（幂等：只补缺，不覆盖已有）：
- 人物：必须保持 = 人物档案 外貌/穿搭 拆行；生图提示词 = 外貌+穿搭；音色提示词 = 人物表值或按档案构造
- 场景/道具/服装：必须保持 = 资产摘要拆句；生图提示词 = 摘要
不生成图片本身（参考图由 重新生成/上传 产生）。
"""
import traceback
import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.models.人物 import 人物
from 接口.models.美术定装 import 美术定装
from 接口.返回.错误 import 取错误位置


def 拆条(文本):
    """把长文本拆成条目行：按句号/分号/换行切，去空去重，每行一条。"""
    if not 文本:
        return []
    段们 = str(文本).replace('\r', '\n').split('\n')
    结果 = []
    for 段 in 段们:
        段 = 段.strip()
        if not 段:
            continue
        for 句 in 段.replace('。', '；').replace('；', '；\n').split('\n'):
            句 = 句.strip().rstrip('；;')
            if 句 and 句 not in 结果:
                结果.append(句)
    return 结果


def 人物档案(剧id, 资产id):
    """按 资产id==人物id 找人物档案行；找不到返回 None。"""
    try:
        return 人物.objects.filter(剧id=剧id, 人物id=资产id).first()
    except Exception:
        return None


@api_view(['POST'])
def 美术初始化(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        数据 = 请求.data if isinstance(请求.data, dict) else {}
        try:
            剧id = int(数据.get('剧id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        集号 = 数据.get('集号')
        查询 = 资产.objects.filter(剧id=剧id)
        if 集号 not in (None, ''):
            try:
                查询 = 查询.filter(集号=int(集号))
            except (TypeError, ValueError):
                pass

        资产行们 = list(查询.order_by('集号', '排序', 'id'))
        已有ids = set(美术定装.objects.filter(
            资产行id__in=[行.id for 行 in 资产行们]).values_list('资产行id', flat=True))

        此刻 = datetime.datetime.now()
        新建 = 0
        for 资产行 in 资产行们:
            if 资产行.id in 已有ids:
                continue

            保持们 = []
            提示词 = ''
            音色 = ''

            if 资产行.类型 == '人物':
                人 = 人物档案(剧id, 资产行.资产id)
                if 人:
                    保持们 = 拆条((人.外貌 or '') + '\n' + (人.穿搭 or ''))
                    提示词 = '，'.join([x for x in [(人.性别 or ''), (人.年龄档 or ''), (人.外貌 or ''), (人.穿搭 or '')] if x])
                    音色 = 人.音色提示词 or ''
                    if not 音色:
                        音色 = '，'.join([x for x in [
                            (人.性别 or ''), '自然', '·', (人.年龄档 or ''), (人.身份 or '')
                        ] if x and x != '·'])
                else:
                    保持们 = 拆条(资产行.摘要)
                    提示词 = 资产行.摘要
            else:
                保持们 = 拆条(资产行.摘要)
                提示词 = 资产行.摘要

            美术定装.objects.create(
                资产行id=资产行.id,
                全局风格='',
                画幅='9:16',
                分辨率='480p',
                生图提示词=提示词 or (资产行.摘要 or ''),
                必须保持='\n'.join(保持们),
                禁止出现='',
                生图状态='待生成',
                音色提示词=音色 if 资产行.类型 == '人物' else '',
                音色url=None,
                音色状态='待生成',
                创建时间=此刻,
                更新时间=此刻,
            )
            新建 += 1

        return Response({'ok': True, '新建': 新建, '已存在': len(资产行们) - 新建})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
