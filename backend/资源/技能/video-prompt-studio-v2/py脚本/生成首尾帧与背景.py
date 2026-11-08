#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成首尾帧与背景.py — 功能 5：读取 提示词生成.md，批量出「首帧 / 尾帧」静帧图 与
「背景图」，并自动把生成文件地址回写到 md（无需人工回填）。

────────────────────────────────────────────────────────────────
做什么
  1. 读 工作配置.yaml → 角色资源所在目录 / 背景资源所在目录 / 图片输出目录 /
     角色背景一览表 / 提示词生成文件。
  2. 读 角色背景一览表.md 的「剧情角色清单」→ 剧情角色名 → 匹配资源角色（参考图）映射。
  3. 解析 提示词生成.md 的全部 段<N> 块。
  4. 对每个段（或全部段跑一遍）：
     a. 是否生成背景图片 = 是 且 场景背景图 为空 → 用 文生图（Z-Image）出背景图：
        提示词 = 场景背景描述（强制补「无阴影无暗影 + 空旷无人」），
        产物命名 <场景ID>_背景.png，回写 场景背景图 / 背景图片存放位置。
     b. 是否生成首帧图片 = 是 → 用 图片工作流（Qwen general）出 首帧 与 尾帧：
        图片1 = 角色1 资源图，图片2 = 角色2 资源图（无则复用图片1），图片3 = 背景图；
        提示词 = 生成图片提示词首帧 / 生成图片提示词尾帧（强制补「无阴影无阴暗」），
        产物 <段N>_首帧.png / <段N>_尾帧.png，回写 生成图片首帧地址 / 生成图片尾帧地址。

人物一致性硬规则（全程遵守；详见 分镜规则.md 禁外貌描写 / 位置指代）
  - 提示词**不提人名**，只用「图片1的角色 / 图片2的角色 / 图片3的场景」指代；
    人物真实长相由 --image1 / --image2 传入的参考图锚定，背景由 --image3 锚定。
  - 必须具体描述人物占位（左 / 右 / 前 / 后）+ 各自朝向（看镜头 / 互看 / 侧脸 / 转头…）。
  - 禁外貌 / 服装 / 背景环境描写（这些由参考图负责，多写一句都算过量）。
  - 背景图必须「空旷无人」（人物由 Qwen 合成阶段加，不在背景里出现）。

依赖（同目录，直接复用，不要重复造轮子）
  - Qwen出图.py    → Qwen 出首 / 尾帧（已内嵌：保人物一致、强制无阴影、洁净负向）
  - Z-Image文生图.py→ Z-Image 出背景（已内嵌：强制无阴影）
  - Comfy客户端.py      → 上传本地图 / 调 ComfyUI
  - 项目路径.py     → md 字段自动回写（write_back_field）/ ComfyUI 输出盘定位

传参
  --config PATH       工作配置.yaml（定位一切；默认取 <本脚本目录>/../工作配置.yaml）
  --project-dir PATH  工作目录（无 --config 时用，定位 工作配置.yaml 与 md）
  --comfy-url URL     ComfyUI 地址（默认 http://127.0.0.1:8188）
  --comfy-output DIR  ComfyUI 输出根（默认自动探测；用于把产物从 ComfyUI 盘拷到项目目录）
  --dry-run           只打印将要执行的任务，不真正出图、也不回写 md（用于核对）
  --only 段1,段2      只处理指定段（逗号分隔，可选；段标识取「段N」，如 段1,段3）

示例
  python 生成首尾帧与背景.py --config "D:/proj/工作配置.yaml"
  python 生成首尾帧与背景.py --config "D:/proj/工作配置.yaml" --dry-run
  python 生成首尾帧与背景.py --config "D:/proj/工作配置.yaml" --only 段1,段2
"""
import argparse
import atexit
import os
import re
import signal
import subprocess
import sys
import urllib.request
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import 项目路径 as pp  # 复用 md 回写 + ComfyUI 输出定位
import Comfy客户端 as cc  # free_vram：每段出图后卸载模型，防连续段占满显存

# ── 运行互斥锁：防止多个出图/出视频进程并发抢 GPU（用户硬规则）──
# 出图(本脚本)与出视频(生成视频.py)同目录，共用同一把锁 .gen_run_lock，
# 确保任意时刻只有一个生成进程在跑，杜绝「多个测试进程互相打断 / 失败后又有图出来」。
RUN_LOCK = os.path.join(HERE, ".gen_run_lock")


def _pid_alive(pid):
    """跨平台判断 PID 是否存活（Windows 用 kernel32.OpenProcess）。"""
    if not pid or pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            kh = ctypes.windll.kernel32
            h = kh.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
            if h:
                kh.CloseHandle(h)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_run_lock():
    """获取运行锁。存活进程已持锁 -> 退出；陈旧锁（持有进程已死）-> 抢占。"""
    try:
        fd = os.open(RUN_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        old_pid = None
        try:
            with open(RUN_LOCK, encoding="utf-8") as f:
                old_pid = int((f.read() or "0").strip() or 0)
        except Exception:
            old_pid = None
        if old_pid and _pid_alive(old_pid):
            print(f"[互斥锁] 已有实例在运行（PID={old_pid}），本进程退出。锁文件：{RUN_LOCK}")
            sys.exit(2)
        try:
            os.remove(RUN_LOCK)
        except OSError:
            pass
        try:
            fd = os.open(RUN_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            print(f"[互斥锁] 锁被瞬间抢占，本进程退出：{RUN_LOCK}")
            sys.exit(2)
    os.write(fd, str(os.getpid()).encode("utf-8"))
    os.close(fd)
    print(f"[互斥锁] 已获取运行锁（本进程 PID={os.getpid()}）")


def release_run_lock():
    try:
        os.remove(RUN_LOCK)
    except OSError:
        pass

# ── 工作配置.yaml 中文字段键 ──────────────────────────────────────────────
CFG_ROLE_DIR = "角色资源所在目录"
CFG_BG_DIR = "背景资源所在目录"
CFG_IMG_OUT = "图片输出目录"
CFG_OVERVIEW = "角色背景一览表"
CFG_STORYBOARD = "提示词生成文件"

# 段内已知字段名（用于判断「使用角色」等块字段的结束边界）
KNOWN_FIELDS = {
    "生成图片的工作流", "是否生成首帧图片", "生成视频的工作流", "视频时长",
    "生成视频地址", "场景ID", "场景背景图", "场景背景描述", "是否生成背景图片",
    "背景图片存放位置", "seed", "负向提示词", "生成图片提示词首帧",
    "生成图片提示词尾帧", "生成图片首帧地址", "生成图片尾帧地址",
    "生成视频的提示词", "连续性锚点", "转场动机", "对话处理",
    "Ref2VA资源分配", "使用角色", "小说情节",
}

FIELD_RE = re.compile(r'^[ \t]*([一-龥A-Za-z0-9_]+)\s*[:：]\s*(.*)$')
SEG_RE = re.compile(r'(?m)^[ \t]*#+[ \t]*=*[ \t]*(段[^\n=]+)')
IMG_SLOT_RE = re.compile(r'图片\s*(\d+)\s*[:：]\s*([^\n]+)')


# ── 配置 / 一览表解析 ────────────────────────────────────────────────────
def read_config(config_path):
    """极简解析 工作配置.yaml 的扁平中文字段（不依赖 PyYAML）。"""
    d = {}
    if not config_path or not os.path.exists(config_path):
        return d
    with open(config_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" in line:
                k, _, v = line.partition(":")
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def load_role_map(overview_path):
    """读 角色背景一览表.md 的「剧情角色清单」→ {剧情角色名: 资源角色参考图文件名}。"""
    m = {}
    if not os.path.exists(overview_path):
        return m
    with open(overview_path, encoding="utf-8") as f:
        content = f.read()
    # 按「标题行」定位，避免一览表中 blockquote 内联的「## 剧情角色清单」字样误命中
    m_head = re.search(r'(?m)^#{1,6}[ \t]*剧情角色清单[ \t]*$', content)
    if not m_head:
        return m
    rest = content[m_head.end():]
    nxt = re.search(r'(?m)^## ', rest)
    body = rest[: nxt.start()] if nxt else rest
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "剧情角色" in line or re.match(r'\|[\s\-:|]+\|$', line):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2 or not cols[0]:
            continue
        name, ref = cols[0], cols[1]
        fn = re.findall(r'`([^`]+\.(?:png|jpg|jpeg|webp|bmp))`', ref, re.IGNORECASE)
        if fn:
            m[name] = fn[0]
    return m


# ── 段块解析 ─────────────────────────────────────────────────────────────
def parse_storyboard(text):
    """返回 [(name, key, fields)]；fields 为段内字段字典。"""
    marks = [(m.start(), m.group(1)) for m in SEG_RE.finditer(text)]
    segs = []
    for i, (start, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        block = text[start:end]
        fields = {}
        lines = block.splitlines()
        j = 0
        while j < len(lines):
            m = FIELD_RE.match(lines[j])
            if m:
                fname, val = m.group(1), m.group(2).strip()
                # 判定块字段：
                #  ① 行内值以 | 开头（表格块）；
                #  ② 行内值为空 且 下一非空行缩进更深（缩进续行块，如 使用角色 / 连续性锚点 / Ref2VA资源分配）。
                is_block = False
                if val.startswith("|"):
                    is_block = True
                elif not val:
                    nk = j + 1
                    while nk < len(lines) and not lines[nk].strip():
                        nk += 1
                    if nk < len(lines):
                        cur_indent = len(lines[j]) - len(lines[j].lstrip())
                        nxt_indent = len(lines[nk]) - len(lines[nk].lstrip())
                        if nxt_indent > cur_indent:
                            is_block = True
                if is_block:
                    indent = len(lines[j]) - len(lines[j].lstrip())
                    k = j + 1
                    buf = []
                    while k < len(lines):
                        cur = lines[k]
                        cur_stripped = cur.strip()
                        if not cur_stripped:
                            break
                        fm = FIELD_RE.match(cur)
                        cur_indent = len(cur) - len(cur.lstrip())
                        # 回到与字段同级（缩进<=字段缩进）且为已知字段时结束块
                        if fm and cur_indent <= indent and fm.group(1) in KNOWN_FIELDS:
                            break
                        buf.append(cur)
                        k += 1
                    fields[fname] = "\n".join(s.strip() for s in buf)
                    j = k
                    continue
                else:
                    fields[fname] = val.strip().strip('"').strip("'")
            j += 1
        segs.append((name, pp.seg_key(name), fields))
    return segs


def get_role_names(use_role_block):
    """从 使用角色 块提取有序角色名：[图片1, 图片2, ...]。"""
    names = []
    if not use_role_block:
        return names
    for mid, nm in IMG_SLOT_RE.findall(use_role_block):
        nm = nm.strip().strip('"').strip("'")
        if nm:
            names.append((int(mid), nm))
    names.sort(key=lambda x: x[0])
    return [nm for _, nm in names]


def _unquote(v):
    return (v or "").strip().strip('"').strip("'").strip()


def _is_yes(v):
    return _unquote(v) in ("是", "yes", "y", "true", "1")


# ── 路径解析 ─────────────────────────────────────────────────────────────
def _safe_name(s):
    """把场景ID/段标识转成文件名安全串（保留中文，替换路径非法字符）。"""
    s = (s or "").strip()
    for ch in ('\\', '/', ':', '*', '?', '"', '<', '>', '|', ' '):
        s = s.replace(ch, "_")
    return s or "未命名"


def resolve_role_file(role_dir, role_map, name):
    fn = role_map.get(name)
    if not fn:
        return None, f"剧情角色「{name}」在 角色背景一览表.md 找不到匹配资源角色（参考图）"
    if not role_dir:
        return None, "配置缺少 角色资源所在目录，无法定位角色参考图"
    p = os.path.join(role_dir, fn)
    if not os.path.exists(p):
        return None, f"角色参考图不存在：{p}"
    return p, ""


def resolve_bg_file(img_out, bg_dir, bg_name, bg_store):
    if bg_store and os.path.exists(bg_store):
        return bg_store
    if bg_name:
        for base in (img_out, bg_dir):
            if base:
                p = os.path.join(base, bg_name)
                if os.path.exists(p):
                    return p
        if os.path.exists(bg_name):
            return bg_name
    return None


# ── 提示词强制条款 ───────────────────────────────────────────────────────
def ensure_shadow_clause(prompt):
    """首帧/尾帧：强制含「无阴影无阴暗」。"""
    p = (prompt or "").rstrip("，。 ")
    if not any(k in p for k in ("无阴影", "无暗影", "无阴暗")):
        p += "，画面无阴影无阴暗"
    return p


def ensure_bg_clauses(prompt):
    """背景：强制含「无阴影无暗影」+「空旷无人」。"""
    p = (prompt or "").rstrip("，。 ")
    if not any(k in p for k in ("无阴影", "无暗影", "无阴暗")):
        p += "，无阴影无暗影"
    if not any(k in p for k in ("无人", "空旷无人")):
        p += "，空旷无人"
    return p


# ── 调用底层 runner ──────────────────────────────────────────────────────
def run_zimage(prompt, negative, copy_to, comfy_url, comfy_output, timeout=None):
    """调 Z-Image文生图.py 出背景；产物拷到 copy_to（独立暂存目录）。
    等待时间无限（wait 不超时）；timeout 仅作透传，默认 None=不限制。"""
    os.makedirs(copy_to, exist_ok=True)
    cmd = [sys.executable, os.path.join(HERE, "Z-Image文生图.py"),
           "--prompt", prompt, "--copy-to", copy_to,
           "--comfy-url", comfy_url]
    if timeout is not None:
        cmd += ["--timeout", str(timeout)]
    if negative:
        cmd += ["--negative", negative]
    if comfy_output:
        cmd += ["--comfy-output", comfy_output]
    print(f"  [Z-Image] prompt={prompt[:50]}... (等待时间无限)")
    subprocess.run(cmd, check=True)


def run_qwen(image1, image2, prompt, negative, out_dir, frame_name,
             comfy_url, comfy_output, timeout=None):
    """调 Qwen出图.py（general 双图）出一张静帧，落到 out_dir/frame_name。
    等待时间无限（wait 不超时）；timeout 仅作透传，默认 None=不限制。
    ⚠️ 双图模式（不传 --image3）：45GB 卡上三图模式（主图+参考图1+背景参考图）显存爆
       （峰值 57GB>OOM），实测双图（仅主图+参考图1）稳定不炸（峰值 33.7GB）。
       general 模式固定只喂 主图(node119)+参考图1(node121)；node130(背景参考图)留空
       会触发 ComfyUI API 的 Permission denied（UI 容错、API 不容错），故由 Qwen出图.py
       用参考图1 兜底填充 node130，规避报错且不引入第 3 张图、不增显存。
       背景参考图【默认不喂】，避免 OOM；跨镜头背景一致需换更大显存卡后，
       再在 Qwen出图.py 显式开启 --image3 路径。"""
    os.makedirs(out_dir, exist_ok=True)
    cmd = [sys.executable, os.path.join(HERE, "Qwen出图.py"),
           "--mode", "general",
           "--image1", image1, "--image2", image2,
           "--prompt", prompt, "--output-dir", out_dir, "--frame-name", frame_name,
           "--comfy-url", comfy_url]
    if timeout is not None:
        cmd += ["--timeout", str(timeout)]
    if negative:
        cmd += ["--negative", negative]
    if comfy_output:
        cmd += ["--comfy-output", comfy_output]
    print(f"  [Qwen] {frame_name} prompt={prompt[:50]}... (等待时间无限)")
    subprocess.run(cmd, check=True)


def _newest_png(directory):
    hits = []
    for fn in os.listdir(directory):
        if fn.lower().endswith(".png"):
            hits.append(os.path.join(directory, fn))
    return max(hits, key=os.path.getmtime) if hits else None


def _safe_rmtree(path):
    """删除目录；清理失败（如沙箱回收站不可用）只告警不中断，已生成的产物不回滚。"""
    if not os.path.isdir(path):
        return
    import shutil
    try:
        shutil.rmtree(path)
    except OSError as e:
        print(f"  [清理][警告] 删除临时目录失败（可忽略）：{path} —— {e}")


# ── 单段处理 ─────────────────────────────────────────────────────────────
def process_background(seg_fields, seg_key, storyboard, img_out, bg_dir,
                       cfg, comfy_url, comfy_output, dry_run, plan, timeout=None):
    bg_name = _unquote(seg_fields.get("场景背景图"))
    need = _is_yes(seg_fields.get("是否生成背景图片"))
    if not need:
        if not bg_name:
            print(f"  [背景][警告] {seg_key}：是否生成背景图片=否 且 场景背景图 为空"
                  f"（配置矛盾：该段无可用背景，相关帧将缺背景）")
        return
    if bg_name:
        print(f"  [背景] {seg_key}：场景背景图已存在（{bg_name}），跳过生成")
        return
    desc = _unquote(seg_fields.get("场景背景描述"))
    scene_id = _unquote(seg_fields.get("场景ID")) or seg_key
    if not desc:
        print(f"  [背景][警告] {seg_key}：需要出背景但 场景背景描述 为空，跳过")
        return
    prompt = ensure_bg_clauses(desc)
    target_name = f"{_safe_name(scene_id)}_背景.png"
    target_path = os.path.join(img_out, target_name)
    if dry_run:
        plan.append(f"[背景·dry] {seg_key} → {target_path}  prompt={prompt[:60]}...")
        return
    if os.path.exists(target_path):
        print(f"  [背景] {seg_key}：目标已存在 {target_name}，跳过（删后再跑可重出）")
        _write_back_bg(storyboard, seg_key, target_name, target_path)
        return
    stage = os.path.join(img_out, f"_bg_stage_{_safe_name(scene_id)}")
    _safe_rmtree(stage)
    run_zimage(prompt, _unquote(seg_fields.get("负向提示词")), stage,
               comfy_url, comfy_output, timeout)
    src = _newest_png(stage)
    if not src:
        print(f"  [背景][错误] {seg_key}：未定位到 Z-Image 生成文件，请手动拷到 {target_path}")
        return
    import shutil
    shutil.move(src, target_path)
    _safe_rmtree(stage)
    print(f"  [背景] 已生成 {target_path}")
    _write_back_bg(storyboard, seg_key, target_name, target_path)


def _write_back_bg(storyboard, seg_key, target_name, target_path):
    pp.write_back_field(storyboard, seg_key, "场景背景图", target_name,
                         insert_after="场景背景描述")
    pp.write_back_field(storyboard, seg_key, "背景图片存放位置",
                         target_path.replace("\\", "/"),
                         insert_after="是否生成背景图片")


def process_frames(seg_fields, seg_key, storyboard, img_out, role_dir, role_map,
                   bg_dir, comfy_url, comfy_output, dry_run, plan,
                   frames_mode="first", timeout=None):
    if not _is_yes(seg_fields.get("是否生成首帧图片")):
        return
    first_p = _unquote(seg_fields.get("生成图片提示词首帧"))
    if not first_p:
        print(f"  [帧][警告] {seg_key}：需要出首帧但 生成图片提示词首帧 缺失，跳过")
        return
    # frames_mode="first" → 只出首帧（默认）；"both" → 首帧+尾帧（旧默认）
    last_p = _unquote(seg_fields.get("生成图片提示词尾帧")) if frames_mode == "both" else ""
    # 角色资源
    names = get_role_names(seg_fields.get("使用角色"))
    if not names:
        print(f"  [帧][警告] {seg_key}：使用角色 为空，无法确定图片1/图片2 资源，跳过")
        return
    char1, err1 = resolve_role_file(role_dir, role_map, names[0])
    if not char1:
        print(f"  [帧][错误] {seg_key}：{err1}，跳过")
        return
    char2, err2 = (resolve_role_file(role_dir, role_map, names[1])
                   if len(names) > 1 else (char1, ""))
    if not char2:
        print(f"  [帧][错误] {seg_key}：{err2}，单角色模式复用图片1")
        char2 = char1
    # 背景：优先用已登记的 场景背景图 / 背景图片存放位置；
    # 同段刚生成的背景以 <场景ID>_背景.png 落盘，也作为候选（避免读不到刚生成的图）。
    # ⚠️ 双图模式（run_qwen 不喂 --image3）下 Qwen 出帧【不消费】背景参考图（避免 OOM），
    #   背景仅留给视频生成/参考用；因此【背景缺失不再阻断首/尾帧生成】——
    #   缺背景时 Qwen 节点130 由 Qwen出图.py 用参考图1 兜底，帧照常出。
    bg_name = _unquote(seg_fields.get("场景背景图"))
    bg_store = _unquote(seg_fields.get("背景图片存放位置"))
    scene_id = _unquote(seg_fields.get("场景ID"))
    candidates = []
    if bg_store:
        candidates.append(bg_store)
    if bg_name:
        candidates += [os.path.join(img_out, bg_name),
                       os.path.join(bg_dir, bg_name) if bg_dir else None,
                       bg_name]
    if scene_id:
        gen = os.path.join(img_out, f"{_safe_name(scene_id)}_背景.png")
        candidates.append(gen)
    bg = next((c for c in candidates if c and os.path.exists(c)), None)
    if not bg:
        print(f"  [帧][提示] {seg_key}：背景图暂不可用（双图模式不消费背景参考图，"
              f"不影响 Qwen 出帧；需跨镜头背景一致时换大显存卡再传 --image3）")
    neg = _unquote(seg_fields.get("负向提示词"))
    fn_first = f"{seg_key}_首帧.png"
    fn_last = f"{seg_key}_尾帧.png"
    pf = ensure_shadow_clause(first_p)
    pl = ensure_shadow_clause(last_p) if frames_mode == "both" else ""
    if dry_run:
        tail = f" / {fn_last}" if frames_mode == "both" else ""
        bg_disp = os.path.basename(bg) if bg else "(无，双图模式不消费背景参考图)"
        plan.append(f"[帧·dry] {seg_key} → {fn_first}{tail}  "
                    f"img1={os.path.basename(char1)} img2={os.path.basename(char2)} "
                    f"bg={bg_disp}")
        return
    run_qwen(char1, char2, pf, neg, img_out, fn_first, comfy_url, comfy_output, timeout)
    p1 = os.path.join(img_out, fn_first)
    if not os.path.exists(p1):
        print(f"  [帧][错误] {seg_key}：首帧未生成 {p1}")
    else:
        pp.write_back_field(storyboard, seg_key, "生成图片首帧地址",
                            p1.replace("\\", "/"), insert_after="生成图片提示词首帧")
        print(f"  [帧] 首帧 {p1}")
    if frames_mode == "both":
        run_qwen(char1, char2, pl, neg, img_out, fn_last, comfy_url, comfy_output, timeout)
        p2 = os.path.join(img_out, fn_last)
        if not os.path.exists(p2):
            print(f"  [帧][错误] {seg_key}：尾帧未生成 {p2}")
        else:
            pp.write_back_field(storyboard, seg_key, "生成图片尾帧地址",
                                p2.replace("\\", "/"), insert_after="生成图片提示词尾帧")
            print(f"  [帧] 尾帧 {p2}")
    else:
        print(f"  [帧] 仅出首帧模式（frames_mode=first），跳过尾帧 {fn_last}")


def cancel_comfyui(comfy_url):
    """（手动工具函数，执行器已不再自动调用）主动通知 ComfyUI 取消/清理任务——
    中断当前执行 + 清空队列。仅当用户需要手动清队列时使用，正常批量流程不再调用。

    这是用户硬规则：本地脚本出图失败，必须让 ComfyUI 也停止该任务，而非只退出本地进程。
    先查队列是否真有残留任务，有才清理、无则跳过（避免对空队列误报 interrupt）。
    """
    base = (comfy_url or "http://127.0.0.1:8188").rstrip("/")
    # 0) 先查队列是否真有残留（running / pending），避免对空队列误报
    has_task = False
    try:
        req = urllib.request.Request(base + "/queue", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        running = data.get("queue_running") or []
        pending = data.get("queue_pending") or []
        has_task = bool(running or pending)
    except Exception as e:
        print(f"  [warn] 查询 ComfyUI 队列失败（保守地仍尝试清理）：{e}")
        has_task = True  # 查不到就保守清理一次，宁滥勿漏
    if not has_task:
        print("  [ComfyUI] 队列已空，无需清理")
        return
    # 1) 中断当前正在执行的 prompt
    try:
        req = urllib.request.Request(
            base + "/interrupt", data=b"{}",
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
        print("  [ComfyUI] 已发送 interrupt（中断当前执行）")
    except Exception as e:
        print(f"  [warn] ComfyUI interrupt 失败（可忽略，任务可能已结束）：{e}")
    # 2) 清空队列（移除排队的待执行 prompt）
    try:
        req = urllib.request.Request(
            base + "/queue", data=json.dumps({"clear": True, "delete": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
        print("  [ComfyUI] 已清空队列（clear）")
    except Exception as e:
        print(f"  [warn] ComfyUI 清空队列失败（可忽略）：{e}")


# ── 主流程 ───────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="功能5：批量出首尾帧与背景并回写 md")
    ap.add_argument("--config", default=None, help="工作配置.yaml")
    ap.add_argument("--project-dir", default=None, help="工作目录（无 --config 时用）")
    ap.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    ap.add_argument("--comfy-output", default=None, help="ComfyUI 输出根（默认自动探测）")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不出图/不回写")
    ap.add_argument("--only", default=None, help="只处理指定段，逗号分隔，如 段1,段2")
    ap.add_argument("--frames", default="first", choices=["first", "both"],
                    help="出帧模式：first=只出首帧（默认）；both=首帧+尾帧（旧默认）")
    args = ap.parse_args()

    # ── 运行互斥锁（用户硬规则：防止多个出图/出视频进程并发抢 GPU）──
    acquire_run_lock()
    atexit.register(release_run_lock)   # 仅释放锁；退出时【不】清理 ComfyUI 队列，避免误清用户/其他进程任务

    # ── 失败处理（用户要求）：单段出图失败 → 直接跳下一段，不取消 ComfyUI 任务、不清理队列 ──
    # 进程退出 / 收到信号时【不】清理 ComfyUI 队列（避免误清用户/其他进程任务）；
    # 锁释放由 atexit 负责，与 ComfyUI 无关。
    def _on_signal(signum, _frame):
        try:
            name = signal.Signals(signum).name
        except Exception:
            name = str(signum)
        print(f"\n  [信号] 收到 {name}，释放运行锁后退出（不清理 ComfyUI 队列）...")
        release_run_lock()
        sys.exit(1)

    try:
        signal.signal(signal.SIGTERM, _on_signal)
        signal.signal(signal.SIGINT, _on_signal)
    except (ValueError, OSError) as e:
        print(f"  [warn] 注册信号处理器失败（不影响主流程）：{e}")

    # 定位配置
    config_path = args.config
    if not config_path and args.project_dir:
        config_path = os.path.join(args.project_dir, "工作配置.yaml")
    if not config_path:
        config_path = os.path.join(os.path.dirname(HERE), "工作配置.yaml")
    config_path = os.path.abspath(config_path)
    if not os.path.exists(config_path):
        print(f"[error] 找不到 工作配置.yaml：{config_path}")
        sys.exit(1)

    cfg = read_config(config_path)
    base = os.path.dirname(config_path)
    role_dir = cfg.get(CFG_ROLE_DIR, "")
    bg_dir = cfg.get(CFG_BG_DIR, "")
    img_out = cfg.get(CFG_IMG_OUT, "")
    if not img_out:
        img_out = os.path.join(base, "图片")
    img_out = os.path.abspath(img_out)
    os.makedirs(img_out, exist_ok=True)
    if role_dir:
        role_dir = os.path.abspath(role_dir)
    if bg_dir:
        bg_dir = os.path.abspath(bg_dir)

    storyboard = os.path.join(base, cfg.get(CFG_STORYBOARD, "提示词生成.md"))
    overview = os.path.join(base, cfg.get(CFG_OVERVIEW, "角色背景一览表.md"))
    if not os.path.exists(storyboard):
        print(f"[error] 找不到 提示词生成.md：{storyboard}")
        sys.exit(1)

    role_map = load_role_map(overview)
    print(f"[info] 角色资源目录={role_dir or '(空)'}；背景资源目录={bg_dir or '(空)'}；"
          f"图片输出目录={img_out}")
    print(f"[info] 剧情角色→资源映射 {len(role_map)} 条；一览表 {overview}")

    with open(storyboard, encoding="utf-8") as f:
        text = f.read()
    segs = parse_storyboard(text)
    print(f"[info] 解析到 {len(segs)} 个段")

    only = set(s.strip() for s in (args.only or "").split(",") if s.strip())

    comfy_output = args.comfy_output or pp.resolve_comfy_output()
    plan = []
    # 起跑前先清一次显存：防本机已有残留模型占卡导致首段显存不足
    cc.free_vram(args.comfy_url)
    for name, key, fields in segs:
        if only and key not in only:
            continue
        print(f"\n=== {name}（{key}）===")
        # 失败策略（用户要求）：单段出图（Qwen/Z-Image 子脚本）失败 →
        # 直接跳过本段、继续后续段；**不**调用 cancel_comfyui
        # （不取消 ComfyUI 任务、不清理队列），等待时间无限（由 Comfy客户端.wait 保证）。
        try:
            process_background(fields, key, storyboard, img_out, bg_dir, cfg,
                               args.comfy_url, comfy_output, args.dry_run, plan)
            process_frames(fields, key, storyboard, img_out, role_dir, role_map,
                           bg_dir, args.comfy_url, comfy_output, args.dry_run, plan,
                           frames_mode=args.frames)
        except Exception as e:
            print(f"  [失败] {key} 出图异常：{type(e).__name__}: {e}")
            print(f"  [跳过] {key} 已跳过，直接继续后续段（单独重跑：--only {key}）")
        # 段间【不】free：旧项目（run_fl2va.py 的 cc.run(total=N)）已验证——
        # 同一模型连续提交时 ComfyUI 会缓存复用、不卸载不重载，整批稳定 ~45.4GB（零叠加），
        # 既杜绝跨段 OOM、又省掉每段 ~9 分钟重载。段间 free 反而会触发「卸→载」竞态叠到 57GB 炸卡。

    # 整批结束再释放一次（兜底）。
    cc.free_vram(args.comfy_url)

    if args.dry_run:
        print("\n────────── Dry-run 计划 ──────────")
        for p in plan:
            print("  " + p)
        print(f"[dry-run] 共 {len(plan)} 个生成任务，未实际出图/回写。")
    else:
        print("\n[完成] 功能5 全部段处理完毕。")


if __name__ == "__main__":
    main()
