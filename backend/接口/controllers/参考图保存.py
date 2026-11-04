# -*- coding: utf-8 -*-
"""参考图保存控制器：POST api/美术/参考图保存。单图操作（添加/编辑/删除/设状态/同步外形）。

请求 {定装id, 动作, ...}：
- 动作=添加 {url, 标注, 来源(默认 上传), 分类(默认父资产类型), 形态, 提示词, 关联人物} → 新建一行，状态默认 当前
- 动作=编辑 {id, 标注, url, 提示词, 分类, 形态, 关联人物}  → 改标注/地址/提示词/分类/形态/关联人物
- 动作=删除 {id}                           → 删除该图
- 动作=转历史 {id}                         → 状态置 历史
- 动作=恢复 {id}                           → 状态置 当前（多张当前可共存）
- 动作=同步外形 {id}                       → 把该图提示词按 外貌/身材/穿搭 拆字段写回关联角色的人物档案：
                                            该角色此前没有图 → 直接覆盖原字段；
                                            已有图 → 追加/替换一套（套名=图形态，空则 外形N），
                                            档案字段内多套用【套名】分段存（无标签首段=默认套）
- 动作=删资产 {}                            → 删除整个美术资产（全部参考图+定装行+资产行），不需要图 id
归属校验：定装 → 资产 → 剧 的用户id 必须等于当前登录用户。
"""
import re
import traceback
import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.models.人物 import 人物
from 接口.models.美术定装 import 美术定装
from 接口.models.参考图 import 参考图
from 接口.返回.错误 import 取错误位置

外形字段们 = ('外貌', '身材', '穿搭')


def 拆提示词字段(文本):
    """人物图解析结果按行拆 外貌/身材/穿搭；没有任何结构行时整段归 外貌。"""
    映射 = {}
    其余 = []
    for 行 in str(文本 or '').replace('\r', '\n').split('\n'):
        行 = 行.strip()
        if not 行:
            continue
        for 键 in 外形字段们:
            if 行.startswith(键 + '：') or 行.startswith(键 + ':'):
                值 = 行[len(键) + 1:].strip().lstrip('；;，,').strip()
                if 值:
                    映射[键] = 值
                break
        else:
            其余.append(行)
    if not 映射 and 其余:
        映射['外貌'] = '\n'.join(其余)
    return 映射


def 套段们(文本):
    """把字段值拆成 [(套名或'', 内容)]；按【套名】分段，无标签首段=默认套。"""
    文本 = (文本 or '').strip()
    if not 文本:
        return []
    部分 = re.split(r'【([^】]*)】', 文本)
    段们 = []
    if 部分[0].strip():
        段们.append(('', 部分[0].strip()))
    i = 1
    while i < len(部分):
        名 = 部分[i].strip()
        文 = 部分[i + 1].strip() if i + 1 < len(部分) else ''
        段们.append((名, 文))
        i += 2
    return 段们


def 写套(旧值, 套名, 新值):
    """字段里替换/追加一套外形；旧值为空直接写（首套无标签），无套名追加为 外形N。"""
    旧值 = (旧值 or '').strip()
    if not 旧值:
        return 新值
    段们 = 套段们(旧值)
    if not 套名:
        套名 = '外形' + str(len(段们) + 1)
    for i, (名, 文) in enumerate(段们):
        if 名 == 套名:
            段们[i] = (名, 新值)
            break
    else:
        段们.append((套名, 新值))
    return '\n'.join([('【' + 名 + '】' + 文) if 名 else 文 for 名, 文 in 段们])


def 校验归属(请求, 定装id):
    定装 = 美术定装.objects.filter(id=定装id).first()
    if not 定装:
        return None, None
    资产行 = 资产.objects.filter(id=定装.资产行id).first()
    剧行 = 剧.objects.filter(id=资产行.剧id).first() if 资产行 else None
    if not 剧行 or 剧行.用户id != 请求.user.id:
        return None, None
    return 定装, 资产行


@api_view(['POST'])
def 参考图保存(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        数据 = 请求.data if isinstance(请求.data, dict) else {}
        动作 = str(数据.get('动作') or '').strip()
        if 动作 not in ('添加', '编辑', '删除', '转历史', '恢复', '同步外形', '删资产'):
            return Response({'ok': False, 'error': '动作必须是 添加/编辑/删除/转历史/恢复/同步外形/删资产。'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            定装id = int(数据.get('定装id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少定装 id。'}, status=status.HTTP_400_BAD_REQUEST)

        定装, 资产行 = 校验归属(请求, 定装id)
        if not 定装:
            return Response({'ok': False, 'error': '定装行不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        此刻 = datetime.datetime.now()

        if 动作 == '删资产':
            # 删除整个美术资产：该资产全部参考图 + 定装行 + 资产行（不需要图 id）
            参考图.objects.filter(资产行id=定装id).delete()
            定装.delete()
            资产id = 资产行.资产id if 资产行 else ''
            if 资产行:
                资产行.delete()
            return Response({'ok': True, '删除资产': 资产id})

        if 动作 == '添加':
            url = str(数据.get('url') or '').strip()
            if not url:
                return Response({'ok': False, 'error': '缺少图片地址。'}, status=status.HTTP_400_BAD_REQUEST)
            if len(url) > 512:
                url = url[:512]
            标注 = str(数据.get('标注') or '').strip()[:200]
            来源 = str(数据.get('来源') or '上传').strip()
            if 来源 not in ('生成', '上传'):
                来源 = '上传'
            # 分类：默认继承父资产类型；形态：同一资产的不同服装/状态标签
            分类 = str(数据.get('分类') or '').strip()[:10] or (资产行.类型 if 资产行 else None)
            形态 = str(数据.get('形态') or '').strip()[:50] or None
            提示词 = str(数据.get('提示词') or '').strip() or None
            关联人物 = str(数据.get('关联人物') or '').strip()[:50] or None
            已有数 = 参考图.objects.filter(资产行id=定装id).count()
            行 = 参考图.objects.create(
                资产行id=定装id,
                url=url,
                标注=标注 or None,
                提示词=提示词,
                分类=分类,
                形态=形态,
                关联人物=关联人物,
                来源=来源,
                状态='当前',
                排序=已有数,
                创建时间=此刻,
                更新时间=此刻,
            )
            return Response({'ok': True, 'id': 行.id})

        try:
            图id = int(数据.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少参考图 id。'}, status=status.HTTP_400_BAD_REQUEST)

        图 = 参考图.objects.filter(id=图id, 资产行id=定装id).first()
        if not 图:
            return Response({'ok': False, 'error': '参考图不存在。'}, status=status.HTTP_404_NOT_FOUND)

        if 动作 == '编辑':
            if '标注' in 数据:
                图.标注 = str(数据.get('标注') or '').strip()[:200] or None
            if 'url' in 数据 and str(数据.get('url') or '').strip():
                图.url = str(数据.get('url')).strip()[:512]
            if '提示词' in 数据:
                图.提示词 = str(数据.get('提示词') or '').strip() or None
            if '分类' in 数据:
                图.分类 = str(数据.get('分类') or '').strip()[:10] or None
            if '形态' in 数据:
                图.形态 = str(数据.get('形态') or '').strip()[:50] or None
            if '关联人物' in 数据:
                图.关联人物 = str(数据.get('关联人物') or '').strip()[:50] or None
            图.更新时间 = 此刻
            图.save()
        elif 动作 == '删除':
            图.delete()
        elif 动作 == '转历史':
            图.状态 = '历史'
            图.更新时间 = 此刻
            图.save()
        elif 动作 == '恢复':
            图.状态 = '当前'
            图.更新时间 = 此刻
            图.save()
        elif 动作 == '同步外形':
            if not (图.提示词 or '').strip():
                return Response({'ok': False, 'error': '该图还没有提示词，先「解析提示词」或手动填写。'},
                                status=status.HTTP_400_BAD_REQUEST)
            人物id = (图.关联人物 or '').strip()
            if not 人物id and 资产行 and 资产行.类型 == '人物':
                人物id = (资产行.资产id or '').strip()   # 未显式关联时按资产id自动匹配
            人 = 人物.objects.filter(剧id=资产行.剧id, 人物id=人物id).first() if 人物id else None
            if not 人:
                return Response({'ok': False, 'error': '这张图还没关联角色（且资产 id 匹配不到人物档案），先在卡片上选关联角色。'},
                                status=status.HTTP_404_NOT_FOUND)
            字段映射 = 拆提示词字段(图.提示词)
            if not 字段映射:
                return Response({'ok': False, 'error': '提示词里没有可写回的外形内容。'},
                                status=status.HTTP_400_BAD_REQUEST)
            # 该角色此前没有别的图 → 第一套，直接覆盖原字段；否则按套追加/替换
            其他图数 = 参考图.objects.filter(资产行id=图.资产行id).exclude(id=图.id).count()
            套名 = (图.形态 or '').strip() or (图.标注 or '').strip() or ''
            更新们 = []
            for 键 in 外形字段们:
                if 键 in 字段映射:
                    if 其他图数 == 0:
                        新值 = 字段映射[键]   # 该角色第一张图：直接用图片解析的外形覆盖原字段
                    else:
                        新值 = 写套(getattr(人, 键) or '', 套名, 字段映射[键])
                    if 键 == '身材':
                        新值 = 新值[:255]   # 身材是 varchar(255)，多套时截断
                    setattr(人, 键, 新值)
                    更新们.append(键)
            if not 更新们:
                return Response({'ok': False, 'error': '提示词里没有 外貌/身材/穿搭 字段可写。'},
                                status=status.HTTP_400_BAD_REQUEST)
            人.更新时间 = 此刻
            人.save()
            return Response({'ok': True, '人物': 人.名 or 人物id, '套名': 套名 or ('默认' if 其他图数 == 0 else '外形'),
                             '首套': 其他图数 == 0, '更新': 更新们})

        return Response({'ok': True})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
