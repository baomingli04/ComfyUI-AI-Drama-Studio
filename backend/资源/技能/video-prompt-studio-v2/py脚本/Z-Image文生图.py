#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Z-Image文生图.py — 调用「纯文生图_Z-Image」工作流出**独立背景/环境图**。

【用途】
  - 出单独的背景图/环境图（技能此前无 txt2img，D8 缺口，由本工作流补上）。
  - Ref2VA 段想保环境一致时：先用本脚本从 ① 世界书文字出背景图，
    再作为 Ref2VA 的环境参考图（`--images` 里的 Picture，写在六段式里当场景锚点）。

【传参说明】
  --prompt TEXT     正向提示词（必填）。描述目标背景/环境（场景、时间、光线、画风）。
  --negative TEXT   负向提示词（可选，不传则保留工作流内置的"反动漫/反卡通"负向）。
  --width/--height  出图边长（可选，覆盖 81 号尺寸节点的 width_override/height_override；
                    不传则沿用工作流默认尺寸（不强制 1024x512））。
  --seed N          随机种子（可选，默认随机）。
  --output-prefix   保存前缀（默认 z-image），落盘 ComfyUI output/。
  --copy-to DIR     可选。生成后把 PNG 拷到指定目录（如 ③ dirs.image_edit 或背景图目录），
                    便于后续 Ref2VA多参考视频 --images 直接引用。
  --comfy-url       ComfyUI 地址（默认 http://127.0.0.1:8188）。
  --timeout         等待秒数（默认 600）。

【底层机制（脚本已封装，了解即可）】
  - 正向 → 节点标题「【正向提示词】在这里输入」(67 CLIPTextEncode)；**原样透传用户 --prompt（用户规则 2026-08-27：不再追加任何提示词）**
  - 负向 → 节点标题「【反向提示词】在这里输入」(64 CLIPTextEncode)，仅透传用户 `--negative`，无则保留工作流内置负向
  - 尺寸 → SDXLEmptyLatentSizePicker+(81) 的 width_override/height_override
  - 采样 → KSampler(69) 固定 steps=25/cfg=4/euler/simple（模型规范，不改）
  - LoRA → 工作流自带 LoraLoaderModelOnly(80)，脚本不触碰（保持工作流默认）
  - ⚠️ 亮度/曝光相关注入已**全部弃用**（2026-08-13 用户实测）：
      - `BACKGROUND_LIGHT` 正向强光词会拉爆曝光；
      - `BACKGROUND_NEGATIVE` 负向"禁止昏暗/阴影/欠曝"同样会迫使模型提亮，导致高光过曝；
    光线语义完全靠用户 prompt 自然表达；**脚本不追加任何提示词（用户规则 2026-08-27：禁止后端组合）。**

示例：
  # 出 9:16 竖版森林湖泊背景，拷到背景图目录
  python Z-Image文生图.py \
      --prompt "森林环绕的天然湖泊，午后明亮柔和的自然光透过树冠洒在湖面，落叶草地，电影感，8K摄影" \
      --width 512 --height 896 --copy-to output/images/backgrounds
"""
import argparse
import glob
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Comfy客户端 as cc

WF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "工作流")
WF_FILE = "纯文生图_Z-Image.json"


def main():
    ap = argparse.ArgumentParser(description="Z-Image 纯文生图（背景/环境图）")
    ap.add_argument("--prompt", required=True, help="正向提示词（必填）")
    ap.add_argument("--negative", default=None, help="负向提示词（可选）")
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output-prefix", default="z-image")
    ap.add_argument("--copy-to", default=None, help="生成后把 PNG 拷到该目录")
    ap.add_argument("--comfy-url", default=cc.DEFAULT_URL)
    ap.add_argument("--comfy-output", default=None, help="ComfyUI output 根（默认探测 D:/ComfyUI-aki-v3/ComfyUI/output 等）")
    ap.add_argument("--timeout", type=int, default=None,
                    help="等待秒数（默认 None = 无限等待，由 Comfy客户端.wait 保证）")
    args = ap.parse_args()

    wf_path = os.path.join(WF_DIR, WF_FILE)
    if not os.path.isfile(wf_path):
        print(f"[error] 技能工作流缺失: {wf_path}"); sys.exit(1)
    api = cc.load_workflow(wf_path)

    # 正向提示词：原样透传用户 --prompt（用户规则 2026-08-27：禁止后端 py 组合任何提示词）
    positive = (args.prompt or "").rstrip()
    if not cc.set_text(api, "【正向提示词】在这里输入", positive):
        print("[warn] 未找到正向提示词节点（title=【正向提示词】在这里输入）")
    # 负向提示词：仅透传用户 --negative，不再注入 BACKGROUND_NEGATIVE。
    # 实测 BACKGROUND_NEGATIVE（"禁止昏暗/阴影/欠曝"）会迫使模型提亮，导致高光过曝（2026-08-13）。
    negative = (args.negative or "").rstrip()
    if not cc.set_text(api, "【反向提示词】在这里输入", negative):
        print("[warn] 未找到反向提示词节点（title=【反向提示词】在这里输入）")
    # 尺寸覆盖（81 号节点 SDXLEmptyLatentSizePicker+；D9 修复）
    # 关键 bug：resolution 是 combo 标签，width_override/height_override 必须与 resolution 的比例匹配才生效，
    # 否则节点以 combo 默认（1728x576 横长）出图，与 override 像素画幅错位 → SaveImage 输出画布被拉伸/留白（用户感知为"曝光大"）。
    # 合法 resolution 仅支持预设（704x1408~1728x576），无 512x896；脚本按目标比例选最接近预设 + 同步 override。
    if args.width or args.height:
        nid = cc.find_nodes(api, class_type="SDXLEmptyLatentSizePicker+")
        if nid:
            n = api[nid[0]]["inputs"]
            # 目标像素（默认 9:16 竖版 512x896；用户可传）
            target_w = args.width or 512
            target_h = args.height or 896
            # 合法 resolution 预设（来自 /object_info，D9 实测）
            # 优先按比例匹配；无精确匹配时选比例最接近的合法预设
            candidates = [
                "704x1408 (0.5)", "704x1344 (0.52)", "768x1344 (0.57)", "768x1280 (0.6)",
                "832x1216 (0.68)", "832x1152 (0.72)", "896x1152 (0.78)", "896x1088 (0.82)",
                "960x1088 (0.88)", "960x1024 (0.94)", "1024x1024 (1.0)", "1024x960 (1.07)",
                "1088x960 (1.13)", "1088x896 (1.21)", "1152x896 (1.29)", "1152x832 (1.38)",
                "1216x832 (1.46)", "1280x768 (1.67)", "1344x768 (1.75)", "1344x704 (1.91)",
                "1408x704 (2.0)", "1472x704 (2.09)", "1536x640 (2.4)", "1600x640 (2.5)",
                "1664x576 (2.89)", "1728x576 (3.0)",
            ]
            target_ratio = target_w / max(target_h, 1)
            best = min(candidates, key=lambda s: abs(float(s.split("(")[1].rstrip(")")) - target_ratio))
            n["resolution"] = best
            n["width_override"] = target_w
            n["height_override"] = target_h
        else:
            print("[warn] 未找到尺寸节点 SDXLEmptyLatentSizePicker+")
    # 种子
    if args.seed is not None:
        for nid in cc.find_nodes(api, class_type="KSampler"):
            api[nid]["inputs"]["seed"] = args.seed
    # 保存前缀
    cc.set_param(api, "SaveImage", "filename_prefix", args.output_prefix)

    print(f"[run] Z-Image 文生图 {args.width or '默认宽'}x{args.height or '默认高'} seed={args.seed or '随机'} -> {args.output_prefix}")
    out = cc.run(api, url=args.comfy_url, timeout=args.timeout)
    # 打印 + 可选拷出
    saved = []
    for nid, kinds in out.items():
        print(f"  节点{nid}: {kinds}")
        imgs = kinds.get("images", []) if isinstance(kinds, dict) else []
        saved.extend(imgs)
    if args.copy_to and saved:
        os.makedirs(args.copy_to, exist_ok=True)
        for fn in saved:
            # SaveImage 落盘在 ComfyUI output/<prefix>_xxxxx_.png，从 ComfyUI 输出根找
            # 通过 /history 拿不到全路径时，从常见根目录探测
            roots = []
            if args.comfy_output:
                roots.append(args.comfy_output)
            roots += [r"D:/ComfyUI-aki-v3/ComfyUI/output", r"D:/ComfyUI/output"]
            copied = None
            for r in roots:
                hit = glob.glob(os.path.join(r, "**", fn), recursive=True)
                if hit:
                    shutil.copy(hit[0], os.path.join(args.copy_to, fn))
                    copied = hit[0]
                    break
            print(f"  拷贝 {fn} -> {args.copy_to}" + (f"（来自 {copied}）" if copied else "（未找到源文件）"))


if __name__ == "__main__":
    main()
