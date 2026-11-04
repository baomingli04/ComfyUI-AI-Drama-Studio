# -*- coding: utf-8 -*-
"""分镜视频接口：GET api/分镜/视频 列表 + POST api/分镜/视频保存。单镜生成的历史版本管理。

GET  {剧id, 集号[, 镜号]}                        → 版本列表（新在前，带选中标记）
POST {剧id, 集号, 镜号, 动作, ...}：
- 动作=添加 {方式, 提示词, 任务id[, url]}        → 落一行：有 url=已生成（首版自动选中），无 url=生成中（提交任务后先占位）
- 动作=完成 {id, url}                            → 生成成功：写 url、状态=已生成（该镜无选中版时自动选中）
- 动作=失败 {id[, 错误]}                         → 生成失败：状态=失败
- 动作=设选中 {id}                               → 该版设为选中（同镜其他版取消）
- 动作=删除 {id}                                 → 删这一版；删选中版时自动把最新一版设为选中
- 动作=清空 {}                                   → 删该镜全部版本
挂业务键 (剧id, 集号, 镜号)；归属校验：剧的用户id 必须等于当前登录用户。
"""
import datetime
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分镜视频 import 分镜视频
from 接口.返回.错误 import 取错误位置


@api_view(['GET', 'POST'])
def 分镜视频接口(请求):
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

        if 请求.method == 'GET':
            查询 = 分镜视频.objects.filter(剧id=剧id, 集号=集号)
            镜号筛 = str(参数.get('镜号') or '').strip()[:20]
            if 镜号筛:
                查询 = 查询.filter(镜号=镜号筛)
            列表 = []
            for 行 in 查询.order_by('-id'):
                列表.append({
                    'id': 行.id, '镜号': 行.镜号 or '', '方式': 行.方式 or '',
                    '提示词': 行.提示词 or '', '任务id': 行.任务id or None,
                    'url': 行.url or '', '状态': 行.状态 or '已生成',
                    '选中': bool(行.选中), '创建时间': 行.创建时间.isoformat() if 行.创建时间 else None,
                })
            return Response({'ok': True, '总数': len(列表), '版本们': 列表})

        数据 = 参数

        动作 = str(数据.get('动作') or '').strip()
        镜号 = str(数据.get('镜号') or '').strip()[:20]
        if 动作 not in ('添加', '完成', '失败', '设选中', '删除', '清空'):
            return Response({'ok': False, 'error': '动作必须是 添加/完成/失败/设选中/删除/清空。'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not 镜号:
            return Response({'ok': False, 'error': '缺少镜号。'}, status=status.HTTP_400_BAD_REQUEST)

        此刻 = datetime.datetime.now()

        if 动作 == '添加':
            url = str(数据.get('url') or '').strip()[:512]
            方式 = str(数据.get('方式') or '').strip()[:50] or None
            提示词 = str(数据.get('提示词') or '').strip() or None
            try:
                任务id = int(数据.get('任务id'))
            except (TypeError, ValueError):
                任务id = None
            with transaction.atomic():
                无选中 = not 分镜视频.objects.filter(
                    剧id=剧id, 集号=集号, 镜号=镜号, 选中=True, 状态='已生成').exists()
                行 = 分镜视频.objects.create(
                    剧id=剧id, 集号=集号, 镜号=镜号,
                    方式=方式, 提示词=提示词, 任务id=任务id, url=url or None,
                    状态='已生成' if url else '生成中', 选中=bool(url) and 无选中,
                    创建时间=此刻, 更新时间=此刻)
            return Response({'ok': True, 'id': 行.id, '选中': 行.选中})

        if 动作 in ('完成', '失败'):
            try:
                版本id = int(数据.get('id'))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '缺少版本 id。'}, status=status.HTTP_400_BAD_REQUEST)
            版 = 分镜视频.objects.filter(id=版本id, 剧id=剧id, 集号=集号, 镜号=镜号).first()
            if not 版:
                return Response({'ok': False, 'error': '版本不存在。'}, status=status.HTTP_404_NOT_FOUND)
            if 动作 == '失败':
                版.状态 = '失败'
                版.更新时间 = 此刻
                版.save()
                return Response({'ok': True})
            url = str(数据.get('url') or '').strip()[:512]
            if not url:
                return Response({'ok': False, 'error': '缺少视频地址。'}, status=status.HTTP_400_BAD_REQUEST)
            版.url = url
            版.状态 = '已生成'
            版.更新时间 = 此刻
            if not 分镜视频.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号, 选中=True, 状态='已生成').exclude(id=版.id).exists():
                版.选中 = True
            版.save()
            return Response({'ok': True, '选中': 版.选中})

        if 动作 == '清空':
            分镜视频.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号).delete()
            return Response({'ok': True})

        # 以下动作都需要 版本id
        try:
            版本id = int(数据.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少版本 id。'}, status=status.HTTP_400_BAD_REQUEST)
        版 = 分镜视频.objects.filter(id=版本id, 剧id=剧id, 集号=集号, 镜号=镜号).first()
        if not 版:
            return Response({'ok': False, 'error': '版本不存在。'}, status=status.HTTP_404_NOT_FOUND)

        if 动作 == '设选中':
            with transaction.atomic():
                分镜视频.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号).exclude(id=版本id).update(选中=False, 更新时间=此刻)
                版.选中 = True
                版.更新时间 = 此刻
                版.save()
            return Response({'ok': True, 'id': 版.id, '选中': True})

        if 动作 == '删除':
            # 2026-11-04：删版本+补选中包进事务，防并发时出现"无任何选中版"（成片会拒合）
            from django.db import transaction as _事务
            原选中 = 版.选中
            with _事务.atomic():
                版.delete()
                若删除了选中 = False
                if 原选中:
                    最新 = 分镜视频.objects.filter(剧id=剧id, 集号=集号, 镜号=镜号).order_by('-id').first()
                    if 最新:
                        最新.选中 = True
                        最新.更新时间 = 此刻
                        最新.save()
                        若删除了选中 = True
            return Response({'ok': True, '补选中': 若删除了选中})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
