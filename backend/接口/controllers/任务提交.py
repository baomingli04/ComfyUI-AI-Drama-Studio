# -*- coding: utf-8 -*-
"""任务提交控制器：POST 任务/提交。立刻返回任务 id，不执行。"""
import traceback

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置

允许类型 = ['文本回复', '图片解析', '生成图片', '文生图8K',
            '三图编辑一致版', '多图编辑多人合并版', '动漫转真人',
            '人物替换', '首尾帧', '参考生视频', '去水印', '二采重绘', '文生视频',
            '多参考生视频', '首尾帧生视频',
            '视频生视频', '参考视频生视频', '加速版生视频',
            '二采加速生视频', '外部分组图生视频',
            '外部分组多参考生视频', '导演台全能']

可存文本 = ['正向提示词', '反向提示词', '系统提示词',
            '组1提示词', '组2提示词', '组3提示词', '组4提示词']
可存小数 = ['组1时长', '组2时长', '组3时长', '组4时长']
可存图 = ['输入图1', '输入图2', '输入图3', '输入图4', '输入图5', '输入图6', '输入图7', '输入图8', '输入图9']
可存视频 = ['输入视频1', '输入视频2', '输入视频3']
可存音频 = ['输入音频1', '输入音频2', '输入音频3']


@api_view(['POST'])
def 任务提交(请求):
    """创建任务记录（状态=已创建），执行交给后续 ComfyUI 环节。"""
    try:
        类型 = (请求.data.get('类型') or '').strip()
        if 类型 not in 允许类型:
            return Response(
                {'ok': False, 'error': '未知任务类型：' + 类型},
                status=status.HTTP_400_BAD_REQUEST,
            )

        参数 = {
            '类型': 类型,
            '状态': '已创建',
            '创建人id': 请求.user,
            '创建时间': timezone.now(),
        }

        for 字段 in 可存文本:
            if 字段 in 请求.data:
                参数[字段] = 请求.data.get(字段) or ''

        for 字段 in 可存小数:
            if 请求.data.get(字段) not in (None, ''):
                参数[字段] = 请求.data.get(字段)

        for 字段 in 可存图 + 可存视频 + 可存音频:
            if 请求.data.get(字段):
                参数[字段] = (请求.data.get(字段) or '').strip()

        if 请求.data.get('图片宽'):
            参数['图片宽'] = int(请求.data.get('图片宽'))
        if 请求.data.get('图片高'):
            参数['图片高'] = int(请求.data.get('图片高'))
        if 请求.data.get('视频宽'):
            参数['视频宽'] = int(请求.data.get('视频宽'))
        if 请求.data.get('视频高'):
            参数['视频高'] = int(请求.data.get('视频高'))
        if 请求.data.get('seed') not in (None, ''):
            参数['seed'] = int(请求.data.get('seed'))
        if 请求.data.get('水印') is not None:
            参数['水印'] = bool(请求.data.get('水印'))
        if 请求.data.get('一采MP') not in (None, ''):
            参数['一采MP'] = 请求.data.get('一采MP')
        if 请求.data.get('二采MP') not in (None, ''):
            参数['二采MP'] = 请求.data.get('二采MP')
        if 请求.data.get('比例') not in (None, ''):
            参数['比例'] = str(请求.data.get('比例')).strip()
        if 请求.data.get('视频时长') not in (None, ''):
            参数['视频时长'] = 请求.data.get('视频时长')
        if 请求.data.get('cfg') not in (None, ''):
            参数['cfg'] = 请求.data.get('cfg')
        if 请求.data.get('模式') not in (None, ''):
            参数['模式'] = str(请求.data.get('模式')).strip()
        if 请求.data.get('采样器') not in (None, ''):
            参数['采样器'] = str(请求.data.get('采样器')).strip()
        if 请求.data.get('底膜精度') not in (None, ''):
            参数['底膜精度'] = str(请求.data.get('底膜精度')).strip()
        if 请求.data.get('步数') not in (None, ''):
            参数['步数'] = int(请求.data.get('步数'))
        if 请求.data.get('生成声音') is not None:
            参数['生成声音'] = bool(请求.data.get('生成声音'))

        # 可选 技能id：带上了就把该技能的 SKILL.md 规范注入系统提示词（口径同 提示词扩写，
        # 模式=image 只读 SKILL.md）。拼好再落库，任务日志里能看到完整系统提示词。
        if 请求.data.get('技能id') not in (None, ''):
            try:
                传技能id = int(请求.data.get('技能id'))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '技能id 必须是数字。'},
                                status=status.HTTP_400_BAD_REQUEST)
            from 接口.models.技能 import 技能
            from 接口.controllers.提示词扩写 import _读技能规范
            一技能 = 技能.objects.filter(id=传技能id).first()
            if 一技能 is None:
                return Response({'ok': False, 'error': '技能不存在（id=%d）' % 传技能id},
                                status=status.HTTP_400_BAD_REQUEST)
            规范 = _读技能规范(一技能.目录名, 'image')
            参数['系统提示词'] = (
                (参数.get('系统提示词') or '').strip()
                + '\n\n==== 技能规范 ====\n' + 规范
            ).strip()

        实例 = task.objects.create(**参数)

        # 唤醒任务执行器（真正执行由 能力/提交并等待 的工作线程做）
        from 能力.提交并等待 import 入队
        入队(实例.id)

        return Response({'ok': True, 'id': 实例.id})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
