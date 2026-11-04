# -*- coding: utf-8 -*-
"""分镜图保存控制器：POST api/分镜/图保存。单镜页的每镜独立创作资源区。

请求 {剧id, 集号, 镜号, 动作, ...}：
- 动作=添加 {url, 标注, 来源(默认 上传), 提示词}   → 落一行
- 动作=编辑 {id, 标注}                              → 改标注
- 动作=删除 {id}                                    → 删这一行
- 动作=清空 {}                                      → 该镜资源图整组清掉（拆分分镜页清空/重拆时用）
GET api/分镜/图?剧id=&集号=&镜号= → 该镜全部资源图。
资产图不落这里（只在前端引用美术列表），归属校验走 剧.用户id。
"""
import datetime
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分镜图 import 分镜图
from 接口.返回.错误 import 取错误位置


def 行字典(行):
    return {
        'id': 行.id,
        '镜号': 行.镜号 or '',
        'url': 行.url or '',
        '标注': 行.标注 or '',
        '来源': 行.来源 or '上传',
        '提示词': 行.提示词 or '',
        '排序': 行.排序 or 0,
    }


@api_view(['GET', 'POST'])
def 分镜图接口(请求):
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

        镜号 = str(参数.get('镜号') or '').strip()[:20]
        if not 镜号:
            return Response({'ok': False, 'error': '缺少镜号。'}, status=status.HTTP_400_BAD_REQUEST)

        if 请求.method == 'GET':
            行们 = 分镜图.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号).order_by('排序', 'id')
            return Response({'ok': True, '镜号': 镜号, '图们': [行字典(行) for 行 in 行们]})

        数据 = 参数
        动作 = str(数据.get('动作') or '').strip()
        if 动作 not in ('添加', '编辑', '删除', '清空'):
            return Response({'ok': False, 'error': '动作必须是 添加/编辑/删除/清空。'},
                            status=status.HTTP_400_BAD_REQUEST)

        此刻 = datetime.datetime.now()

        if 动作 == '清空':
            # 该镜资源图整组清掉（拆分分镜页清空/重拆时同步清理用）
            数 = 分镜图.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号).delete()
            return Response({'ok': True, '删除数': 数[0] if isinstance(数, tuple) else 0})

        if 动作 == '添加':
            url = str(数据.get('url') or '').strip()[:512]
            if not url:
                return Response({'ok': False, 'error': '缺少图片地址。'}, status=status.HTTP_400_BAD_REQUEST)
            标注 = str(数据.get('标注') or '').strip()[:200] or None
            来源 = str(数据.get('来源') or '上传').strip()
            if 来源 not in ('上传', '资产', '生成'):
                来源 = '上传'
            提示词 = str(数据.get('提示词') or '').strip() or None
            已有数 = 分镜图.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号).count()
            行 = 分镜图.objects.create(
                剧id=剧id, 集号=集号, 镜号=镜号,
                url=url, 标注=标注, 来源=来源, 提示词=提示词,
                排序=已有数, 创建时间=此刻, 更新时间=此刻)
            return Response({'ok': True, 'id': 行.id})

        try:
            图id = int(数据.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少图片 id。'}, status=status.HTTP_400_BAD_REQUEST)
        行 = 分镜图.objects.filter(id=图id, 剧id=剧id, 集号=集号, 镜号=镜号).first()
        if not 行:
            return Response({'ok': False, 'error': '图片不存在。'}, status=status.HTTP_404_NOT_FOUND)

        if 动作 == '编辑':
            if '标注' in 数据:
                行.标注 = str(数据.get('标注') or '').strip()[:200] or None
            if '排序' in 数据:
                try:
                    行.排序 = int(数据.get('排序'))
                except (TypeError, ValueError):
                    pass
            行.更新时间 = 此刻
            行.save()
        elif 动作 == '删除':
            行.delete()
        return Response({'ok': True})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
