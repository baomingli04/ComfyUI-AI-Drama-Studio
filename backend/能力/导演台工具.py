# -*- coding: utf-8 -*-
"""导演台工具：MiniMax H3 Director 系列工作流的参数填充。

和旧工作流不一样：旧的是 LoadImage / ResolutionSelector / PrimitiveFloat 多个节点，
这一系列只有一个 MiniMaxH3Director 节点，参数写在它的 inputs 上，另外还挂了一份
嵌套的 timeline_data（JSON 字符串）。节点实际以 timeline_data 为准，只改 inputs
不改 timeline_data 会让页上填的宽高、帧数、提示词全部失效，所以两边必须同步。
"""
import json
import math

from 能力.工作流工具 import 按类型找节点, 随机种子

# 画布必须落在 32 的倍数上（lib/image_prep.py:10 MINIMAX_CANVAS_STRIDE，
# 非 32 倍数会被 assert_minimax_canvas 直接报错）
画布倍数 = 32

# 比例标签键 → (宽比, 高比)。标签可能带中文后缀（'16:9 (宽屏)'），解析时只取冒号前一段
比例数值 = {
    '1:1': (1, 1),
    '2:3': (2, 3),
    '3:2': (3, 2),
    '3:4': (3, 4),
    '4:3': (4, 3),
    '9:16': (9, 16),
    '16:9': (16, 9),
    '21:9': (21, 9),
}


def 找导演节点(api):
    """返回 MiniMaxH3Director 节点 id 列表（按 id 数值升序）。"""
    return 按类型找节点(api, 'MiniMaxH3Director')


def 取时间线(节点):
    return json.loads(节点.get('inputs', {}).get('timeline_data') or '{}')


def 写时间线(节点, 时间线):
    节点.setdefault('inputs', {})['timeline_data'] = json.dumps(时间线, ensure_ascii=False)


def 最小帧数(时长秒, 帧率=24):
    """MiniMax H3 的帧数规则：max(5, round(秒×帧率))，再向上补到 17k+5。

    节点内部 gen_timeline._duration_to_minimax_frames 就是这么算的，
    所以 5 秒 @24fps = 124 帧（124 = 17×7+5），不是 120。
    这里必须和它一致，否则页上填的时长跟实际出片长度对不上。
    """
    帧 = max(5, int(round(float(时长秒) * float(帧率))))
    return 帧 + (5 - 帧 % 17) % 17


def 由比例与像素算宽高(比例, 兆像素):
    """「比例 + 兆像素」→ 32 倍数像素宽高。算不出来返回 (None, None)。

    项目口径是页面给「比例 + 一采MP（0.x）」，而 Director 一采只认像素宽高
    （docs/13 §0.6：Python 完全不读 megapixels / aspectRatio），所以这一步换算
    必须在后端做。公式照搬插件 director/refine_pack.py:231 的
    "Director ResolutionSelector math"，与工作流里存的 864×480 / 480×864 /
    576×736 对得上（都是 0.4MP）。
    """
    if not 比例 or 兆像素 is None:
        return None, None
    键 = str(比例).strip().split(' ')[0]          # '16:9 (宽屏)' → '16:9'
    比值 = 比例数值.get(键)
    if not 比值:
        return None, None
    try:
        mp = float(兆像素)
    except (TypeError, ValueError):
        return None, None
    mp = min(16.0, max(0.1, mp))                  # 与 refine_pack 的 clamp 一致
    宽比, 高比 = float(比值[0]), float(比值[1])
    scale = math.sqrt((mp * 1024 * 1024) / (宽比 * 高比))
    宽 = int(round((宽比 * scale) / 画布倍数) * 画布倍数)
    高 = int(round((高比 * scale) / 画布倍数) * 画布倍数)
    return max(画布倍数, 宽), max(画布倍数, 高)


def _段容器(时间线, 时间线模式=''):
    """本次真正该写的「段」容器——按 timelineMode 过滤，不再无差别遍历。

    以前是 ('segments', 'shots', 'keyframes', 'videoClips') 全遍历，会踩到脏数据：
    D6 / D7 的 timeline 里残留着别人的 shots(4) / keyframes(7)（猴子那套旧提示词），
    遍历会把这些项的 prompt 全部改成用户提示词。prompt_batch 分支当前不读它们所以
    没炸，但一旦工作流改成 fl2v / legacy 就会出乱子（docs/13 附 B 缺陷 2）。

    按源码分支只写该写的那一处：
      · timelineMode=fl2v（D3）→ shots[]
      · 其余（t2v / r2v / prompt_batch / video）→ segments[]
    batchWorkspaces / videoWorkspaces（含 rv2v.globalCommon）是前端 UI 自己用的
    镜像字段，director/plan.py 与 gen_timeline.py 都不读，所以这里不写它们。
    """
    模式 = str(时间线模式 or '').lower()
    键组 = ('shots',) if 模式 == 'fl2v' else ('segments',)
    容器 = []
    for 键 in 键组:
        值 = 时间线.get(键)
        if isinstance(值, list):
            容器.append(值)
    return 容器


def 有外部组(api, 节点序号=0):
    """Director 是否接了 i2v_groups / r2v_groups。

    nodes/director_common.py:233 —— 一旦接了分组，节点走
    build_plan_from_external_groups，timeline_data 的段 / refs 完全不参与，
    只从 Director 标量取 width / height / frame_rate / total_frames。
    """
    ids = 找导演节点(api)
    if 节点序号 >= len(ids):
        return False
    inputs = api[ids[节点序号]].get('inputs') or {}
    return bool(inputs.get('i2v_groups') or inputs.get('r2v_groups'))


def 做参考项(文件名列表, 键名='imageFile'):
    """把上传后的文件名列表转成 timeline_data 里的 refs 结构。

    r2v 的提示词靠 <Picture 1> / <Video 1> / <Audio 1> 引用，编号就是这里的顺序。
    """
    return [{'index': i, 键名: 名, 'fileName': '', 'type': 'input', 'subfolder': ''}
            for i, 名 in enumerate(文件名列表)]


def 取组参数(任务, 组数=4):
    """取外部分组的「每组提示词 + 每组时长」，空则回落。

    回落规则（docs/02 第 9 节）：组提示词空 → 用 正向提示词；组时长空 → 用 视频时长。
    所以不填的组和加列之前行为完全一致。
    """
    公共提示词 = (任务.正向提示词 or '').rstrip()
    公共时长 = float(任务.视频时长) if 任务.视频时长 else None
    结果 = []
    for i in range(1, 组数 + 1):
        提示词 = (getattr(任务, '组%d提示词' % i) or '').rstrip() or 公共提示词
        时长 = getattr(任务, '组%d时长' % i)
        时长 = float(时长) if 时长 else 公共时长
        结果.append((提示词, 时长))
    return 结果


def 做首尾镜头(首帧文件=None, 尾帧文件=None, 时长秒=5, 提示词='', 反向提示词=''):
    """fl2v 用的一「组」：startImage / endImage / durationSec / prompt。

    都不传图就是 fl2va 路径上的文生；只传尾帧官方也允许。
    """
    def 图(名):
        return {'imageFile': 名, 'imageB64': '', 'width': 0, 'height': 0} if 名 else None

    return [{
        'startImage': 图(首帧文件),
        'endImage': 图(尾帧文件),
        'durationSec': float(时长秒),
        'prompt': 提示词,
        'negativePrompt': 反向提示词 or 'bad video',
    }]


def 填导演参数(api, 提示词='', 反向提示词=None, seed=None, cfg=None,
               帧率=None, 宽=None, 高=None, 时长秒=None, 节点序号=0,
               参考图=None, 参考视频=None, 参考音频=None, 镜头=None, 源视频=None,
               兆像素=None, 比例=None):
    """把参数写进 MiniMaxH3Director 节点的 inputs 与 timeline_data。

    画布口径（docs/13 §0.6，2026-09-21 已定）：**页面只收「比例 + 一采MP」，前端
    按公式算出 32 倍数宽高、在页面上直接显示成固定值（只读）**。本函数做的是同一条
    公式的后端那一处实现——因为 Django 直发 /prompt（API 模式没有浏览器，插件 JS
    不执行），Director 一采的 Python 又只认 width/height，所以必须再算一次写进去。
    给了 兆像素 + 比例 就以它们为准（优先），算不出来才回落调用方直接传的 宽/高。

    只覆盖传入的非空项，其余沿用工作流默认值。提示词写 global_prompt 与
    timeline_data.global.prompt；段级 prompt 仅在原值非空时覆盖（说明这个
    工作流是按段组织的）。时长只在单段时改写段的帧数，多段保持原分段不动。
    参考图/视频/音频（已上传到 ComfyUI input 的文件名）写进每个段的 refs。

    timeline_data 的段到底参不参与，由源码分支决定（详见 docs/13）：
      · 接了 i2v_groups / r2v_groups（D8/D9）→ 走 build_plan_from_external_groups，
        段与 refs 全部不读，这里跳过段级写入。
      · timelineMode=video（D4/D5）→ 只认 global.*，段级 refs 不读。
      · prompt_batch（D1/D2/D6/D7）→ 强制 segment，只认段级 refs；
        其中 r2v + commonEnabled（仅 D7）才额外合并 global.refs。
      · fl2v（D3）→ 走 build_fl2v_director_plan，读 shots[]。

    反向提示词的生效范围（源码决定，后端改不了）：
      D1/D2/D6/D7 段 negativePrompt 生效；D3 shots[].negativePrompt 生效；
      D4/D5（video 分支没有 negative 字段）、D8/D9（外部组路径写死默认值）不生效。
    """
    ids = 找导演节点(api)
    if not ids:
        raise ValueError('工作流里没有 MiniMaxH3Director 节点。')
    if 节点序号 >= len(ids):
        raise IndexError('MiniMaxH3Director 只有 %d 个，不够第 %d 个' % (len(ids), 节点序号 + 1))

    节点 = api[ids[节点序号]]
    inputs = 节点.setdefault('inputs', {})

    # 「比例 + 一采MP」优先；换算不出来才用调用方直接给的像素宽高
    if 兆像素 is not None and 比例:
        算宽, 算高 = 由比例与像素算宽高(比例, 兆像素)
        if 算宽 and 算高:
            宽, 高 = 算宽, 算高

    if 提示词:
        inputs['global_prompt'] = 提示词
    if cfg is not None:
        inputs['cfg'] = cfg
    inputs['seed'] = int(seed) if seed is not None else 随机种子()
    if 帧率 is not None:
        inputs['frame_rate'] = int(帧率)
    if 宽 is not None:
        inputs['width'] = int(宽)
    if 高 is not None:
        inputs['height'] = int(高)

    帧率值 = int(帧率) if 帧率 is not None else int(inputs.get('frame_rate') or 24)
    总帧数 = inputs.get('total_frames')
    if 时长秒 is not None and 帧率值:
        # 不能直接用 时长×帧率：MiniMax H3 只认 17k+5 的帧数，节点会再补一次
        总帧数 = 最小帧数(时长秒, 帧率值)
    if 总帧数 is not None:
        inputs['total_frames'] = int(总帧数)
    总帧数 = int(inputs.get('total_frames') or 0)

    # ---- 同步 timeline_data ----
    时间线 = 取时间线(节点)
    if 时间线:
        if 镜头 is not None:
            时间线['shots'] = 镜头
        if 时长秒 is not None:
            时间线['durationSec'] = float(时长秒)
        if 源视频 is not None:
            # v2v / rv2v：源视频文件名（已上传到 ComfyUI input），帧数按本次时长算
            视频块 = 时间线.setdefault('video', {})
            视频块['videoFile'] = 源视频
            视频块['fileName'] = 源视频
            视频块['sourceFrameCount'] = 总帧数
        时间线['totalFrames'] = 总帧数
        时间线['frameRate'] = 帧率值
        if 宽 is not None:
            时间线['width'] = int(宽)
        if 高 is not None:
            时间线['height'] = int(高)

        输出 = 时间线.get('output')
        if isinstance(输出, dict):
            if 宽 is not None:
                输出['width'] = int(宽)
            if 高 is not None:
                输出['height'] = int(高)
            # longEdge 只在 long_edge 模式生效；9 个工作流的 output.mode 都是 fixed，
            # fixed 时写 longEdge 没意义（resolve_output_dimensions 只取 width/height）。
            if str(输出.get('mode') or '').lower() == 'long_edge':
                输出['longEdge'] = max(int(宽 or 输出.get('width') or 0),
                                       int(高 or 输出.get('height') or 0))

        全局 = 时间线.get('global')
        if isinstance(全局, dict) and 提示词:
            全局['prompt'] = 提示词

        # global.refs 到底生不生效，看源码两条规则：
        #   1) timelineMode=video + editMode=global（D4/D5）：plan.py:885 直接
        #      seg_refs = list(global_refs)，段级 refs 根本不参与。
        #   2) gen_timeline.py:531 —— 只有 r2v/r2i 且 commonEnabled 才
        #      merge_indexed_refs(global, local)；prompt_batch 强制 segment 模式，
        #      其余情况只认段级 refs，写 global 是白写。
        是视频时间线 = str(时间线.get('timelineMode') or '').lower() == 'video'
        任务类别 = str((全局 or {}).get('taskType') or inputs.get('task_type') or '')
        是参考任务 = ('r2v' in 任务类别) or ('r2i' in 任务类别)
        写全局参考 = isinstance(全局, dict) and (
            是视频时间线 or (是参考任务 and 全局.get('commonEnabled')))

        # r2v + commonEnabled（9 个工作流里只有 D7）：源码 gen_timeline.py:525 会
        # concat_common_segment_prompt(global, 段)，global 和段都写就会变成
        # 「提示词 + \n\n + 提示词」送进模型（docs/13 附 B 缺陷 1）。
        # 这里改成只写 global、段 prompt 留空：源码 seg_prompt = local_prompt or prompt
        # 会自动兜底用 global，最终文本只有一份。
        段提示词留空 = 是参考任务 and bool((全局 or {}).get('commonEnabled'))
        if 写全局参考:
            if 参考图 is not None and 'refs' in 全局:
                全局['refs'] = 做参考项(参考图, 'imageFile')
            if 参考视频 is not None and 'refVideos' in 全局:
                全局['refVideos'] = 做参考项(参考视频, 'videoFile')
            if 参考音频 is not None and 'refAudios' in 全局:
                全局['refAudios'] = 做参考项(参考音频, 'audioFile')

        生成 = 时间线.get('gen')
        if isinstance(生成, dict):
            生成['defaultFrameCount'] = 总帧数

        # 接了外部分组（D8/D9）时 timeline 的段整体不参与，写了也是白写，
        # 而且会污染工作流自带的段数据，所以直接跳过。
        外部组 = 有外部组(api, 节点序号)
        if 外部组:
            写时间线(节点, 时间线)
            return api

        段组 = _段容器(时间线, 时间线.get('timelineMode'))
        主段 = 时间线.get('segments')
        # 只有主 segments 恰好一段时，才改它的帧数；多段工作流的分段结构保持不动
        单段 = isinstance(主段, list) and len(主段) == 1
        for 段列表 in 段组:
            for 段 in 段列表:
                if not isinstance(段, dict):
                    continue
                # v2v / rv2v 的段 prompt 原本是空的，单段时直接用页上填的提示词
                if 提示词 and (单段 or 段.get('prompt')):
                    # D7（r2v + commonEnabled）只写 global，段留空让源码兜底
                    段['prompt'] = '' if 段提示词留空 else 提示词
                # D4 / D5 的 video 分支根本没有 negative 字段，段里虽有这个键也
                # 不会被读（docs/13 附 A），写了是无效写入，这里直接跳过。
                if 反向提示词 is not None and 'negativePrompt' in 段 and not 是视频时间线:
                    段['negativePrompt'] = 反向提示词
                # video 模式（D4/D5）下段级 refs 根本不读（plan.py 用 global_refs），
                # 写了也是白写；其余模式段级 refs 才是唯一入口。
                if not 是视频时间线:
                    if 参考图 is not None and 'refs' in 段:
                        段['refs'] = 做参考项(参考图, 'imageFile')
                    if 参考视频 is not None and 'refVideos' in 段:
                        段['refVideos'] = 做参考项(参考视频, 'videoFile')
                    if 参考音频 is not None and 'refAudios' in 段:
                        段['refAudios'] = 做参考项(参考音频, 'audioFile')
                if 单段 and 总帧数:
                    段['frameCount'] = 总帧数
                    段['length'] = 总帧数
                    if 时长秒 is not None:
                        段['durationSec'] = float(时长秒)

        写时间线(节点, 时间线)

    return api
