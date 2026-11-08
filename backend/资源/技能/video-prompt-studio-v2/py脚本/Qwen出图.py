#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qwen出图.py — 调用 Qwen-Image-Edit 工作流出图（角色图 / 首尾帧 / 场景图）。

【传参说明】
  --mode          出图模式，二选一（默认 single）：
                    single  = 单图编辑      → qwen2511 单图编辑版本 (2).json
                    general = 三图参考(通用) → qwen2511 双图编辑版本 (1).json（1 主图 + 2 参考图）
  --image1 PATH   必填。主图（单图模式）或 图1/主图（双图/三图模式）。本地图片路径即可（脚本自动上传到 ComfyUI，不要手填 input/ 文件名）。
  --image2 PATH   双图/三图模式必填。参考图1（通用编辑的第二张参考图）。
  --image3 PATH   三图参考模式(general)可选。参考图2 = **背景参考图**（如 Z-Image 生成的场景图 / 真实场景照片），
                    传入后生成图共享该背景，保证跨镜头背景一致。不传则退化为双图。
  --prompt TEXT   正向编辑提示词（必填）。例如「让图1人物保持外貌，换上图2的衣服」。
  --negative TEXT 负向提示词（可选，不填则用内置洁净度负向）。
  --output-prefix 保存前缀（默认 Qwen_Edit_2511），落盘到 ComfyUI output/。
  --width/--height 出图目标边长（可选，默认按原图；Quality 由 Qwen 模型决定）。
  --comfy-url     ComfyUI 地址（默认 http://127.0.0.1:8188）。
  --timeout       等待秒数（默认 600）。

【落盘目录：配置驱动，无需手传（用户规则 2026-08-13 续，已写进代码）】
  之前靠文档规则要求"生成后必须回写地址、产物落指定目录"，实际漏填/传错 --output-dir
  导致图落在 ComfyUI 默认盘、用户找不到。现在这两件事**脚本写死自动做**：
    - 不传 --output-dir 时，脚本读 工作配置.yaml 的 图片输出目录 自动落盘：
        * 帧模式（--storyboard + --seg + --frame-type）→ frames_fl2va/<seg>/<first|last>/001.png
        * 普通出图 → image_edit/（用 output_prefix 命名，防覆盖）
    - 帧模式生成后，脚本自动把该帧绝对路径回写 storyboard 对应段的
      「生成图片首帧地址 / 生成图片尾帧地址」字段（幂等，可反复跑）。
  仍可用 --output-dir / --frame-name 手动覆盖落点（向后兼容）。
  --output-dir   手动指定目标文件夹（如 ③ dirs.frames_fl2va）。不给则按上面自动落盘。
  --frame-name   落进 output-dir 的文件名（如 001.png）。仅手动模式需给；自动模式固定 001.png。
  --comfy-output ComfyUI 的 output 根目录（与 --output-dir 配合定位源文件并拷贝）。
                不给时自动模式会探测常用路径（D:/ComfyUI/output 等）。
  --storyboard / --seg / --frame-type
                帧模式三件套：给定后自动落 frames_fl2va 并回写 storyboard 帧地址。
                --seg 如 "段1"；--frame-type 取 first（首帧）或 last（尾帧）。

【底层机制（脚本已封装，了解即可）】
  - 正向提示词 → 节点 class_type="easy positive" 的 positive 字段。
  - 负向提示词 → 节点标题含「文本编码」的 TextEncodeQwenImageEditPlus 的 prompt 字段。
  - 图片       → LoadImage 节点（single=1 个；general=2 个；general 可选第 3 个=背景参考图）。
                下标按节点 id 数字排序：119=主图(image1) / 121=参考图1(image2) / 130=背景参考图(image3)。
                ⚠️ 工作流无节点控制左/右/背景排布——"图1在左、图2在右、图3是背景"如何表达，
                见 分镜规则.md（工作流提示词写法 › Qwen 首帧/尾帧提示词：提示词须声明人物→图映射/空间位置/双人各自朝向）。
  - 出图固定 steps=8 / cfg=1（Lightning LoRA），无需改。
  - 人物/环境洁净度负向已内置（dirty/grime/wrinkled skin(除非老年)/ugly 等）。
  - **提示词原样透传（用户规则 2026-08-27）**：发送的提示词是什么就是什么，脚本不再自动注入保五官/无阴影等任何条款。

示例：
  # 普通出图（落 ComfyUI 默认目录）
  python Qwen出图.py --mode single --image1 char_01.png \
      --prompt "保持人物外貌，改为晴朗白天的干净街道背景"

  # FL2VA 批量段：首/尾帧生图时直接落进 frames_fl2va 并按 001/002 命名
  python Qwen出图.py --mode single --image1 char_01_front.png \
      --prompt "保持人物外貌，干净街道背景" \
      --output-dir output/frames/fl2va --frame-name 001.png \
      --comfy-output D:/ComfyUI/output

  # 三图参考(通用)：主图 + 参考图1 + 背景参考图(保证跨镜头背景一致)
  # 硬规则（见 分镜规则.md 禁外貌描写）：已给参考图时，prompt 禁止描述人物长相/服装/五官/背景环境，
  #   只写动作、表情、姿态、构图、人数、特殊效果；参考图负责外貌与背景。
  # 硬规则（见 分镜规则.md 位置指代）：general 提示词必须声明 人物→图映射 + 空间位置 + 双人各自朝向
  #   （工作流无节点控制左/右/背景，全靠提示词文字；格式见 分镜规则.md 工作流提示词写法）。
  #   正确写法示例（图1在左、图2在右、图3背景，两人各自朝向避免都看镜头）：
  python Qwen出图.py --mode general --image1 main.png --image2 ref1.png \
      --image3 background_zimage.png \
      --prompt "图1人物李宝明在左、图2人物王哲在右，以图3为背景；两人并肩而立，神情惊愕、转头四望，李宝明侧脸看向右侧、王哲看向画面左侧"

  # ⭐ 自动帧模式（推荐）：不传 --output-dir，脚本按 config 落 frames_fl2va 并自动回写 storyboard
  #   生成后段1 首帧落在 <config.dirs.frames_fl2va>/段1/first/001.png，
  #   并自动把该绝对路径写回 storyboard「生成图片首帧地址」字段（⑧ 直接读，无需手工回填）。
  python Qwen出图.py --mode general --image1 main.png --image2 ref1.png \
      --image3 "D:/.../真实场景/街道.png" \
      --prompt "保持图1人物特征与图2人物特征，两人并肩站在图3背景中，神情惊愕、转头四望" \
      --storyboard 提示词生成.md --seg 段1 --frame-type first \
      --comfy-output D:/ComfyUI/output
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import Comfy客户端 as cc
import 项目路径 as pp  # 配置驱动落盘 + storyboard 自动回写（用户规则 2026-08-13 续）

WF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "工作流")

MODE_FILES = {
    "single":  "qwen2511 单图编辑版本  (2).json",
    "general": "qwen2511 双图编辑版本  (1).json",
}

DEFAULT_NEGATIVE = (
    "脏污，污渍，皱纹皮肤（老年除外），丑陋，脏墙，破旧损坏的道具，"
    "低质量"
)


def _locate_generated(comfy_output, prefix, out):
    """从 extract_outputs 结果里取第一张生成图，拼出 ComfyUI 输出盘的源文件路径。"""
    if not comfy_output:
        return None
    fname = None
    for nid, kinds in (out or {}).items():
        if isinstance(kinds, dict) and "images" in kinds and kinds["images"]:
            fname = kinds["images"][0]
            break
    if fname:
        # ComfyUI SaveImage 通常把文件写进 <comfy_output>/<prefix>/<filename>
        cand = os.path.join(comfy_output, prefix, fname)
        if os.path.exists(cand):
            return cand
        cand2 = os.path.join(comfy_output, fname)
        if os.path.exists(cand2):
            return cand2
    # 兜底：在 comfy_output 整棵树下找最近修改的 png（应对 SaveImage 落点子目录差异）
    try:
        hits = []
        for root, _, files in os.walk(comfy_output):
            for fn in files:
                if fn.lower().endswith(".png"):
                    hits.append(os.path.join(root, fn))
        if hits:
            return max(hits, key=os.path.getmtime)
    except OSError:
        pass
    return None


def main():
    ap = argparse.ArgumentParser(description="Qwen 出图调用")
    ap.add_argument("--mode", choices=list(MODE_FILES), default="single")
    ap.add_argument("--image1", required=True)
    ap.add_argument("--image2", default=None)
    ap.add_argument("--image3", default=None,
                    help="三图参考(general)可选：参考图2=背景参考图(Z-Image 场景图/真实场景照片)，保跨镜头背景一致")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--negative", default=DEFAULT_NEGATIVE)
    ap.add_argument("--output-prefix", default="Qwen_Edit_2511")
    ap.add_argument("--comfy-url", default=cc.DEFAULT_URL)
    ap.add_argument("--timeout", type=int, default=None,
                    help="等待秒数（默认 None = 无限等待，由 Comfy客户端.wait 保证）")
    # FL2VA 批量段：生图时直接落进项目 frames_fl2va（用户硬规则）
    ap.add_argument("--output-dir", default=None,
                    help="目标项目文件夹（如 frames_fl2va）；给定后自动拷入并重命名")
    ap.add_argument("--frame-name", default=None,
                    help="落进 output-dir 的文件名（如 001.png）；需与 --output-dir 配合")
    ap.add_argument("--comfy-output", default=None,
                    help="ComfyUI output 根目录；配合 --output-dir 定位源文件拷贝（自动模式会尝试探测）")
    # ---- 配置驱动落盘 + 自动回写（用户规则 2026-08-13 续：不再靠文档规则/人工回填）----
    ap.add_argument("--storyboard", default=None,
                    help="storyboard 路径；配 --seg/--frame-type 时，生成后自动把帧地址回写该段")
    ap.add_argument("--seg", default=None,
                    help="段标识（如 段1 / 段A）；配 --storyboard/--frame-type 自动回写")
    ap.add_argument("--frame-type", choices=["first", "last"], default=None,
                    help="FL2VA 帧类型：first=首帧 / last=尾帧；触发自动落 frames_fl2va 并回写")
    args = ap.parse_args()

    if (args.output_dir or args.frame_name) and not (args.output_dir and args.frame_name):
        print("[error] --output-dir 与 --frame-name 必须同时给定（FL2VA 批量段）"); sys.exit(1)
    if args.output_dir and not args.comfy_output:
        print("[warn] 给了 --output-dir 但没给 --comfy-output，将无法自动拷贝，"
              "请手动把 ComfyUI 输出拷到目标目录")

    wf_path = os.path.join(WF_DIR, MODE_FILES[args.mode])
    if not os.path.exists(wf_path):
        print(f"[error] 工作流不存在: {wf_path}"); sys.exit(1)

    api = cc.load_workflow(wf_path)

    # 图片（set_image 会先把本地文件上传到 ComfyUI，再写回文件名；LoadImage 不认绝对路径）
    if args.mode == "single":
        cc.set_image(api, "LoadImage", args.image1, 0, url=args.comfy_url)
    else:
        if not args.image2:
            print("[error] 双图模式需要 --image2"); sys.exit(1)
        cc.set_image(api, "LoadImage", args.image1, 0, url=args.comfy_url)  # 主图
        cc.set_image(api, "LoadImage", args.image2, 1, url=args.comfy_url)  # 参考图1
        if args.image3:
            # 三图参考：参考图2 = 背景参考图（Z-Image 场景图 / 真实场景照片），保跨镜头背景一致
            cc.set_image(api, "LoadImage", args.image3, 2, url=args.comfy_url)
        else:
            # 双图模式：第 3 个 LoadImage 节点（背景参考图 image3，节点130）若留空，
            # ComfyUI 后端加载工作流时空 image 访问 input 会报 Permission denied（手动界面容错、API 不容错）。
            # 复用参考图1 填充该通道，保证 3 个图像输入都有有效图、规避报错（不影响双图主语义）。
            cc.set_image(api, "LoadImage", args.image2, 2, url=args.comfy_url)

    # 提示词（用户规则 2026-08-27：发送的提示词是什么就是什么，脚本不再追加任何保五官/无阴影等条款）
    positive = (args.prompt or "").rstrip()
    # 正向提示词节点：两个 qwen 工作流（单图/双图通用）的标题均为「正面提示词」、
    # class_type 均为 easy positive（全小写，_looks_like_class 会误判为"非 class_type"而改走
    # title 匹配，但 title 是「正面提示词」≠"easy positive"，导致匹配失败、正向提示词丢失）。
    # 故此处直接用 title 子串「正面提示词」匹配，对三种模式通用。
    cc.set_param(api, "正面提示词", "positive", positive)
    negative = (args.negative or "").rstrip()
    cc.set_param(api, "文本编码", "prompt", negative)

    # 输出前缀
    cc.set_param(api, "SaveImage", "filename_prefix", args.output_prefix)

    print(f"[run] Qwen 出图 mode={args.mode} prompt={args.prompt[:40]}...")
    out = cc.run(api, url=args.comfy_url, timeout=args.timeout)
    for nid, kinds in out.items():
        print(f"  节点{nid}: {kinds}")

    # ---- 自动落盘目录（配置驱动，用户规则 2026-08-13 续：不再手传 --output-dir）----
    # 未显式给 --output-dir 时，按 工作配置.yaml 的 图片输出目录 决定落点：
    #   - 帧模式（--storyboard + --seg + --frame-type）：落到 frames_fl2va/<seg>/<first|last>/001.png
    #   - 普通出图：落到 image_edit/（用 output_prefix 作文件名，防覆盖）
    # 显式给 --output-dir 则仍走原逻辑（手动覆盖优先）。
    if not args.output_dir:
        if args.storyboard and args.seg and args.frame_type:
            dirs = pp.load_dirs(os.path.dirname(os.path.abspath(args.storyboard)))
            sk = pp.seg_key(args.seg)
            args.output_dir = os.path.join(dirs["frames_fl2va"], sk, args.frame_type)
            args.frame_name = "001.png"
        else:
            dirs = pp.load_dirs(os.getcwd())
            base = re.sub(r"[\\/:]", "_", args.output_prefix)
            out_path = pp.unique_name(dirs["image_edit"], base, ".png")
            args.output_dir = os.path.dirname(out_path)
            args.frame_name = os.path.basename(out_path)

    # FL2VA 批量段 / 通用：把生成结果拷进 output-dir 并重命名（生图时指定文件夹，否则 ⑧ 读不到）
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        # 未给 --comfy-output 时尝试探测 ComfyUI output 根，保证自动模式也能拷
        if not args.comfy_output:
            args.comfy_output = pp.resolve_comfy_output()
            if not args.comfy_output:
                print(f"[warn] 未提供 --comfy-output 且未探测到 ComfyUI output 根，"
                      f"无法自动拷贝；请手动把 ComfyUI 生成图拷到 {args.output_dir}/{args.frame_name}")
        src = _locate_generated(args.comfy_output, args.output_prefix, out)
        if src and os.path.exists(src):
            dst = os.path.join(args.output_dir, args.frame_name)
            import shutil
            shutil.copy2(src, dst)
            print(f"[copy] {src} -> {dst}")
            # 帧模式：自动回写 storyboard 对应段「生成图片首帧地址 / 生成图片尾帧地址」
            if args.storyboard and args.seg and args.frame_type:
                dst_abs = dst.replace("\\", "/")
                field = "生成图片首帧地址" if args.frame_type == "first" else "生成图片尾帧地址"
                ok = pp.write_back_field(args.storyboard, pp.seg_key(args.seg), field, dst_abs)
                if ok:
                    print(f"[回写] {field}: {dst_abs}")
                else:
                    print(f"[warn] 在 storyboard 未找到段 {args.seg}，未回写 {field}")
        else:
            print(f"[warn] 未定位到生成文件，请手动拷到 {args.output_dir}/{args.frame_name}")


if __name__ == "__main__":
    main()
