# -*- coding: utf-8 -*-
"""提示词扩写：POST api/提示词/扩写。

学旧项目 promptgen 的约定（用户拍板的规则不偏离）：
- 技能规范 = 技能目录下 SKILL.md + references/base-en.txt（single_frame）
  或 references/ref-en.txt（multi_reference）。
- 图片不发给本地 LLM，仅作命名锚点；@图N/@视频N/@音频N 是硬占位符，
  模型必须替换成规范标签（<Picture N>/<Subject N>/<Video N>/<Audio N>），输出不得残留 @。
- 不擅自添加用户未要求的角色/情节/元素。
body: { 技能id, 模式: single_frame|multi_reference, 需求, 引用:[{名称,类型}], 声音模式, 附加规则 }
- 附加规则 = 用户在该页「扩写提示词配置」里写的规则，前端整段传来，后端原样插成 system 的
  「用户附加规则（最高优先级）」段，不改写、不拼接用户内容。
返回 { ok, 提示词 }
"""
import traceback

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 能力.LLM调用 import 调用LLM
from 接口.models.技能 import 技能
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 提示词扩写(请求):
    try:
        数据 = 请求.data or {}
        技能id = 数据.get('技能id')
        模式 = (数据.get('模式') or 'single_frame').strip()
        需求 = (数据.get('需求') or '').strip()
        引用 = 数据.get('引用') or []
        声音模式 = (数据.get('声音模式') or 'dialogue_only').strip()
        # 用户在本页「扩写提示词配置」里写的规则：前端整段传来，原样插入，后端不改一个字
        附加规则 = (数据.get('附加规则') or '').strip()

        if not 技能id:
            raise ValueError('技能id 必填')
        if 模式 not in ('image', 'single_frame', 'multi_reference'):
            raise ValueError('模式只能是 image / single_frame / multi_reference')
        if not 需求:
            raise ValueError('需求（要扩写的内容）不能为空')

        实例 = 技能.objects.filter(id=技能id).first()
        if 实例 is None:
            raise ValueError('技能不存在（id=%s）' % 技能id)

        规范 = _读技能规范(实例.目录名, 模式)

        # 统计素材引用（仅命名，不传文件给 LLM）
        图数 = sum(1 for r in 引用 if (r.get('类型') or '') == 'image')
        视频数 = sum(1 for r in 引用 if (r.get('类型') or '') == 'video')
        音频数 = sum(1 for r in 引用 if (r.get('类型') or '') == 'audio')

        模式规则, 替换规则 = _模式与替换规则(模式, 图数)
        声音规则 = _声音规则(声音模式) if 模式 != 'image' else ''

        系统 = (
            '你是视频/图片生成提示词写手。严格按下面给定的规则写提示词，'
            '只输出提示词本身，不要任何解释、前缀或后缀。\n\n'
            '==== 模式规则 ====\n' + 模式规则 + '\n\n'
            '==== 引用替换规则 ====\n' + 替换规则 + '\n\n'
            + 声音规则 + '\n\n'
            '==== 素材清单 ====\n'
            '图片 %d 张（@图1..@图%d）、视频 %d 个（@视频1..@视频%d）、音频 %d 个（@音频1..@音频%d）。\n\n'
            '==== 技能规范 ====\n' + 规范
        ) % (图数, max(图数, 1), 视频数, max(视频数, 1), 音频数, max(音频数, 1))

        if 附加规则:
            系统 += ('\n\n==== 用户附加规则（最高优先级，与上文冲突时以本节为准）====\n'
                     + 附加规则)

        提示词 = 调用LLM([
            {'role': 'system', 'content': 系统},
            {'role': 'user', 'content': 需求},
        ]).strip()

        # 硬替换兜底：输出残留 @引用 时按规则替换
        提示词 = _兜底替换(提示词, 图数)

        return Response({'ok': True, '提示词': 提示词})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _转义(文本):
    """规范原文里可能出现裸 % （如 size%/tilt），而规范会被拼进 % 格式化字符串，
    裸 % 会被当成占位符导致 TypeError。读取时先转义成 %%，格式化后还原为单个 %。"""
    return 文本.replace('%', '%%')


def _读技能规范(目录名, 模式):
    根 = settings.SKILL_DIR / 目录名
    parts = []
    技能md = 根 / 'SKILL.md'
    if 技能md.is_file():
        parts.append(_转义(技能md.read_text(encoding='utf-8', errors='ignore')))
    规范名 = 'ref-en.txt' if 模式 == 'multi_reference' else 'base-en.txt'
    规范文件 = 根 / 'references' / 规范名
    if 规范文件.is_file():
        parts.append('# 规范文件 ' + 规范名 + '\n'
                     + _转义(规范文件.read_text(encoding='utf-8', errors='ignore')))
    else:
        for 名 in ('base-en.txt', 'ref-en.txt'):
            另 = 根 / 'references' / 名
            if 另.is_file():
                parts.append('# 规范文件 ' + 名 + '\n'
                             + _转义(另.read_text(encoding='utf-8', errors='ignore')))
    if not parts:
        raise ValueError('技能 %s 没有可读取的规范（SKILL.md / references）' % 目录名)
    return '\n\n'.join(parts)


def _模式与替换规则(模式, 图数):
    if 模式 == 'image':
        模式规则 = (
            'image（图片生成/图片编辑模式）：把用户的简短描述扩写成一段详细、具体、可直接用于'
            '图片生成模型的提示词：写清主体外观、动作姿态、场景环境、光影氛围、构图视角、'
            '画面风格与画质要求；保持用户原有意图，不擅自添加用户未要求的角色或情节；'
            '写一段连贯文字即可，不要分点、不要标题。'
        )
        替换规则 = '本模式无 @引用 标签体系；若需求里出现 @图N，按「图N」理解并在文字中自然描述其作用即可。'
        return 模式规则, 替换规则
    if 模式 == 'single_frame':
        if 图数 >= 2:
            模式规则 = (
                'single_frame（首尾帧 FL2VA 双图模式）：图1=首帧、图2=尾帧（顺序即上传顺序）。'
                '按 base-en.txt 的 FL2VA 写法——提示词首行用对齐行（无尖括号）：'
                '「How the reference pictures align with the target video — '
                'Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; '
                'Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.」，'
                '随后写 integrated_multimodal_description / overall_soundscape / non_diegetic_music 三段。'
            )
            替换规则 = ('@图N 必须硬替换为无尖括号的 Picture N（图1→Picture 1 首帧，图2→Picture 2 尾帧）；'
                        '输出不得残留 @ 符号。')
        elif 图数 == 1:
            模式规则 = (
                'single_frame（首帧/单图 I2VA 模式）：图1=首帧。按 base-en.txt 的 I2VA 写法——'
                '提示词首行用：「For the target video, at 0.00 seconds into the target video, '
                '<Picture 1> (from [Shot 1]) is fully referenced.」，随后写三段字段。'
            )
            替换规则 = '@图N 必须硬替换为 <Picture N>（带尖括号，I2VA 首帧锚点）；输出不得残留 @ 符号。'
        else:
            模式规则 = ('single_frame（文生图/文生视频模式）：无参考图。按 base-en.txt 直接输出 '
                        'integrated_multimodal_description / overall_soundscape / non_diegetic_music 三段。')
            替换规则 = '本模式无 @图 引用；若需求写了 @图N，忽略它，不引入图片标签。'
    else:
        模式规则 = (
            'multi_reference（全参考/多参考生成）：输出六个段落——'
            'subject_definitions、summary、retention_analysis、detailed_description、'
            'overall_soundscape、non_diegetic_music，按 ref-en.txt 写法，'
            '使用 <Subject N>/<Picture N>/<Video N>/<Audio N> 标签体系。'
        )
        替换规则 = ('@引用必须硬替换为规范标签（输出不得残留 @ 符号）：'
                    '@图N → 具体帧/关键帧锚点用 <Picture N>，可复用的人物/场景/服装/风格用 <Subject N>；'
                    '@视频N → <Video N>；@音频N → <Audio N>。标签编号 N 与需求里写的 N 一致。')
    return 模式规则, 替换规则


def _声音规则(声音模式):
    if 声音模式 == 'silent':
        return '声音控制（强制）：overall_soundscape 与 non_diegetic_music 两个字段都必须写 N/A（完全无声）。'
    if 声音模式 == 'ambient':
        return ('声音控制（强制）：non_diegetic_music 必须写 N/A；'
                'overall_soundscape 只写客观环境音（风、雨、街道、室内底噪等），不写配乐。')
    if 声音模式 == 'custom':
        return '声音控制：按用户需求里写明的声音要求处理；未提及时 non_diegetic_music 写 N/A。'
    return ('声音控制（强制）：non_diegetic_music 必须写 N/A（无画外配乐）；'
            'overall_soundscape 用中文写一段极简环境底噪，不得写情绪化/抽象配乐描述。')


def _兜底替换(文本, 图数):
    """模型输出残留 @引用 时的兜底替换。"""
    import re
    文本 = re.sub(r'@视频(\d+)', r'<Video \1>', 文本)
    文本 = re.sub(r'@音频(\d+)', r'<Audio \1>', 文本)
    文本 = re.sub(r'@图(\d+)', r'<Picture \1>', 文本)
    return 文本
