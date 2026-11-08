#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ref2VA多参考视频.py — 调用「H3-全能参考生视频（图9视频3音频3）优化版」(Ref2VA)。

【柔性装填（核心）】
  参考数量完全由本次传入决定，工作流文件一个字不改，prompt 在内存里按实际数量拼：
    --images  N 张 (1~9)：只保留 ref_image_0..N-1 共 N 个图片槽，
                          其余 (9-N) 个 LoadImage 节点整段从 prompt 摘除并断开主节点连线。
    --videos  K 个 (0~3)：保留前 K 个视频槽，其余摘除。
    --audios  M 个 (0~3)：保留前 M 个音频槽，其余摘除。
  没传的音频/视频节点直接不进 prompt → 不触发空路径校验 → 零消耗、不报错。
  传 1 张图就只接 1 个图槽；传 4 张就接 4 个；传满 9+3+3 则与原始工作流等价。

【传参说明】
  --images IMG1..IMGN   必填，1~9 张参考图（顺序=ref_image_0..N-1）。
                        约定：图片按顺序 = 角色参考图在前、背景图在最后（与 分镜规则.md §3 Ref2VA 六段式一致：图片1=主角A参考、图片2=主角B参考、图片3=背景…）；背景必须在末尾，防串脸。
                        工作流不会自动识别首尾帧——须靠 --prompt 六段式显式绑定
                        （<Picture 1> is the first frame... / <Subject N> 其外貌来自 <Picture 3>）。
  --videos V1..VK      可选，0~3 个参考视频（带声，取其音轨）。不传则不接。
  --audios A1..AM      可选，0~3 个参考音频。不传则不接。
  --prompt TEXT         必填。六段式提示词（subject_definitions / summary / retention_analysis /
                        detailed_description / overall_soundscape / non_diegetic_music）。
  --preset {opt,v5}     参数预设（默认 opt）：opt=0.3MP/11s，v5=0.4MP/5s。也可用下方细参覆盖。
  --megapixels MP       分辨率（覆盖预设，默认随 preset）。
  --duration FLOAT      时长（覆盖预设，默认随 preset；受模型 15s 上限）。
  --aspect RATIO        比例（默认 9:16）。
  --seed INT            随机种子。不传=每次随机（0.1/0.2 抽卡，脚本打印本次 seed 并回写文档顶部 视频抽卡种子）；
                        传=固定复用（0.3-0.9 成品复用 0.1/0.2 抽卡成功那个 seed，内容一致只提清晰度）。
  --output-prefix       视频保存前缀（默认 video/MiniMax_H3）。
                        ⭐ 防互顶：若 ComfyUI 输出目录已有同前缀成片，自动追加 _2/_3…
                        序号，绝不覆盖上次 0.1 抽卡的片。
  --comfy-url           ComfyUI 地址（默认 http://127.0.0.1:8188）。
  --timeout             等待秒数（默认 None = 无限等待，由 Comfy客户端.wait 保证）。

【底层机制（脚本已封装）】
  - 主节点 MiniMaxH3ReferenceToVideo 的各 ref_* 连线在运行时按实际数量裁剪。
  - 本地图/视频/音频先上传到 ComfyUI（Load* 节点只认内部文件名，外部绝对路径会 400），
    再写回返回的文件名；已是 ComfyUI 内部文件名则原样写入。
  - PrimitiveStringMultiline 节点 = 六段式提示词（API 用 value 字段）。
  - ResolutionSelector 覆盖 aspect/megapixels；PrimitiveFloat 覆盖时长。
  - SaveVideo 覆盖前缀。
  - ⚠️ 提示词一律中文（用户规则 2026-08-13）；不再自动追加 BEAUTY_CLAUSE（已弃用），
    六段式正文（含亮度/美颜语义）由 storyboard 提示词直接提供。

示例：
  # 只传 1 张图，4 秒，无音频无视频
  python Ref2VA多参考视频.py --images naruto.png --prompt "$(cat shot.txt)" \
      --duration 4 --megapixels 0.5 --aspect 9:16 --output-prefix video/MiniMax_H3_Naruto_4s

  # 传 9 图 + 3 视频 + 3 音频（等价原始工作流）
  python Ref2VA多参考视频.py --images f1..f9 --videos v1 v2 v3 --audios a1 a2 a3 \
      --prompt "$(cat shot.txt)" --preset opt
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Comfy客户端 as cc
import 项目路径 as pp  # 定位成片绝对路径 + 配置目录落盘

WF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "工作流")
WF_FILE = "H3-全能参考生视频（图9视频3音频3）优化版.json"

PRESETS = {
    "opt": {"megapixels": 0.3, "duration": 11},
    "v5":  {"megapixels": 0.4, "duration": 5},
}

# ResolutionSelector 节点的 aspect_ratio 只认完整标签，短写需映射
ASPECT_MAP = {
    "1:1": "1:1 (Square)",
    "2:3": "2:3 (Portrait Photo)",
    "3:2": "3:2 (Photo)",
    "3:4": "3:4 (Portrait Standard)",
    "4:3": "4:3 (Standard)",
    "9:16": "9:16 (Portrait Widescreen)",
    "16:9": "16:9 (Widescreen)",
    "21:9": "21:9 (Ultrawide)",
}

MAX_IMAGES = 9
MAX_VIDEOS = 3
MAX_AUDIOS = 3


def _main_id(api):
    ids = cc.find_nodes(api, class_type="MiniMaxH3ReferenceToVideo")
    if not ids:
        raise RuntimeError("工作流里找不到 MiniMaxH3ReferenceToVideo 主节点")
    return ids[0]


def _src_of(api, main_id, key):
    """返回主节点某输入连线指向的源节点 id（无则 None）。"""
    v = api[main_id]["inputs"].get(key)
    return v[0] if isinstance(v, list) else None


def _drop_input(api, main_id, key):
    api[main_id]["inputs"].pop(key, None)


def _drop_node(api, nid):
    api.pop(str(nid), None)


def _resolve(path_or_name, url):
    """本地文件→上传并返回内部文件名；已是内部名则原样返回。"""
    if os.path.isfile(path_or_name):
        return cc.upload_image(url, path_or_name)
    return path_or_name


def _require_local(path, label):
    """本地素材路径必须真实存在，否则立刻给出清晰报错后退出。

    典型坑：.bat 用 CMD 默认代码页(GBK)保存/运行时，中文路径会被糟蹋成乱码，
    此时 os.path.isfile 判 False，若静默把乱码全路径写进节点只会得到诡异的 400。
    这里先拦下来，明确告诉用户是「路径找不到/被代码页糟蹋」，而不是「绝对路径不支持」。
    """
    if not os.path.isfile(path):
        print(f"[error] 找不到{label}（很可能是 .bat 中文路径被 CMD 代码页糟蹋，"
              f"或路径拼错）：\n        {path}")
        print("        修复：.bat 顶部加 `chcp 65001 >nul` 与 `set PYTHONUTF8=1`，"
              f"且 .bat 文件保存为 UTF-8 编码。")
        sys.exit(1)


def _unique_prefix(prefix, comfy_output):
    """防互顶：若 ComfyUI 输出目录已有同前缀成片，自动追加 _2/_3… 序号。

    目的：0.1 抽卡可能反复跑，成片必须保留不覆盖；0.4 成品用独立前缀再叠加。
    SaveVideo 的 prefix 相对 ComfyUI output 目录（如 video/xxx → output/video/xxx）。
    comfy_output: ComfyUI output 目录绝对路径（--comfy-output 传入）；None 则不防互顶。
    """
    if not comfy_output or not os.path.isdir(comfy_output):
        return prefix
    try:
        rel_dir, base = os.path.split(prefix)
        check_dir = os.path.join(comfy_output, rel_dir) if rel_dir else comfy_output
        if not os.path.isdir(check_dir):
            return prefix
        exists = [f for f in os.listdir(check_dir)
                  if f.startswith(base) and f.endswith((".mp4", ".webm", ".gif", ".png"))]
        if not exists:
            return prefix
        n = 2
        while any(f.startswith(f"{base}_{n}") for f in os.listdir(check_dir)):
            n += 1
        return f"{prefix}_{n}"
    except Exception:
        # 查不到就按原前缀走，宁可同名也不阻断出片
        return prefix


def main():
    ap = argparse.ArgumentParser(description="Ref2VA 多参考生视频调用（柔性装填）")
    ap.add_argument("--images", nargs="+", required=True,
                    help=f"{MAX_IMAGES} 张以内参考图，顺序=ref_image_0..N-1")
    ap.add_argument("--videos", nargs="*", default=[], help=f"最多 {MAX_VIDEOS} 个参考视频")
    ap.add_argument("--audios", nargs="*", default=[], help=f"最多 {MAX_AUDIOS} 个参考音频")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--preset", choices=list(PRESETS), default="opt")
    ap.add_argument("--megapixels", type=float, default=None)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--seed", type=int, default=None,
                    help="固定随机种子。不传=每次随机（0.1/0.2 抽卡，脚本会打印本次 seed 并回写文档顶部 视频抽卡种子）；传=固定复用（0.3-0.9 成品复用 0.1/0.2 抽卡成功的那个 seed，内容一致只提清晰度）")
    ap.add_argument("--config", default=None, help="工作配置.yaml（用于自动定位 提示词生成.md 回写 seed；无 --storyboard 时启用）")
    ap.add_argument("--storyboard", default=None, help="提示词生成.md 路径（顶部 视频抽卡种子 回写用；优先于 --config）")
    ap.add_argument("--output-prefix", default="video/MiniMax_H3")
    ap.add_argument("--comfy-output", default=None,
                    help="ComfyUI output 目录绝对路径（防互顶用；不传则不防互顶）")
    ap.add_argument("--comfy-url", default=cc.DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=None)
    args = ap.parse_args()

    n_img, n_vid, n_aud = len(args.images), len(args.videos), len(args.audios)
    if not (1 <= n_img <= MAX_IMAGES):
        print(f"[error] --images 需 1~{MAX_IMAGES} 张，收到 {n_img}"); sys.exit(1)
    if n_vid > MAX_VIDEOS:
        print(f"[error] --videos 最多 {MAX_VIDEOS} 个，收到 {n_vid}"); sys.exit(1)
    if n_aud > MAX_AUDIOS:
        print(f"[error] --audios 最多 {MAX_AUDIOS} 个，收到 {n_aud}"); sys.exit(1)

    mp = args.megapixels if args.megapixels is not None else PRESETS[args.preset]["megapixels"]
    dur = args.duration if args.duration is not None else PRESETS[args.preset]["duration"]

    if mp >= 0.3 and args.seed is None:
        print(f"  [警告] mp={mp} ≥ 0.3 但未传 --seed：独立调用会违反 seed 铁律（成品档须复用顶部 视频抽卡种子）；"
              f"建议由 生成视频.py 统一传入 --seed。")

    wf_path = os.path.join(WF_DIR, WF_FILE)
    api = cc.load_workflow(wf_path)
    main = _main_id(api)

    # ---- 本地素材存在性预检（中文路径被 CMD 代码页糟蹋时会早报错）----
    for p in args.images:
        _require_local(p, "参考图")
    for p in args.videos:
        _require_local(p, "参考视频")
    for p in args.audios:
        _require_local(p, "参考音频")

    # ---- 图片：保留前 N 个，摘除其余 ----
    provided_imgs = [_resolve(p, args.comfy_url) for p in args.images]
    for j in range(MAX_IMAGES):
        nid = _src_of(api, main, f"ref_images.ref_image_{j}")
        if nid is None:
            continue
        if j < n_img:
            api[nid]["inputs"]["image"] = provided_imgs[j]
        else:
            _drop_input(api, main, f"ref_images.ref_image_{j}")
            _drop_node(api, nid)

    # ---- 视频：保留前 K 个，摘除其余（含其音轨连线）----
    provided_vids = [_resolve(p, args.comfy_url) for p in args.videos]
    for j in range(MAX_VIDEOS):
        nid = _src_of(api, main, f"ref_videos.ref_video_{j}")
        if nid is None:
            continue
        if j < n_vid:
            api[nid]["inputs"]["video"] = provided_vids[j]
        else:
            _drop_input(api, main, f"ref_videos.ref_video_{j}")
            _drop_input(api, main, f"ref_video_audios.ref_video_audio_{j}")
            _drop_node(api, nid)

    # ---- 音频：保留前 M 个，摘除其余 ----
    provided_auds = [_resolve(p, args.comfy_url) for p in args.audios]
    for j in range(MAX_AUDIOS):
        nid = _src_of(api, main, f"ref_audios.ref_audio_{j}")
        if nid is None:
            continue
        if j < n_aud:
            api[nid]["inputs"]["audio"] = provided_auds[j]
        else:
            _drop_input(api, main, f"ref_audios.ref_audio_{j}")
            _drop_node(api, nid)

    # ---- 六段式提示词（原样透传，不再注入 BEAUTY_CLAUSE，用户 2026-08-13 弃用；提示词一律中文）----
    prompt = (args.prompt or "").rstrip()
    cc.set_text(api, "Input Text (Prompt)", prompt)

    # ---- 分辨率 / 时长 ----
    aspect = ASPECT_MAP.get(args.aspect, args.aspect)
    cc.set_resolution(api, aspect, mp)
    for nid in cc.find_nodes(api, class_type="PrimitiveFloat"):
        api[nid]["inputs"]["value"] = dur

    # ---- seed：不传=随机（抽卡，打印本次 seed 并回写文档顶部），传=固定复用（成品）----
    seed = args.seed
    hits = cc.find_nodes(api, class_type="RandomNoise")
    if hits:
        if seed is None:
            seed = random.randint(0, 2**63 - 1)
            for nid in hits:
                api[nid]["inputs"]["noise_seed"] = seed
            print(f"  SEED: {seed}")
            print(f"    （0.1/0.2 抽卡：此值已回写 提示词生成.md 顶部 视频抽卡种子；0.3-0.9 成品跑 --seed {seed} 复用同一内容）")
            sb = args.storyboard or pp.resolve_storyboard(args.config)
            if sb:
                pp.write_back_top_field(sb, "视频抽卡种子", seed)
                print(f"  ✅ 已回写 视频抽卡种子={seed} -> {sb}")
            else:
                print(f"  ⚠️ 未指定 --storyboard/--config，未回写 seed（请手动记录 {seed}）")
        else:
            for nid in hits:
                api[nid]["inputs"]["noise_seed"] = seed
            print(f"  固定 seed={seed} -> 节点{hits}(RandomNoise)")

    # ---- 输出：防互顶（同前缀已有成片时自动追加 _2/_3… 序号）----
    prefix = _unique_prefix(args.output_prefix, args.comfy_output)
    if prefix != args.output_prefix:
        print(f"  输出防互顶：前缀 {args.output_prefix} 已有产出，自动改用 {prefix}")

    # ---- 输出 ----
    cc.set_param(api, "SaveVideo", "filename_prefix", prefix)

    print(f"[run] Ref2VA 图片={n_img} 视频={n_vid} 音频={n_aud} | "
          f"{dur}s {mp}MP {args.aspect} -> {args.output_prefix}")
    out = cc.run(api, url=args.comfy_url, timeout=args.timeout)
    for nid, kinds in out.items():
        print(f"  节点{nid}: {kinds}")

    # 报告最终成片绝对路径（供 ⑧ 执行器拷贝到配置目录 video_raw + 回写 storyboard）
    final = pp.locate_video(prefix, args.comfy_output)
    if final:
        print(f"FINAL_VIDEO: {final}")
    else:
        print(f"[warn] 未定位到成片（检查 --comfy-output 是否指向 ComfyUI 实际 output 根）")


if __name__ == "__main__":
    main()
