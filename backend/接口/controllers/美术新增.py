# -*- coding: utf-8 -*-
"""美术新增控制器：POST api/美术/新增 {剧id, 类型, 名称, 别名, 级别, 摘要}。

/video/art 四分区「＋新增」入口：图片/美术资源全剧共用，不挂具体集，落库 集号=0
（资产清单按集提取/全量替换不经过 集号=0，互不干扰；美术列表不传集号即全量带出）。
- 资产id：按类型前缀 CHAR_/SCN_/PROP_/COST_ 在全剧范围顺延编号（取现有最大序号+1）
- 同步建美术定装行（派生逻辑与 美术初始化 相同：人物查档案，其余用摘要）
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback
import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.models.美术定装 import 美术定装
from 接口.controllers.美术初始化 import 拆条, 人物档案
from 接口.返回.错误 import 取错误位置

类型们 = ('人物', '场景', '道具', '服装')
前缀们 = {'人物': 'CHAR', '场景': 'SCN', '道具': 'PROP', '服装': 'COST'}


def 下一个资产id(剧id, 类型):
    """全剧范围该类型前缀的现有最大序号 + 1，如 CHAR_006。"""
    前缀 = 前缀们.get(类型, 'PROP')
    最大 = 0
    for (资产id,) in 资产.objects.filter(剧id=剧id, 资产id__startswith=前缀 + '_') \
            .values_list('资产id'):
        try:
            序 = int(str(资产id).split('_', 1)[1])
        except (IndexError, ValueError):
            continue
        if 序 > 最大:
            最大 = 序
    return '%s_%03d' % (前缀, 最大 + 1)


@api_view(['POST'])
def 美术新增(请求):
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

        类型 = str(数据.get('类型') or '').strip()
        if 类型 not in 类型们:
            return Response({'ok': False, 'error': '类型必须是 ' + '、'.join(类型们) + '。'},
                            status=status.HTTP_400_BAD_REQUEST)
        名称 = str(数据.get('名称') or '').strip()[:100]
        if not 名称:
            return Response({'ok': False, 'error': '名称不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        别名 = str(数据.get('别名') or '').strip()[:300]
        级别 = str(数据.get('级别') or '').strip()[:50]
        摘要 = str(数据.get('摘要') or '').strip()

        资产id = 下一个资产id(剧id, 类型)
        此刻 = datetime.datetime.now()

        资产行 = 资产.objects.create(
            剧id=剧id,
            集号=0,          # 全剧共用资源，不挂具体集
            资产id=资产id,
            类型=类型,
            名称=名称,
            别名=别名 or None,
            关系='新增',
            级别=级别 or None,
            摘要=摘要,
            排序=999,
            创建时间=此刻,
            更新时间=此刻,
        )

        # 定装派生：与 美术初始化 同口径（人物查档案，其余用摘要）
        保持们 = []
        提示词 = ''
        音色 = ''
        if 类型 == '人物':
            人 = 人物档案(剧id, 资产id)
            if 人:
                保持们 = 拆条((人.外貌 or '') + '\n' + (人.穿搭 or ''))
                提示词 = '，'.join([x for x in [(人.性别 or ''), (人.年龄档 or ''), (人.外貌 or ''), (人.穿搭 or '')] if x])
                音色 = 人.音色提示词 or ''
                if not 音色:
                    音色 = '，'.join([x for x in [
                        (人.性别 or ''), '自然', '·', (人.年龄档 or ''), (人.身份 or '')
                    ] if x and x != '·'])
            else:
                保持们 = 拆条(摘要)
                提示词 = 摘要
        else:
            保持们 = 拆条(摘要)
            提示词 = 摘要

        定装 = 美术定装.objects.create(
            资产行id=资产行.id,
            全局风格='',
            画幅='9:16',
            分辨率='480p',
            生图提示词=提示词 or 摘要,
            必须保持='\n'.join(保持们),
            禁止出现='',
            生图状态='待生成',
            音色提示词=音色 if 类型 == '人物' else '',
            音色url=None,
            音色状态='待生成',
            创建时间=此刻,
            更新时间=此刻,
        )

        return Response({'ok': True, '资产行id': 资产行.id, '定装id': 定装.id,
                         '资产id': 资产id, '类型': 类型, '名称': 名称})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
