# -*- coding: utf-8 -*-
"""导演台全能能力：MiniMax H3 导演台全能工作流.json（API 格式）。

设计原则（2026-10-23 重做）：**只改本次任务必须改的字段，其余一律沿用工作流原值。**

工作流里已经跑通过、不能动的配置：
  · 节点 1 底膜（默认 ref2va bf16）
  · 节点 25 的 fl2v_turbo_8step LoRA（strength 1）+ 节点 17 SageAttention 补丁
  · Director 的 steps=8 / sampler=res_multistep / scheduler=simple / cfg=1 /
    shift_video=12 / shift_audio=3
  · timeline 的 editMode=segment、output.continuityEnabled=true / overlap=22 /
    mode=continue、liveTaePreview=true、global.commonEnabled=true、
    以及工作流自带的分段结构（默认 10s + 5s 两段，共 367 帧）

本能力只覆盖这些：
  0. 底膜精度（任务.底膜精度：auto / bf16 / int8）→ 决定 unet_name 具体文件
  1. 底膜（节点 "1" unet_name）：t2v/i2v/fl2v → fl2va，r2v/v2v/rv2v → ref2va
  2. Director 节点 "12"：task_type / width / height / ref_max_size /
     total_frames / global_prompt，以及用户显式给的 cfg / seed / steps / sampler
  3. timeline_data（**就地修补，不重建**）：
       totalFrames / frameRate / width / height / refMaxSize / durationSec
       output.width / height / longEdge / megapixels / aspectRatio / audioMode
       global.taskType / prompt / refs / refVideos / refAudios
       分段的帧数（按原比例分配时长后补 17k+5）与提示词
       fl2v 用 shots[]（首尾帧），并清掉工作流里残留的旧 shots/keyframes
       i2v 写段级 genImage（首帧图），并压成单段
       v2v / rv2v 走 timelineMode=video + editMode=global，源片写 timeline.video

六种模式在插件里的落点（2026-10-23 读源码核对，不是猜的）：
  · t2v / r2v  → timelineMode=prompt_batch，段级提示词；r2v 的素材在 commonEnabled
                 时合并 global，所以只写 global
  · fl2v        → timelineMode=fl2v，读 shots[]（fl2v_timeline.build_fl2v_director_plan）
  · i2v         → prompt_batch + gen_submode=gen_image；editMode=segment 时
                 `_resolve_gen_image_ref` 只读 `段.genImage`，且
                 `_build_gen_source_clips` 对**每一段**都要求有图（缺一段直接抛
                 "Segment #N has no source image"）→ 多段等于每段都从这张图重开，
                 所以本页 i2v 固定单段
  · v2v / rv2v  → timelineMode=video 时 `is_gen_timeline` 返回 False，走
                 plan.build_director_plan 的 video 分支：editMode=global 下
                 `seg_refs = list(global_refs)`，段级素材完全不读，源片来自
                 timeline.video.videoFile，长度取 timeline.totalFrames
                 **两者都不支持参考视频**：task_prompts.py:59 里 rv2v 只有
                 「可选参考图 1–9 与参考音频 1–3」，plan.reference_video_for_segment
                 的注释也写死 "not used by v2v — source clip is the ref" 且只对 r2v 生效。
                 rv2v 的参考素材只走 global.refs / global.refAudios。

关于提示词落在哪：r2v 且 global.commonEnabled=true 时，插件会把
`global.prompt` 与段 prompt 拼接（concat_common_segment_prompt），两边都写会重复，
所以统一「只写 global、段 prompt 留空」，由源码 `local or global` 兜底。
参考素材同理：commonEnabled=true 时 global.refs/refVideos/refAudios 会合并进每段，
写段级会重复，故也统一写 global（commonEnabled=false 时才回落到段级）。
"""
import json
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件, 随机种子
from 能力.导演台工具 import (
    由比例与像素算宽高, 最小帧数, 做参考项, 做首尾镜头, 按类型找节点,
)

工作流文件 = 'MiniMax H3 导演台全能工作流.json'

# 模式 → (Director task_type 官方串, 基座模型族)
# 官方串必须与节点下拉里的一字不差（来源：/object_info/MiniMaxH3Director 的
# task_type options，2026-10-23 实测拉取）。节点共 7 个可选值，mixed 暂未接入本页。
模式配置 = {
    't2v': ('t2v — 文生视频(Text to Video)', 'fl2va'),
    'i2v': ('i2v — 图生视频(Image to Video)', 'fl2va'),
    'fl2v': ('fl2v — 首尾帧生视频(First-Last Frame)', 'fl2va'),
    'r2v': ('r2v — 参考主体生视频(Reference to Video)', 'ref2va'),
    'v2v': ('v2v — 视频转视频(Video to Video)', 'ref2va'),
    'rv2v': ('rv2v — 参考素材改视频(Reference Video Edit)', 'ref2va'),
}

# 走「源视频时间轴编辑」的两个模式：timelineMode=video + editMode=global，
# 源片自动成为 <Video 1>，出片长度跟源片走（totalFrames 超过源帧数会被裁到源帧数）
视频时间线模式 = ('v2v', 'rv2v')

# 报错信息里用的中文名（不要用模式配置里那个带官方串的长标签）
模式中文 = {
    't2v': '文生视频',
    'i2v': '图生视频',
    'fl2v': '首尾帧生视频',
    'r2v': '参考主体生视频',
    'v2v': '视频转视频',
    'rv2v': '参考素材改视频',
}

# 基座模型文件名（2026-10-23 已核实依据）
#   · 配对规则来自 ComfyUI_MiniMaxH3_Director/README.md:42
#     「t2v / i2v / fl2v 用 fl2va UNET；r2v / v2v / rv2v 用 ref2va UNET」
#   · README.md:131-132 官方推荐两个族都用 *_pruned_int8_convrot.safetensors
#   · 本项目已跑通的 5 个单模式工作流（多参考/文生/首尾帧/视频生视频/参考视频）
#     也全部用 int8_convrot
#   · 但 r2v 这里保留工作流原值 bf16：该文件是「全能」工作流实测跑通的配置
#     （2026-10-22 18:04 日志：38445MB 加载、steps=8、367f、refs=3，完整出片），
#     按用户要求「工作流已测试，不能乱改」不动它。
#   · int8 底膜可以正常吃 bf16 LoRA：ComfyUI-MiniMax-H3-PDD-Acc/README.md 明确写
#     "bf16 originals or int8 convrot builds both work — LoRA application goes
#      through ComfyUI's quant-aware patch path"，且本机 comfy_kitchen 后端支持
#      int8_linear / dequantize_int8_convrot_weight / rotate_int8_convrot_weight。
# 底膜文件：族 × 精度。页面给一个「底膜精度」开关，用户自己决定吃显存还是吃画质。
# 4 个文件都真实存在于 ComfyUI 的 UNETLoader 下拉（/object_info 实测，2026-10-23）。
#
# 三档的区别（2026-10-23 新增，别把三档含义混了）：
#   auto —— 保持本项目原有行为，**默认档，没动过任何实测配置**：
#              ref2va → bf16（全能工作流原值，38G）
#              fl2va  → int8 convrot（官方推荐，20G）
#   bf16 —— 两个族都用 bf16：显存最紧、画质上限最高、加载最慢（约 5 分钟/族）
#   int8 —— 两个族都用 int8 convrot：官方推荐，显存约省一半、加载快很多，画质略降
#
# 依据（同上）：
#   · 配对规则 README.md:42「t2v/i2v/fl2v 用 fl2va；r2v/v2v/rv2v 用 ref2va」
#   · README.md:131-132 官方推荐两个族都用 *_pruned_int8_convrot.safetensors
#   · 本项目已跑通的 5 个单模式工作流也全部用 int8_convrot
#   · ref2va 在 auto 档保留 bf16，因为那是「全能」工作流实测跑通的配置
#     （2026-10-22 18:04 日志：38445MB 加载、steps=8、367f、refs=3，完整出片），
#     按用户要求「工作流已测试，不能乱改」不动；int8 那档是**可选**，不是替换。
#   · int8 底膜可以正常吃 bf16 LoRA（PDD-Acc README：LoRA 走 quant-aware patch path）
基座模型文件 = {
    'ref2va': {
        'auto': 'minimax_h3_ref2va_pruned_bf16.safetensors',
        'bf16': 'minimax_h3_ref2va_pruned_bf16.safetensors',
        'int8': 'minimax_h3_ref2va_pruned_int8_convrot.safetensors',
    },
    'fl2va': {
        'auto': 'minimax_h3_fl2va_pruned_int8_convrot.safetensors',
        'bf16': 'minimax_h3_fl2va_pruned_bf16.safetensors',
        'int8': 'minimax_h3_fl2va_pruned_int8_convrot.safetensors',
    },
}

# 精度档位 → (简称, 页面说明)。前端显示用，别在前端再抄一份文件名。
精度说明 = {
    'auto': ('工作流默认', 'ref2va=bf16 / fl2va=int8，与工作流原值一致，没动过任何实测配置'),
    'bf16': ('bf16（38G/族）', '两个族都用 bf16：显存最紧、画质上限最高、加载最慢'),
    'int8': ('int8 convrot（20G/族）', '两个族都用 int8：官方推荐，显存约省一半、加载快很多，画质略降'),
}

# 比例 → 导演台 output.aspectRatio 的完整标签。
# 必须用插件 refine_pack.RESOLUTION_ASPECTS 的中文标签（工作流里存的就是
# "16:9 (宽屏)"），写成英文 "16:9 (Widescreen)" 与工作流不一致。
比例标签 = {
    '1:1': '1:1 (方形)',
    '2:3': '2:3 (竖版照片)',
    '3:2': '3:2 (横版照片)',
    '3:4': '3:4 (竖版标准)',
    '4:3': '4:3 (标准)',
    '9:16': '9:16 (竖屏)',
    '16:9': '16:9 (宽屏)',
    '21:9': '21:9 (超宽)',
}


def _取素材(任务, comfy_url, 前缀, 数量):
    """把任务上的输入图/视频/音频列上传到 ComfyUI，返回文件名列表（顺序即 <Picture N> 编号）。"""
    结果 = []
    for i in range(1, 数量 + 1):
        路径 = getattr(任务, '%s%d' % (前缀, i), '') or ''
        if 路径:
            结果.append(上传到Comfy(comfy_url, str(任务文件(路径))))
    return 结果


def _就近17k5(帧):
    """把帧数就近补到 MiniMax 的 17k+5（不向下超过 22 帧，约 1 秒）。"""
    n = max(5, int(round(float(帧))))
    k = max(1, int(round((n - 5) / 17.0)))
    return 17 * k + 5


def _补帧(分段, 目标秒, 帧率):
    """把目标时长分给各段，返回 (分段, 总帧数)。

    插件里 `durationSec` 才是权威字段：gen_timeline._segment_frame_count 对
    t2v/i2v/r2v/fl2v 只要段上有 durationSec，就用官方公式
    `max(5, round(秒×帧率))` 再补 17k+5 反算帧数，**完全忽略 frameCount**。
    所以这里写的 durationSec 必须与 frameCount 自洽：durationSec = 帧数 / 帧率。

    两个分支：
      · 目标时长 == 各段原时长之和 → 分段完全不动（保持工作流原值：
        15s 就是 10s/5s、243+124、总 367 帧，与测试通过的配置逐字节一致）
      · 否则按目标帧数等比分配，每段就近补 17k+5，避免短时长被撑长
        （按秒分配 5s 会得到 90+56=146 帧/6.08s，按帧分配是 90+39=129 帧/5.38s）
    """
    if not 分段:
        return [], 最小帧数(目标秒, 帧率)

    原时长 = []
    for 段 in 分段:
        try:
            值 = float(段.get('durationSec') or 0)
        except (TypeError, ValueError):
            值 = 0.0
        if 值 <= 0:
            值 = float(段.get('frameCount') or 段.get('length') or 0) / float(帧率)
        原时长.append(值 if 值 > 0 else 1.0)
    总原 = sum(原时长) or float(len(原时长))

    # 分支一：时长没改 → 原样保留（不做任何重算）
    if abs(float(目标秒) - 总原) < 1e-6:
        累计 = 0
        for i, 段 in enumerate(分段):
            帧 = int(段.get('frameCount') or 段.get('length') or 0)
            if 帧 <= 0:
                帧 = 最小帧数(原时长[i], 帧率)
            段['frameCount'] = 帧
            段['length'] = 帧
            段['start'] = 累计
            累计 += 帧
        return 分段, 累计

    # 分支二：按目标帧数等比分配
    目标帧 = 最小帧数(目标秒, 帧率)
    累计 = 0
    for i, 段 in enumerate(分段):
        if i == len(分段) - 1:
            帧 = _就近17k5(目标帧 - 累计)
        else:
            帧 = _就近17k5(目标帧 * 原时长[i] / 总原)
        段['frameCount'] = 帧
        段['length'] = 帧
        段['start'] = 累计
        # 与 frameCount 自洽，插件用官方公式反算能拿回同一帧数
        段['durationSec'] = round(帧 / float(帧率), 4)
        累计 += 帧
    return 分段, 累计


def _兜底分段(时长秒):
    return [{
        'id': 's0', 'start': 0, 'length': 0, 'frameCount': 0, 'durationSec': 时长秒,
        'prompt': '', 'negativePrompt': '', 'taskType': '',
        'refs': [], 'refAudios': [], 'refVideos': [],
        'genImage': {'imageFile': '', 'fileName': ''},
        'startImage': None, 'endImage': None,
        'continuityFromPrev': False, 'refImageSize': 'match',
    }]


def _单段(帧数, 时长秒, 反向提示词=''):
    """整条片只有一段。i2v / v2v / rv2v 用。

    段结构照抄项目里已跑通的 v2v / rv2v 工作流（segments 恰好 1 段，
    length=frameCount=totalFrames），这样插件 `_segment_ranges_from_timeline`
    拿到的区间就是 (0, 总帧数)，不会出现「第二段起止被 totalFrames 夹成 0 帧」
    这种半死不活的状态。
    """
    帧 = int(帧数)
    return [{
        'id': 's0', 'start': 0, 'length': 帧, 'frameCount': 帧,
        'durationSec': float(时长秒),
        'prompt': '', 'negativePrompt': 反向提示词 or '',
        'taskType': '',
        'refs': [], 'refAudios': [], 'refVideos': [],
        'referenceVideo': {'videoFile': '', 'fileName': '', 'type': 'input', 'subfolder': ''},
        'genImage': {'imageFile': '', 'fileName': ''},
        'startImage': None, 'endImage': None,
        'continuityFromPrev': False, 'refImageSize': 'match',
    }]


def 构建导演台全能(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    模式 = (getattr(任务, '模式', '') or 'r2v').strip().lower()
    # 以前这里是 `if 模式 not in 模式配置: 模式 = 'r2v'` 的静默兜底：页面传错值时
    # 会拿 r2v 的底膜 + r2v 的提示词跑出一条**看起来正常但完全不是你要的**片子，
    # 白烧一次 GPU。改成直接报错，错在明面上。
    if 模式 not in 模式配置:
        raise ValueError('导演台全能不支持模式「%s」，可选：%s'
                         % (模式, ' / '.join(模式配置.keys())))
    task_type, 模型族 = 模式配置[模式]

    导演ids = 按类型找节点(api, 'MiniMaxH3Director')
    if not 导演ids:
        raise ValueError('工作流里没有 MiniMaxH3Director 节点。')
    inputs = api[导演ids[0]]['inputs']

    帧率 = int(inputs.get('frame_rate') or 24)

    # ---- 1) 自动切换底膜 ----
    # 两个维度：模式决定**族**（ref2va ↔ fl2va），精度开关决定**文件**
    # （auto=工作流原值 / bf16 / int8）。族由官方配对定，精度由用户在页面上选。
    精度 = (getattr(任务, '底膜精度', '') or 'auto').strip().lower()
    if 精度 not in ('auto', 'bf16', 'int8'):
        精度 = 'auto'
    unet_ids = 按类型找节点(api, 'UNETLoader')
    if unet_ids:
        api[unet_ids[0]]['inputs']['unet_name'] = 基座模型文件[模型族][精度]

    # ---- 2) 素材上传 ----
    参考图, 参考视频, 参考音频 = [], [], []
    首帧 = 尾帧 = None
    首帧图 = None          # i2v：整条片的第 0 帧
    源视频 = None          # v2v / rv2v：被改的那条片
    if 模式 == 'r2v':
        参考图 = _取素材(任务, comfy_url, '输入图', 9)
        参考视频 = _取素材(任务, comfy_url, '输入视频', 3)
        参考音频 = _取素材(任务, comfy_url, '输入音频', 3)
        if not 参考图:
            raise ValueError('参考主体生视频至少要上传 1 张参考图。')
    elif 模式 == 'i2v':
        图 = _取素材(任务, comfy_url, '输入图', 1)
        if not 图:
            raise ValueError('图生视频必须上传 1 张首帧图（输入图1）。')
        首帧图 = 图[0]
    elif 模式 == 'fl2v':
        图 = _取素材(任务, comfy_url, '输入图', 2)
        if not 图:
            raise ValueError('首尾帧生视频至少要上传首帧（输入图1）。')
        首帧 = 图[0]
        尾帧 = 图[1] if len(图) > 1 else None
    elif 模式 in 视频时间线模式:
        # 源视频只能从 输入视频1 取。**rv2v 官方不支持参考视频**：
        # lib/task_prompts.py:59 写的是「源视频时间轴编辑，可选参考图（1–9）与参考音频（1–3）」
        # 只有图片和音频；plan.reference_video_for_segment 的注释也写死
        # "not used by v2v — source clip is the ref"，且只对 r2v 生效。
        # 所以这里不再上传 输入视频2/3 —— 传了也不会被读，只会白占上传时间和显存。
        视频 = _取素材(任务, comfy_url, '输入视频', 1)
        if not 视频:
            raise ValueError('%s必须上传 1 个源视频（输入视频1）。' % 模式中文[模式])
        源视频 = 视频[0]
        if 模式 == 'rv2v':
            参考图 = _取素材(任务, comfy_url, '输入图', 9)
            参考音频 = _取素材(任务, comfy_url, '输入音频', 3)
    # t2v：纯文本，没有任何素材

    # ---- 3) 分辨率：比例 + 一采MP → 32 倍数宽高；算不出来就沿用工作流宽高 ----
    比例 = str(getattr(任务, '比例', '') or '').strip()
    一采MP = getattr(任务, '一采MP', None)
    宽 = 高 = None
    算过 = False
    if 比例 and 一采MP is not None:
        宽, 高 = 由比例与像素算宽高(比例, 一采MP)
        算过 = bool(宽 and 高)
    if not 算过:
        宽 = int(inputs.get('width') or 864)
        高 = int(inputs.get('height') or 480)

    # ---- 4) timeline_data（就地修补） ----
    时间线 = json.loads(inputs.get('timeline_data') or '{}')
    if not 时间线:
        时间线 = {'version': 5, 'editMode': 'segment', 'segments': _兜底分段(5),
                  'shots': [], 'keyframes': [], 'output': {}, 'global': {}}

    时长秒 = getattr(任务, '视频时长', None)
    时长秒 = float(时长秒) if 时长秒 else float(时间线.get('durationSec') or 5)

    提示词 = (getattr(任务, '正向提示词', '') or '').rstrip()
    反向 = getattr(任务, '反向提示词', None)
    # 没有任何「自带信息」的模式必须给提示词，否则白跑一次：t2v 什么都没有；
    # v2v / rv2v 虽然有源片，但「要改成什么样」全靠提示词，空提示词等于原片重绘。
    if 模式 in ('t2v', 'v2v', 'rv2v') and not 提示词:
        raise ValueError('%s必须填写正向提示词。' % 模式中文[模式])

    输出 = 时间线.setdefault('output', {})
    # 导演台组件里「声音」这个下拉只在 v2v / rv2v / r2v 三个模式出现
    # （web/js/minimax_timeline.js:5054-5055 用
    # isVideoEditTaskKey(taskKey) || taskKey === "r2v" 控制显隐），
    # 其余模式根本不给选，所以这里也只在同样的模式里接受网页的开关，
    # 其它模式一律沿用工作流里存的值。
    可改声音 = 模式 in ('r2v', 'v2v', 'rv2v')
    audioMode = str(输出.get('audioMode') or 'generate')
    if 可改声音:
        声音开关 = getattr(任务, '生成声音', None)
        # 组件 mute 分支直接返回 0 采样空音轨
        # （director/audio_export.py:382-383 → empty_audio_dict = torch.zeros(1,1,0)），
        # 进 ComfyUI 原生 CreateVideo→SaveVideo 必然抛
        # av.error.MemoryError [Errno 12]（2026-10-23 task_112 实测：0 采样必崩，
        # 等长静音 455400 采样正常）。所以「关声音」这一档不能用，
        # 关掉时仍然按 generate 提交，不做静音。
        if 声音开关 is not None and not 声音开关:
            audioMode = 'generate'

    全局 = 时间线.setdefault('global', {})
    全局['taskType'] = task_type
    全局['prompt'] = 提示词
    # 素材写 global 的两种情况（其余写段级）：
    #   · r2v + commonEnabled=true → 插件会 merge_indexed_refs(global, 段)
    #   · v2v / rv2v → editMode=global，插件 `seg_refs = list(global_refs)`，段级根本不读
    共享参考 = (模式 == 'r2v' and bool(全局.get('commonEnabled'))) or 模式 in 视频时间线模式

    if 模式 == 'fl2v':
        时间线['timelineMode'] = 'fl2v'
        时间线['segments'] = []
        # 工作流里残留着旧测试的 shots / keyframes（猴子那套），fl2v 会优先读
        # shots[]，必须整段替换，否则会把旧提示词和旧图跑进去。
        时间线['keyframes'] = []
        时间线['shots'] = 做首尾镜头(首帧, 尾帧, 时长秒, 提示词, 反向 or '')
        总帧数 = 最小帧数(时长秒, 帧率)
    elif 模式 in 视频时间线模式:
        # 源视频时间轴编辑：timelineMode=video → is_gen_timeline=False →
        # plan.build_director_plan 的 video 分支。长度只认 timeline.totalFrames
        # （logical_frame_count 先读 totalFrames，再读 video.sourceFrameCount），
        # 段区间由 _segment_ranges_from_timeline 从 segments[].length 切。
        时间线['timelineMode'] = 'video'
        时间线['editMode'] = 'global'
        总帧数 = 最小帧数(时长秒, 帧率)
        时间线['segments'] = _单段(总帧数, 时长秒, 反向 or '')
        # 同样要清掉旧测试残留，video 分支虽然不读 shots，但留着容易误判
        时间线['shots'] = []
        时间线['keyframes'] = []
        视频块 = 时间线.setdefault('video', {})
        视频块['videoFile'] = 源视频
        视频块['fileName'] = 源视频
        视频块['subfolder'] = ''
        视频块['type'] = 'input'
        视频块['sourceFrameCount'] = 总帧数
        # frames / frameMap 是浏览器里存 base64 帧的，有值就会盖过 videoFile
        # （load_timeline_segment 优先走 frames_b64），必须清空
        视频块['frames'] = []
        视频块['frameMap'] = []
        视频块['deletedSourceRanges'] = []
        # 自定义档：源片尺寸由 ffprobe 出来的 storageWidth/Height 决定，这里不写，
        # 让插件 probe 真实帧；输出宽高仍由 output.width/height 决定
    else:
        时间线['timelineMode'] = 'prompt_batch'
        if 模式 == 'i2v':
            # i2v 的图是「第 0 帧」。插件对 gen_image 子模式会为**每一段**都取一次
            # 源图（gen_timeline._build_gen_source_clips 里没有图就直接抛
            # "Segment #N has no source image"），多段就等于每段都从这张图重开，
            # 中间会看到画面跳回起点。所以 i2v 固定单段：一张图 → 一条片。
            总帧数 = 最小帧数(时长秒, 帧率)
            分段 = _单段(总帧数, 时长秒, 反向 or '')
            分段[0]['genImage'] = {'imageFile': 首帧图, 'fileName': ''}
            # 工作流残留的 3 个旧 shot 跟 i2v 无关，清掉免得进度/分段统计把它算进去
            时间线['shots'] = []
            时间线['keyframes'] = []
        else:
            分段 = 时间线.get('segments') or []
            if not 分段:
                分段 = _兜底分段(时长秒)
            分段, 总帧数 = _补帧(分段, 时长秒, 帧率)
        时间线['segments'] = 分段
        for 段 in 分段:
            # 提示词只写 global（commonEnabled 下两边都写会被拼接成两份）
            段['prompt'] = ''
            if 反向 is not None:
                段['negativePrompt'] = 反向
            if 共享参考 or 模式 == 't2v':
                段['refs'] = []
                段['refVideos'] = []
                段['refAudios'] = []

    if 模式 == 'r2v' or 模式 in 视频时间线模式:
        参考 = {
            'refs': 做参考项(参考图, 'imageFile'),
            'refVideos': 做参考项(参考视频, 'videoFile') if 参考视频 else [],
            'refAudios': 做参考项(参考音频, 'audioFile') if 参考音频 else [],
        }
        if 共享参考:
            全局.update(参考)
        else:
            for 段 in 时间线.get('segments') or []:
                段.update(参考)
    else:
        全局['refs'] = []
        全局['refVideos'] = []
        全局['refAudios'] = []

    if 模式 == 'i2v':
        # 工作流里 global.sourceWidth/Height 是上次那张 768×1024 竖图的尺寸，
        # i2v 的源图换了以后这个值会误导插件（_resolve_gen_image_source_dims 先读它）。
        # 置 0 让它回落到输出画布（gen_timeline.py:697 `src_w or out_w`）。
        全局['sourceWidth'] = 0
        全局['sourceHeight'] = 0

    时间线['totalFrames'] = int(总帧数)
    时间线['frameRate'] = 帧率
    时间线['width'] = int(宽)
    时间线['height'] = int(高)
    时间线['refMaxSize'] = max(int(宽), int(高))
    时间线['durationSec'] = float(时长秒)

    输出['width'] = int(宽)
    输出['height'] = int(高)
    输出['longEdge'] = max(int(宽), int(高))
    输出['audioMode'] = audioMode
    if 算过:
        输出['megapixels'] = round(float(一采MP), 4)
        键 = 比例.split(' ')[0]
        if 键 in 比例标签:
            输出['aspectRatio'] = 比例标签[键]

    # ---- 5) 写回 Director 节点 ----
    inputs['task_type'] = task_type
    inputs['timeline_data'] = json.dumps(时间线, ensure_ascii=False)
    inputs['global_prompt'] = 提示词
    inputs['frame_rate'] = 帧率
    inputs['width'] = int(宽)
    inputs['height'] = int(高)
    inputs['ref_max_size'] = max(int(宽), int(高))
    inputs['total_frames'] = int(总帧数)

    # 用户显式给了才覆盖，否则沿用工作流（cfg=1 / seed=666 / steps=8 / res_multistep）
    cfg = getattr(任务, 'cfg', None)
    if cfg not in (None, ''):
        inputs['cfg'] = float(cfg)
    seed = getattr(任务, 'seed', None)
    if seed not in (None, ''):
        inputs['seed'] = int(seed)
    else:
        inputs['seed'] = 随机种子()
    步数 = getattr(任务, '步数', None)
    if 步数 not in (None, ''):
        inputs['steps'] = int(步数)
    采样器 = (getattr(任务, '采样器', '') or '').strip()
    if 采样器:
        inputs['sampler'] = 采样器

    return api
