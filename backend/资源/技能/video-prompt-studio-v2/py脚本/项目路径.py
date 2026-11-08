#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目路径.py — 配置驱动的产物落点 + storyboard 字段自动回写（脚本硬化层）。

为什么存在（用户规则 2026-08-13 续）：
  之前「生成后必须回写地址」「产物落指定目录」是写在文档里的"规则"，靠人记、靠人填，
  结果要么漏回写、要么 --output-dir 传错导致图落在 ComfyUI 默认盘、用户找不到。
  这两件事现在**写死在脚本里**：脚本读 工作配置.yaml 的 图片输出目录 / 视频输出目录 自动落盘，
  生成后自动把帧地址/视频地址回写 storyboard——不依赖任何文档规则或人工步骤。

职责：
  1. load_dirs(work_dir)        读 工作配置.yaml 的 图片输出目录 / 视频输出目录，
                                全部返回绝对 forward-slash 路径；配置缺失时用
                                基于 <work_dir>/output 的默认布局兜底（脚本永远能自动落盘）。
  2. resolve_comfy_output()     定位 ComfyUI 的 output 根（用于把生成产物从 ComfyUI 盘
                                拷贝到项目配置目录）；显式参数 > 候选路径探测。
  3. seg_key(name)              段标题 → 短键（"段1 — 穿越现身" → "段1"），
                                与 run_storyboard 的 seg_key 保持一致。
  4. write_back_field(...)      把任一字段写回 storyboard 指定段（自动回写核心）。
                                幂等：已存在则覆盖，不存在则插入到 insert_after 行后。

注：只用标准库（re/os），不连 ComfyUI、不读工作流 JSON。yaml 用正则兜底，避免强依赖。
"""
import os
import re

CONFIG_NAME = "工作配置.yaml"

# ComfyUI output 根候选（用于从 ComfyUI 输出拷贝产物到项目配置目录）
# 显式 --comfy-output 优先；否则按此顺序探测第一个存在的目录。
COMFY_OUTPUT_CANDIDATES = [
    "D:/ComfyUI/output",
    "D:/ComfyUI-aki-v3/ComfyUI/output",
    "C:/ComfyUI/output",
    "D:/ComfyUI-aki-v3/output",
]


def find_config(work_dir):
    """在工作目录及其父目录链（最多 6 层）找 工作配置.yaml；找不到返回 None。"""
    cur = os.path.abspath(work_dir)
    for _ in range(6):
        p = os.path.join(cur, CONFIG_NAME)
        if os.path.isfile(p):
            return p
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None


def _load_yaml(path):
    """尽量用 yaml 解析；未装或失败时返回 None（交给调用方正则兜底）。"""
    try:
        import yaml
        return yaml.safe_load(open(path, encoding="utf-8"))
    except Exception:
        return None


def _flat_read(path):
    """极简解析 工作配置.yaml 的扁平中文字段（yaml 不可用时的兜底，与 生成首尾帧与背景.py 同口径）。"""
    d = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if ":" in line:
                    k, _, v = line.partition(":")
                    d[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return d


def load_dirs(work_dir):
    """读 工作配置.yaml 的 图片输出目录 / 视频输出目录 / 角色资源所在目录；
    缺失则用基于 <work_dir>/图片、<work_dir>/视频 的默认布局兜底。

    返回 dict（全部绝对 forward-slash 路径）：
        output_dir / image_edit / frames_fl2va / video_raw / frames_4k / characters
    """
    cfg_path = find_config(work_dir)
    cfg = {}
    if cfg_path:
        cfg = _load_yaml(cfg_path)
        if not isinstance(cfg, dict):
            cfg = _flat_read(cfg_path)

    def _abs(v):
        return os.path.abspath(v).replace("\\", "/") if v else ""

    img_out = _abs(cfg.get("图片输出目录")) or os.path.abspath(os.path.join(work_dir, "图片")).replace("\\", "/")
    vid_out = _abs(cfg.get("视频输出目录")) or os.path.abspath(os.path.join(work_dir, "视频")).replace("\\", "/")
    role_dir = _abs(cfg.get("角色资源所在目录")) or os.path.abspath(os.path.join(work_dir, "角色")).replace("\\", "/")
    return {
        "output_dir": vid_out,
        "image_edit": img_out,
        "frames_fl2va": f"{img_out}/frames/fl2va",
        "video_raw": f"{vid_out}/raw",
        "frames_4k": f"{vid_out}/frames/4k",
        "characters": role_dir,
    }


def resolve_comfy_output(explicit=None):
    """定位 ComfyUI 的 output 根：显式参数优先，否则探测候选目录。找不到返回 None。"""
    if explicit:
        return os.path.abspath(explicit).replace("\\", "/")
    for c in COMFY_OUTPUT_CANDIDATES:
        if os.path.isdir(c):
            return c.replace("\\", "/")
    return None


def seg_key(name):
    """段标题 → 短键（"段A — ..." → "段A"）。"""
    return re.split(r"[—\-—\s]", name)[0].strip() or name


def _seg_blocks(text):
    """返回 [(start, end, name)] 每段在文本中的区间（含段标题行）。"""
    marks = [(m.start(), m.group(1))
             for m in re.finditer(r"(?m)^[ \t]*#+[ \t]*=*[ \t]*(段[^\n=]+)", text)]
    blocks = []
    for i, (start, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        blocks.append((start, end, name))
    return blocks


def write_back_field(storyboard, seg_key_val, field, value, insert_after="分辨率"):
    """把 {field: value} 写回 storyboard 指定段（自动回写核心）。

    - seg_key_val：段标题首词（段1 / 段A 等），与 seg_key() 同口径。
    - 已存在该字段 → 覆盖其值（幂等，可反复跑不重复插入）。
    - 不存在 → 插在 insert_after（默认「分辨率」）行之后；若段内也无 insert_after，则追加到段末。
    - value 以双引号包裹写入（与 storyboard 现有字段格式一致）。

    返回 True 表示命中并写入了对应段；False 表示没找到该段。
    """
    with open(storyboard, encoding="utf-8") as f:
        text = f.read()
    blocks = _seg_blocks(text)
    target = None
    for start, end, name in blocks:
        if seg_key(name) == seg_key_val:
            target = (start, end)
            break
    if not target:
        return False
    start, end = target
    block = text[start:end]
    new_line = f'  {field}: "{value}"'
    if re.search(rf"(?m)^[ \t]{{2,}}{re.escape(field)}\s*[:：]", block):
        block = re.sub(
            rf"(?m)^([ \t]{{2,}}){re.escape(field)}\s*[:：]\s*\"?[^\n]*\"?",
            lambda m: f'{m.group(1)}{field}: "{value}"', block)
    else:
        m2 = re.search(rf"(?m)^([ \t]{{2,}}){re.escape(insert_after)}[^\n]*\n", block)
        if m2:
            block = block[:m2.end()] + new_line + "\n" + block[m2.end():]
        else:
            block = block + new_line + "\n"
    text = text[:start] + block + text[end:]
    with open(storyboard, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def write_back_top_field(storyboard, field, value):
    """把文档顶部（非段内）的全局字段 {field: value} 更新（幂等覆盖）。

    用于 视频抽卡种子 这类位于文件顶部、不属于任何段的全局字段。
    命中则替换整行；未命中则追加到文件末尾。返回是否命中已存在字段。
    """
    with open(storyboard, encoding="utf-8") as f:
        text = f.read()
    # 仅匹配行首无缩进的字段（排除段内同名/相似字段）
    pat = re.compile(r'^(?![\t ])' + re.escape(field) + r'\s*[:：]', re.MULTILINE)
    new_line = f'{field}: "{value}"'
    if pat.search(text):
        text = pat.sub(lambda _: new_line, text, count=1)
        hit = True
    else:
        text = text.rstrip("\n") + "\n" + new_line + "\n"
        hit = False
    with open(storyboard, "w", encoding="utf-8") as f:
        f.write(text)
    return hit


def resolve_storyboard(config_path):
    """从 工作配置.yaml 解析 提示词生成文件 的绝对路径；无 config 或字段缺失返回 None。"""
    if not config_path or not os.path.isfile(config_path):
        return None
    cfg = _flat_read(config_path)
    fn = cfg.get("提示词生成文件")
    if not fn:
        return None
    base = os.path.dirname(os.path.abspath(config_path))
    p = os.path.join(base, fn)
    return p if os.path.isfile(p) else None


def unique_name(directory, base, ext):
    """在 directory 内生成不覆盖的 <base><ext>（已存在则加 _2/_3…）。"""
    os.makedirs(directory, exist_ok=True)
    cand = os.path.join(directory, f"{base}{ext}")
    if not os.path.exists(cand):
        return cand
    n = 2
    while True:
        cand = os.path.join(directory, f"{base}_{n}{ext}")
        if not os.path.exists(cand):
            return cand
        n += 1


VIDEO_EXTS = (".mp4", ".webm", ".gif", ".mov", ".mkv")


def locate_video(prefix, comfy_output):
    """根据 ComfyUI 的 output 前缀定位实际生成的视频文件绝对路径。

    prefix 如 "video/MiniMax_H3_段1_04"（相对 comfy_output）。实际文件落在
    comfy_output/video/MiniMax_H3_段1_04.<ext>，防互顶可能改名 _2/_3。
    返回第一个匹配的绝对路径（forward-slash），找不到返回 None。
    """
    if not comfy_output:
        return None
    rel_dir, base = os.path.split(prefix)
    search_dir = os.path.join(comfy_output, rel_dir) if rel_dir else comfy_output
    if not os.path.isdir(search_dir):
        return None
    base_l = base.lower()  # Windows 文件名不区分大小写，Python startswith 区分，统一转小写比
    for fn in sorted(os.listdir(search_dir)):
        fl = fn.lower()
        if fl.startswith(base_l) and fl.endswith(VIDEO_EXTS):
            return os.path.join(search_dir, fn).replace("\\", "/")
    return None


if __name__ == "__main__":
    # 自测：打印当前脚本目录的默认布局 + 若附近有 config 则打印读到的 dirs
    here = os.path.dirname(os.path.abspath(__file__))
    print("默认布局（work_dir=脚本目录）:")
    for k, v in load_dirs(here).items():
        print(f"  {k}: {v}")
    print("ComfyUI output 探测:", resolve_comfy_output())
