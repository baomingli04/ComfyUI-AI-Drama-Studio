#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FL2VA首尾帧视频.py — 调用「（批量首尾帧）海螺生视频」(FL2VA 批量首尾帧) 工作流。

【传参说明】
  --first-dir DIR   必填。首帧目录：按段顺序命名（001.png,002.png...），第 i 张 = 第 i 段首帧。
  --last-dir DIR    可选。尾帧目录：第 i 张 = 第 i 段尾帧（数量必须与首帧目录一致）。
                    ⚠️ 正确工作流是「每段独立首/尾帧成对」（easy loadImagesForLoop 按对加载），
                    不是旧「（批量）漫剧海螺生视频4步」的共享序列（N+1 张、段N尾=段N+1首）。
                    【首帧-only 模式】不传 --last-dir 时，脚本自动把首帧复制为尾帧喂给工作流——
                    即唯一源图就是首帧，视频仅由首帧驱动（功能 5 默认只出首帧时的标准用法）。
  --prompts-file FILE 必填。每段 FL2VA 提示词，每行一段，行序 = 段序（第 i 行配 首帧第 i 张→尾帧第 i 张）。
  --count N          段数（可选）。不填则自动 = 首帧目录图片数。
  --aspect RATIO     比例（默认 9:16）。
  --megapixels MP    分辨率（**非权威兜底**=0.1；实际 mp 必须来自 提示词生成.md 的 视频时长 字段，由 ⑧ 显式传 --megapixels 覆盖；节点内置默认须被覆盖；定稿上调 0.3/0.4）。
  --duration FLOAT   每段时长（可选）。不填则保留工作流默认分支（无对白5s/有对白8s）。
  --output-prefix    视频保存前缀（默认 video/MiniMax_H3，写 VHS_VideoCombine.filename_prefix）。
  --comfy-url        ComfyUI 地址（默认 http://127.0.0.1:8188）。
  --timeout          等待秒数（默认 None = 无限等待，由 Comfy客户端.wait 保证）。

【底层机制（脚本已封装）】
  - 首帧目录写入 PrimitiveString「首帧」(134)、尾帧目录写入 PrimitiveString「尾帧」(135)；
    easy loadImagesForLoop(139/136) 按循环 index 各取第 i 张成对（首 i → 尾 i）。
  - 提示词：Text Load Line From File(140).file_path 按行取（行 i = 段 i）+ Text Multiline(146) 兜底。
  - ⚠️ 提示词一律中文（用户规则 2026-08-13）；不再自动追加 BEAUTY_CLAUSE（已弃用），
    视频提示词正文（含亮度/美颜语义）由 storyboard 提示词直接提供。
  - For循环-开始(138).total = 段数。
  - ResolutionSelector(132) 覆盖 aspect/megapixels（D16：set_resolution 内置裸比例→combo 完整标签映射）。
  - 保存：VHS_VideoCombine(208).filename_prefix（正确工作流无 SaveVideo 节点，D15 修复后已弃旧版）。
  - 视频时长受模型 15s 上限约束（模型限制，非显存）。

示例：
  python FL2VA首尾帧视频.py --first-dir output/frames/fl2va_first --last-dir output/frames/fl2va_last \
      --prompts-file prompts.txt --aspect 9:16 --megapixels 0.1 --output-prefix video/MiniMax_H3_FL2VA
"""
import argparse
import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Comfy客户端 as cc
import 项目路径 as pp  # 定位成片绝对路径 + 配置目录落盘

WF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "工作流")
WF_FILE = "（批量首尾帧）海螺生视频.json"

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


def count_images(folder):
    return len([f for f in os.listdir(folder) if f.lower().endswith(IMG_EXT)])


def _unique_prefix(prefix, comfy_output):
    """防互顶：若 ComfyUI 输出目录已有同前缀成片，自动追加 _2/_3… 序号。

    目的：0.1 抽卡可能反复跑，成片必须保留不覆盖；成品档用独立前缀再叠加。
    SaveVideo/VHS 的 prefix 相对 ComfyUI output 目录（如 video/xxx → output/video/xxx）。
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
    ap = argparse.ArgumentParser(description="FL2VA 批量首尾帧生视频调用")
    ap.add_argument("--first-dir", required=True, help="首帧目录（第 i 张 = 第 i 段首帧）")
    ap.add_argument("--last-dir", default=None,
                    help="尾帧目录（可选）。不传 → 首帧-only：自动把首帧复制为尾帧喂工作流")
    ap.add_argument("--prompts-file", required=True)
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--megapixels", type=float, default=0.1)  # 兜底值，非权威；⑧ 必须显式传（取自 提示词生成.md 的 视频时长）
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--output-prefix", default="video/MiniMax_H3")
    ap.add_argument("--seed", type=int, default=None,
                    help="随机种子。不传=每次随机（0.1/0.2 抽卡，脚本打印本次 seed 并回写文档顶部 视频抽卡种子）；传=固定复用（0.3-0.9 成品档复用 0.1/0.2 抽卡成功那个 seed）")
    ap.add_argument("--config", default=None, help="工作配置.yaml（用于自动定位 提示词生成.md 回写 seed；无 --storyboard 时启用）")
    ap.add_argument("--storyboard", default=None, help="提示词生成.md 路径（顶部 视频抽卡种子 回写用；优先于 --config）")
    ap.add_argument("--comfy-output", default=None,
                    help="ComfyUI output 目录绝对路径（防互顶用；不传则不防互顶）")
    ap.add_argument("--comfy-url", default=cc.DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=None)
    args = ap.parse_args()

    first_dir = os.path.abspath(args.first_dir)
    if not os.path.isdir(first_dir):
        print(f"[error] 首帧目录不存在: {first_dir}"); sys.exit(1)
    if not os.path.isfile(args.prompts_file):
        print(f"[error] 提示词文件不存在: {args.prompts_file}"); sys.exit(1)

    if args.last_dir:
        last_dir = os.path.abspath(args.last_dir)
        if not os.path.isdir(last_dir):
            print(f"[error] 尾帧目录不存在: {last_dir}"); sys.exit(1)
        n_first, n_last = count_images(first_dir), count_images(last_dir)
        if n_first != n_last:
            print(f"[error] 首帧({n_first}) 与尾帧({n_last}) 数量不一致"); sys.exit(1)
    else:
        # 首帧-only 模式：未提供尾帧 → 复用首帧作为尾帧（唯一源图即首帧）
        last_dir = os.path.join(os.path.dirname(first_dir), "_fl2va_last_derived")
        os.makedirs(last_dir, exist_ok=True)
        copied = 0
        for f in os.listdir(first_dir):
            if f.lower().endswith(IMG_EXT):
                shutil.copy(os.path.join(first_dir, f), os.path.join(last_dir, f))
                copied += 1
        print(f"[首帧-only] 未提供尾帧，已将首帧复制为尾帧（{copied} 张）→ {last_dir}")
        n_first = count_images(first_dir)
        n_last = n_first

    total = args.count or n_first
    if total < 1:
        print(f"[error] 图片数不足（需至少 1 张首帧）；count={total}"); sys.exit(1)

    wf_path = os.path.join(WF_DIR, WF_FILE)
    if not os.path.isfile(wf_path):
        print(f"[error] 技能工作流缺失: {wf_path}"); sys.exit(1)
    api = cc.load_workflow(wf_path)

    # 首/尾帧目录：写入 PrimitiveString「首帧」(134) /「尾帧」(135)（按当前 value 区分，title 相同都是「字符串」）
    dir_map = {"首帧": first_dir, "尾帧": last_dir}
    for nid in cc.find_nodes(api, class_type="PrimitiveString"):
        v = api[nid]["inputs"].get("value", "")
        if v in dir_map:
            api[nid]["inputs"]["value"] = dir_map[v]

    # 提示词：文件按行读取，原样透传（不再注入 BEAUTY_CLAUSE，用户 2026-08-13 弃用）
    with open(args.prompts_file, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]
    out_lines = [ln for ln in lines if ln.strip()]
    prompts_text = "\n".join(out_lines)
    cc.set_param(api, "Text Load Line From File", "file_path", os.path.abspath(args.prompts_file))
    cc.set_text(api, "多行文本", prompts_text)

    # 段数
    cc.set_param(api, "For循环-开始", "total", total)

    # 分辨率
    cc.set_resolution(api, args.aspect, args.megapixels)

    # 时长（可选，统一覆盖 Float 节点）
    if args.duration is not None:
        for nid in cc.find_nodes(api, class_type="PrimitiveFloat"):
            api[nid]["inputs"]["value"] = args.duration

    # seed：不传=随机（抽卡，打印本次 seed 并回写文档顶部），传=固定复用（成品）
    seed = args.seed
    hits = cc.find_nodes(api, class_type="RandomNoise")
    if hits:
        if seed is None:
            seed = random.randint(0, 2**63 - 1)
            for nid in hits:
                api[nid]["inputs"]["noise_seed"] = seed
            print(f"  SEED: {seed}")
            print(f"    （0.1/0.2 抽卡：此值已回写 提示词生成.md 顶部 视频抽卡种子；0.3-0.9 成品档跑 --seed {seed} 复用同一内容）")
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

    # 输出前缀（正确工作流用 VHS_VideoCombine 保存；防互顶自动加 _2/_3… 序号）
    prefix = _unique_prefix(args.output_prefix, args.comfy_output)
    if prefix != args.output_prefix:
        print(f"  输出防互顶：前缀 {args.output_prefix} 已有产出，自动改用 {prefix}")
    cc.set_param(api, "VHS_VideoCombine", "filename_prefix", prefix)

    mode = "首帧-only" if not args.last_dir else "首+尾"
    print(f"[run] FL2VA 段数={total} 模式={mode} first={first_dir} last={last_dir} aspect={args.aspect} mp={args.megapixels}")
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
