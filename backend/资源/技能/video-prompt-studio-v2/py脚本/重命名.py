#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重命名.py — 功能 2：角色 / 背景图批量识别重命名 + 重建「角色背景一览表.md」资源清单。

【契约】严格按 参考文档/图片重命名规范.md（一～七）执行；规则以该文档为准，不另立。

【默认行为：逐张识别 → 按规则重命名】
  · 角色图：未以「单一视图_ / 多角度视图_」开头的，调用识别接口提取 8 字段 →
    重命名为 `{视图}_{年龄}_{服饰}-{服饰颜色}_{肤色}_{姿势}_{发型}_{发色}_{背景}.png`；
    已按规范命名的直接跳过（幂等，可断点续跑）。
  · 背景图：未以 `_背景.<ext>` 结尾的，判定场景描述后重命名为 `{场景描述}_背景.<ext>`：
      - 若文件 stem 已是可读中文场景描述（含 CJK、且非 ScreenShot/IMG/时间戳），
        视为已含场景描述，仅补 `_背景` 后缀、不再识别（尊重用户手起的场景名）；
      - 否则调用识别接口提取场景描述（规范 §三）。
  · 每张识别成功的图，另存 `{原名base}_反推.txt` 存档（--no-txt 关闭）。
  · 全部角色 / 背景写入 角色背景一览表.md（已存在条目跳过，不重复）。

【识别后端与回退】
  · 主用 图片识别端点（--backend，默认 http://192.168.31.131:8488，llama.cpp 视觉）；
  · 连续识别失败达 --consecutive 次（默认 3），后续统一转 ComfyUI 图片反推工作流改名；
  · 单图识别失败（字段不足）→ 保留原名跳过（规范 §五）。

【回写】只覆盖「现有资源角色清单 / 背景清单」两节，其余节（剧情角色清单 / 剧情角色详情表）原样保留。

【传参】详见 图片重命名规范.md §七。
  --config PATH       工作配置.yaml（读取角色/背景目录 + 项目目录）
  --dir SPEC          可重复；用户直接指定目录，支持 角色:<路径> / 背景:<路径>。
                      指定子集时【只更新该子集涉及的角色/背景子块】，其余子块原样保留，
                      不会冲掉整节一览表（整节仍基于完整 role_dir/bg_dir 重建）。
  --project-dir PATH  一览表所在目录；默认取 --config 所在目录
  --no-txt            不写 {原名}_反推.txt 存档
  --consecutive N     连续识别失败几次转 ComfyUI（默认 3）
  --no-fallback       远程失败不回退 ComfyUI
  --timeout N         单图识别超时秒数（默认 120）
  --busy-threshold N  远程忙闲阈值（默认 None）
  --backend-model S   远程识别模型名（默认 None）
  --comfy-url URL     默认 http://127.0.0.1:8188
  --backend URL       远程视觉端点，默认 http://192.168.31.131:8488
  --dry-run           只预览改名 / 清单，不改文件、不写一览表
"""

import argparse
import os
import re
import sys
import tempfile

# ── 角色 8 字段（顺序即文件名中紧随「视图」之后的顺序）──
FIELDS = ["年龄", "服饰", "服饰颜色", "肤色", "姿势", "发型", "发色", "背景"]

STRUCT_PROMPT = (
    "请仔细观察这张人物图片，严格按以下 8 个字段、每行一个、"
    "格式为「字段名：值」输出，不要编号、不要解释、不要输出其他任何内容。\n"
    "重要：每个字段都必须填【具体、可区分】的描述，严禁用「健康/正常/自然/普通」"
    "等无信息量的套话填充任何字段。\n"
    "年龄：（同时标明性别，如「年轻女性」「中年男子」）\n"
    "服饰：（服装大类，如「红衣」「盔甲」「现代西装」）\n"
    "服饰颜色：（该服装的颜色，如「红色」「银白」）\n"
    "肤色：（必须从下列词中取【最贴切的一个】描述：白皙 / 偏白 / 偏黄 / 小麦色 / "
    "古铜色 / 深棕 / 黝黑；可加简短修饰，如「偏黄的小麦色」。严禁只写"
    "「健康肤色」「正常肤色」「自然肤色」「普通肤色」等无区分度词语）\n"
    "姿势：（动作/姿态，如「持刃戒备」「双手抱胸」）\n"
    "发型：（如「长直发」「短寸」）\n"
    "发色：（头发颜色，如「乌黑」「金发」）\n"
    "背景：（场景环境，如「古庙正殿夜景」）\n"
)

BACKGROUND_PROMPT = (
    "请观察这张图片的场景环境，严格按一行输出，格式「场景描述：值」，"
    "不要编号、不要解释、不要输出其他任何内容。\n"
    "场景描述：（用简短中文描述环境/场景，如「古庙正殿夜景」「樱花树下庭院」）\n"
)

IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
MULTI_VIEW_MARKERS = ("三视图", "多角度", "多视图", "三视")
ROLE_DONE = ("单一视图_", "多角度视图_")
# 背景已规范：任意大小写后缀，且文件名以 _背景. 结尾
BG_DONE_RE = re.compile(r"_背景\.(png|jpe?g|webp|bmp)$", re.I)

# 无意义文件名（截图/导出/时间戳），需走识别
_MEANINGLESS_RE = re.compile(
    r"(?i)(screenshot|screen_?shot|img_?\d*|dji_|wx_|mmexport|捕获|capture)"
)


def looks_like_scene_name(stem):
    """背景 stem 是否已是有意义的中文场景描述（无需识别，直接补 _背景）。"""
    if not re.search(r"[一-鿿]", stem):  # 无中文字符 → 无意义
        return False
    if _MEANINGLESS_RE.search(stem):
        return False
    if re.fullmatch(r"\d{6,}", stem):  # 纯数字时间戳
        return False
    return True


# ── 单实例锁：防止并发多实例往 ComfyUI 队列塞任务堆积成孤儿 ──
LOCK_PATH = os.path.join(tempfile.gettempdir(), "vps_rename.lock")


def _pid_alive(pid):
    if sys.platform == "win32":
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            h = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
            if h == 0:
                return False
            kernel32.CloseHandle(h)
            return True
        except Exception:
            return True
    else:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, FileNotFoundError):
            return False
        except OSError:
            return True


def acquire_lock():
    if os.path.exists(LOCK_PATH):
        old_pid = None
        try:
            with open(LOCK_PATH, "r") as f:
                old_pid = int(f.read().strip())
        except Exception:
            pass
        if old_pid and _pid_alive(old_pid):
            print(f"[单实例锁] 已有 重命名.py 实例在运行 (PID={old_pid})，本实例退出。")
            sys.exit(1)
        else:
            try:
                os.remove(LOCK_PATH)
            except OSError:
                pass
    try:
        with open(LOCK_PATH, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def release_lock():
    try:
        if os.path.exists(LOCK_PATH):
            os.remove(LOCK_PATH)
    except OSError:
        pass


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


def collect_dirs(args):
    """返回 [(dir_path, type)]，type ∈ {'角色','背景'}。"""
    result = []
    cfg = read_config(args.config) if args.config else {}
    role_dir = os.path.abspath(cfg["角色资源所在目录"]) if cfg.get("角色资源所在目录") else None
    bg_dir = os.path.abspath(cfg["背景资源所在目录"]) if cfg.get("背景资源所在目录") else None

    for spec in (args.dir or []):
        typ = "角色"
        p = spec
        if spec.startswith("角色:") or spec.startswith("背景:"):
            typ, _, p = spec.partition(":")
            typ = typ.strip()
            p = p.strip()
        p = os.path.abspath(p)
        if role_dir and os.path.abspath(p) == role_dir:
            typ = "角色"
        elif bg_dir and os.path.abspath(p) == bg_dir:
            typ = "背景"
        result.append((p, typ))

    if role_dir and not any(p == role_dir for p, _ in result):
        result.append((role_dir, "角色"))
    if bg_dir and not any(p == bg_dir for p, _ in result):
        result.append((bg_dir, "背景"))

    if not result:
        print("[error] 未指定任何目录：请用 --dir 或 --config 提供。")
        sys.exit(1)
    return result


def overview_path(args, cfg):
    if args.project_dir:
        return os.path.join(args.project_dir, "角色背景一览表.md")
    if args.config:
        return os.path.join(os.path.dirname(os.path.abspath(args.config)), "角色背景一览表.md")
    rd = cfg.get("角色资源所在目录")
    bd = cfg.get("背景资源所在目录")
    if rd:
        return os.path.join(os.path.dirname(os.path.abspath(rd)), "角色背景一览表.md")
    if bd:
        return os.path.join(os.path.dirname(os.path.abspath(bd)), "角色背景一览表.md")
    return "角色背景一览表.md"


def role_identity(role_root, filepath):
    """从 角色根目录 推断 (性别, 角色名)。目录布局：<root>/男/<角色名>/*.png。"""
    d = os.path.dirname(filepath)
    rel = os.path.relpath(d, role_root)
    parts = rel.split(os.sep) if rel != "." else []
    gender = ""
    char = ""
    if parts and parts[0] in ("男", "女"):
        gender = parts[0]
        if len(parts) > 1:
            char = parts[1]
    return gender, char


def sanitize(s, maxlen=20):
    s = (s or "").strip()
    s = re.sub(r'[\\/:*?"<>|\r\n\t；　、，,（）()\[\]【】]', "", s)
    s = s.replace("—", "").replace("–", "").replace(" ", "")
    return s[:maxlen]


def detect_view(orig_base):
    for mk in MULTI_VIEW_MARKERS:
        if mk in orig_base:
            return "多角度视图"
    return "单一视图"


def parse_fields(text):
    fields = {}
    for name in FIELDS:
        m = re.search(rf"(?m)^{re.escape(name)}\s*[:：]\s*(.*)$", text)
        fields[name] = m.group(1).strip() if m else ""
    return fields


def parse_scene(text):
    m = re.search(r"(?m)^场景描述\s*[:：]\s*(.*)$", text)
    return m.group(1).strip() if m else ""


def build_role_name(fields, view):
    v = sanitize(view) or "单一视图"
    age = sanitize(fields["年龄"]) or "未知"
    cloth = sanitize(fields["服饰"]) or "未知"
    cloth_color = sanitize(fields["服饰颜色"]) or "未知"
    skin = sanitize(fields["肤色"]) or "未知"
    pose = sanitize(fields["姿势"]) or "未知"
    hair = sanitize(fields["发型"]) or "未知"
    hair_color = sanitize(fields["发色"]) or "未知"
    bg = sanitize(fields["背景"]) or "未知"
    return f"{v}_{age}_{cloth}-{cloth_color}_{skin}_{pose}_{hair}_{hair_color}_{bg}"


def build_bg_name(scene):
    return (sanitize(scene) or "未知") + "_背景"


def _unique_target(target, existing):
    if target not in existing:
        return target
    base, ext = os.path.splitext(target)
    i = 2
    while f"{base}_{i}{ext}" in existing:
        i += 1
    return f"{base}_{i}{ext}"


def _replace_section(path, title, body_lines):
    """用 body_lines 整体替换一览表中 `## title` 这一节（含其原有正文），
    保留其它节。不存在则追加到末尾。"""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# 角色背景一览表\n"
    lines = content.splitlines()
    idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^##\s+" + re.escape(title) + r"\s*$", ln):
            idx = i
            break
    if idx is None:
        new_block = "\n\n## " + title + "\n" + "\n".join(body_lines) + "\n"
        content = content.rstrip("\n") + new_block
    else:
        end = len(lines)
        for j in range(idx + 1, len(lines)):
            if re.match(r"^##\s+", lines[j]):
                end = j
                break
        new_section = ["## " + title] + body_lines
        lines = lines[:idx] + new_section + lines[end:]
        content = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_blocks(path, title):
    """读取一览表某节下按 `### label` 切分的子块，返回 {label: [内容行]}（不含 ### 行）。
    若节内无 ### 子标题（如背景清单，扁平 bullet），整体作为 key='' 返回。"""
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    m = re.search(r"(?m)^##\s+" + re.escape(title) + r"\s*$", text)
    if not m:
        return {}
    rest = text[m.end():]
    nxt = re.search(r"(?m)^##\s+", rest)
    if nxt:
        rest = rest[:nxt.start()]
    blocks = {}
    cur = ""
    for ln in rest.splitlines():
        h = re.match(r"^###\s+(.*?)\s*$", ln)
        if h:
            cur = h.group(1)
            blocks[cur] = []
        else:
            blocks.setdefault(cur, []).append(ln)
    return blocks


# ── 视觉反推后端 ──
def _load_recognizer(args, force_comfy=False):
    try:
        import 视觉识别 as vr
    except Exception as e:
        print(f"[warn] 视觉后端加载失败，跳过视觉改名：{e}")
        return None
    return vr.VisionRecognizer(
        remote_url=None if force_comfy else args.backend,
        remote_model=args.backend_model,
        comfy_url=args.comfy_url,
        timeout=args.timeout,
        busy_threshold=args.busy_threshold,
        no_fallback=args.no_fallback,
    )


def process_image(path, typ, args, state):
    """识别单张图 → 改名 + 写 _反推.txt。返回新文件名或 None（跳过/失败）。"""
    base, ext = os.path.splitext(os.path.basename(path))
    ext = ext.lower()
    directory = os.path.dirname(path)

    # 背景：stem 已是中文场景描述则直接补 _背景，不再识别（尊重用户手起名）
    if typ == "背景" and not BG_DONE_RE.search(os.path.basename(path)):
        stem = os.path.splitext(os.path.basename(path))[0]
        if looks_like_scene_name(stem):
            existing = set(os.listdir(directory))
            target = _unique_target(sanitize(stem) + "_背景" + ext, existing)
            if target != os.path.basename(path):
                if not args.dry_run:
                    os.rename(path, os.path.join(directory, target))
                print(f"  [ok] {os.path.basename(path)}  ->  {target}（沿用场景名，未识别）")
            return target

    # 其余情况走识别接口
    rec = state["rec"]
    if rec is None:
        rec = _load_recognizer(args)
        state["rec"] = rec
    if rec is None:
        return None
    try:
        if typ == "背景":
            text, _ = rec.recognize(path, BACKGROUND_PROMPT)
            scene = parse_scene(text)
            if not scene:
                return None
            target_base = build_bg_name(scene)
        else:
            text, _ = rec.recognize(path, STRUCT_PROMPT)
            fields = parse_fields(text)
            if sum(1 for f in FIELDS if fields[f]) < 2:
                return None
            target_base = build_role_name(fields, detect_view(base))
    except Exception as e:
        state["consec"] += 1
        if state["consec"] >= args.consecutive and not state["force_comfy"]:
            state["force_comfy"] = True
            state["rec"] = _load_recognizer(args, force_comfy=True)
            print(f"[info] 连续失败 {state['consec']} 次，后续统一改用 ComfyUI 反推改名。")
        print(f"  [warn] 识别失败，跳过 {os.path.basename(path)}: {e}")
        return None
    state["consec"] = 0  # 成功则重置计数

    existing = set(os.listdir(directory))
    target = _unique_target(target_base + ext, existing)
    if args.dry_run:
        print(f"  [dry] {os.path.basename(path)}  ->  {target}")
        return target
    try:
        os.rename(path, os.path.join(directory, target))
    except OSError as e:
        print(f"  [warn] 重命名失败，跳过 {os.path.basename(path)}: {e}")
        return None
    print(f"  [ok]  {os.path.basename(path)}  ->  {target}")
    # 写 _反推.txt 存档（除非 --no-txt）
    if not args.no_txt:
        txt_path = os.path.join(directory, base + "_反推.txt")
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError:
            pass
    return target


def rebuild_role_inventory(role_dir, ov_path, args, state, only=None):
    """按 男/女/<角色名> 目录树重建「现有资源角色清单」。
    未规范的角色图默认识别改名；已规范的跳过。每行带相对路径 + 身份（供下游性别匹配追溯）。
    only: 可选 [子目录绝对路径列表]；若给定，只重新处理这些子目录下的角色，
          其余角色子块从现有一览表原样保留（merge，不整体冲掉整节）。"""
    only_norm = [os.path.abspath(p) for p in (only or [])]

    def _in_only(full):
        if not only_norm:
            return True
        a = os.path.abspath(full)
        return any(a == p or a.startswith(p + os.sep) for p in only_norm)

    groups = {}
    for root, _d, names in os.walk(role_dir):
        for fn in sorted(names):
            if not fn.lower().endswith(IMG_EXTS) or not os.path.isfile(os.path.join(root, fn)):
                continue
            full = os.path.join(root, fn)
            if not _in_only(full):
                continue
            rel = os.path.relpath(full, role_dir).replace(os.sep, "/")
            gender, char = role_identity(role_dir, full)
            groups.setdefault((gender, char), []).append((rel, full, fn))
            # 默认识别改名（未规范的）；--no-rename 时仅登记不改名
            if not fn.startswith(ROLE_DONE) and not args.no_rename:
                new = process_image(full, "角色", args, state)
                if new and new != fn:
                    rel = os.path.relpath(os.path.join(os.path.dirname(full), new), role_dir).replace(os.sep, "/")
                    key = (gender, char)
                    groups[key] = [(r, f, n) for (r, f, n) in groups[key] if f != full]
                    groups[key].append((rel, os.path.join(os.path.dirname(full), new), new))

    existing_blocks = _read_blocks(ov_path, "现有资源角色清单")

    body = [
        "（由 重命名.py 自动生成；按真实目录 `火影\\真人版加生提示词\\角色` 的 男/女/角色子目录 分组；",
        "每行：`- `相对路径` | 角色（性别）`；相对路径即文件所在目录（含 男/女/角色名），",
        "供「生成剧情角色表.py」按性别匹配；已按 8 字段规范命名的图也照此登记）",
        "",
    ]
    counters = {"男": 0, "女": 0, "其它": 0}
    gen_labels = set()
    for gender in ("男", "女", "其它"):
        for (g, c) in sorted(groups.keys()):
            if (g if g in ("男", "女") else "其它") != gender:
                continue
            label = f"{c}（{g}）" if c else f"未归类（{g}）"
            gen_labels.add(label)
            body.append(f"### {label}")
            for rel, _f, _n in sorted(groups[(g, c)]):
                body.append(f"- `{rel}` | {label}")
            body.append("")
            counters[gender] += len(groups[(g, c)])

    # only 模式：把未处理的角色子块（在现有一览表但不在本次 groups）原样补回，保持男/女/其它顺序
    if only_norm:
        for gender in ("男", "女", "其它"):
            for label, lines in existing_blocks.items():
                if label in gen_labels:
                    continue
                g = "男" if "（男）" in label else ("女" if "（女）" in label else "其它")
                if g != gender:
                    continue
                body.append(f"### {label}")
                for ln in lines:
                    if ln.strip():
                        body.append(ln)
                body.append("")
                counters[gender] += len([ln for ln in lines if ln.strip().startswith("- ")])

    if args.dry_run:
        total = counters["男"] + counters["女"] + counters["其它"]
        print(f"[dry] 现有资源角色清单：将更新 {len(groups)} 个角色子块，"
              f"全量登记 男 {counters['男']} / 女 {counters['女']} / 其它 {counters['其它']} 张；不写一览表")
        return

    _replace_section(ov_path, "现有资源角色清单", body)
    print(f"[角色] 分组 {len(groups)} 个角色（子集更新），"
          f"全量登记 男 {counters['男']} / 女 {counters['女']} / 其它 {counters['其它']} 张 @ {role_dir}")


def rebuild_bg_inventory(bg_dir, ov_path, args, state, only=None):
    """真实场景背景：未规范的识别/沿用场景名重命名为 `{场景描述}_背景.<ext>` 并登记。
    only: 可选 [子目录绝对路径列表]；子集时仅更新这些背景，其余背景行从现有一览表原样保留。"""
    only_norm = [os.path.abspath(p) for p in (only or [])]

    def _in_only(full):
        if not only_norm:
            return True
        a = os.path.abspath(full)
        return any(a == p or a.startswith(p + os.sep) for p in only_norm)

    entries = []
    renamed = 0
    existing = set(os.listdir(bg_dir))
    for fn in sorted(existing):
        full = os.path.join(bg_dir, fn)
        if not os.path.isfile(full) or not fn.lower().endswith(IMG_EXTS):
            continue
        if not _in_only(full):
            continue
        if BG_DONE_RE.search(fn):
            new_fn = fn  # 已符合规范
        elif args.no_rename:
            new_fn = fn  # 仅登记不改名
        else:
            new = process_image(full, "背景", args, state)
            new_fn = new if new else fn
            if new and new != fn:
                renamed += 1
                existing.discard(fn)
                existing.add(new)
        scene = re.sub(r"_背景$", "", os.path.splitext(new_fn)[0])
        entries.append((new_fn, scene))

    body = [
        "（由 重命名.py 自动生成；按真实目录 `火影\\真实场景`；背景命名 `{场景描述}_背景.<ext>`，",
        "场景描述来自识别接口或沿用已有中文场景名；已符合规范者跳过）",
        "",
    ]
    for new_fn, scene in entries:
        body.append(f"- `{new_fn}` | {scene} 场景背景")

    # only 模式：把未处理的背景行（在现有一览表但不在本次 entries）原样补回
    if only_norm:
        handled = {e[0] for e in entries}
        if os.path.exists(ov_path):
            txt = open(ov_path, encoding="utf-8").read()
            m = re.search(r"(?m)^##\s+背景清单\s*$", txt)
            if m:
                rest = txt[m.end():]
                nxt = re.search(r"(?m)^##\s+", rest)
                if nxt:
                    rest = rest[:nxt.start()]
                for ln in rest.splitlines():
                    if not ln.strip().startswith("- "):
                        continue
                    fn = re.search(r"`([^`]+)`", ln)
                    if fn and fn.group(1) not in handled:
                        body.append(ln)

    if args.dry_run:
        print(f"[dry] 背景清单：将更新 {len(entries)} 张（重命名 {renamed}），不写一览表")
        return

    _replace_section(ov_path, "背景清单", body)
    print(f"[背景] 重命名 {renamed} 张，登记 {len(entries)} 张 @ {bg_dir}")


def main():
    acquire_lock()
    import atexit
    atexit.register(release_lock)

    ap = argparse.ArgumentParser(description="功能2：批量识别重命名 + 重建角色/背景资源清单")
    ap.add_argument("--config", default=None, help="工作配置.yaml（读取角色/背景目录 + 项目目录）")
    ap.add_argument("--dir", action="append", default=[],
                    help="用户指定目录；可重复。支持 角色:<路径> / 背景:<路径> 前缀")
    ap.add_argument("--project-dir", default=None, help="角色背景一览表.md 所在目录")
    ap.add_argument("--no-txt", action="store_true", help="不写 {原名}_反推.txt 存档")
    ap.add_argument("--consecutive", type=int, default=3, help="连续识别失败几次转 ComfyUI（默认3）")
    ap.add_argument("--no-fallback", action="store_true", help="远程失败不回退 ComfyUI")
    ap.add_argument("--timeout", type=int, default=120, help="单图识别超时秒数（默认120）")
    ap.add_argument("--busy-threshold", type=int, default=None, help="远程忙闲阈值（默认None）")
    ap.add_argument("--backend-model", default=None, help="远程识别模型名（默认None）")
    ap.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    ap.add_argument("--backend", default="http://192.168.31.131:8488", help="远程视觉端点")
    ap.add_argument("--dry-run", action="store_true", help="只预览改名/清单，不改文件、不写一览表")
    ap.add_argument("--no-rename", action="store_true",
                    help="仅按目录树重建两节清单、不调用识别接口改名（快速刷新一览表，不改名）")
    args = ap.parse_args()

    state = {"rec": None, "consec": 0, "force_comfy": False}

    cfg = read_config(args.config) if args.config else {}
    role_dir = os.path.abspath(cfg["角色资源所在目录"]) if cfg.get("角色资源所在目录") else None
    bg_dir = os.path.abspath(cfg["背景资源所在目录"]) if cfg.get("背景资源所在目录") else None

    # 用户 --dir 指定的子集 → 仅作过滤器（only），不再当根目录
    only_role, only_bg = [], []
    for spec in (args.dir or []):
        typ, _, p = ("角色", "", spec)
        if spec.startswith("角色:") or spec.startswith("背景:"):
            typ, _, p = spec.partition(":")
            typ = typ.strip()
            p = p.strip()
        p = os.path.abspath(p)
        (only_bg if typ == "背景" else only_role).append(p)
    # 未给 --dir 或给的正是完整根 → 全量（only=None）
    if not only_role or (role_dir and any(p == role_dir for p in only_role)):
        only_role = None
    if not only_bg or (bg_dir and any(p == bg_dir for p in only_bg)):
        only_bg = None

    ov_path = overview_path(args, cfg)
    print(f"[info] 一览表路径: {ov_path}")
    if only_role:
        print(f"[info] 角色子集过滤: {len(only_role)} 个目录（仅更新这些角色，其余保留）")
    if only_bg:
        print(f"[info] 背景子集过滤: {len(only_bg)} 个目录")

    if role_dir:
        rebuild_role_inventory(role_dir, ov_path, args, state, only=only_role)
    if bg_dir:
        rebuild_bg_inventory(bg_dir, ov_path, args, state, only=only_bg)

    print("[done] 清单已重建（仅覆盖 现有资源角色清单 / 背景清单 两节）。")


if __name__ == "__main__":
    main()
