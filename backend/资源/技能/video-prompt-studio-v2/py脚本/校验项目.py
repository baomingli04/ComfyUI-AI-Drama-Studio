#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验项目.py — 把分散在参考文档里的「自检清单 / 红线 / 防漏写 / 铁律」固化成**只读校验器**。

为什么存在（用户原话「如果有 md 规则弄一个 py 执行比较好，就弄一个，省的每次都写脚本」）：
  分镜规则.md / 分镜转视频.md / 首尾帧生成规则.md / 调用规范.md / 初始化文档.md 里写了大量
  「自检清单」「防漏写 / 防下游读不到」「mp/seed 铁律」「R1 路由」——过去每次跑到哪一步都靠
  人肉读文档逐条核对（漏看就出岔子：world书没生成、视频没进工程目录、回写字段名写错、
  路由选反、seed 串段…）。现在这些规则**写死在脚本里**：只读
  工作配置.yaml + 角色背景一览表.md + 提示词生成.md + 磁盘产物，对照文档产出
  PASS / WARN / FAIL 报告。

  它**不连 ComfyUI、不出图、不改任何文件**——纯校验，可放在任意阶段跑（初始化后、
  分镜后、出图后、出视频后），把"人工自检"变成一条命令。

对照的文档与规则（单一可信源）：
  - 初始化文档.md          → 配置 8 中文字段齐全、指向的文件存在、图片/视频目录已建
  - 图片重命名规范.md       → 一览表三章节齐全；角色参考图文件真实存在（func5/6 路由依赖）
  - 分镜规则.md（schema/R1）→ 剧情角色清单 5 列；使用角色取自剧情角色清单；R1 路由一致；
                              视频时长≤14；场景背景图/描述二选一；首帧↔工作流联动
  - 首尾帧生成规则.md       → func5 回写四字段（场景背景图/背景图片存放位置/首帧地址/尾帧地址）
                              非空且文件存在
  - 分镜转视频.md / 调用规范.md → func6/7 生成视频地址回写且文件存在；中文字幕要求；
                              段内 视频抽卡种子 固化（mp>=0.3 复用防串段）
  - 调用规范.md 九/十       → 回写位置总表、mp/seed 铁律速查

用法：
  python 校验项目.py --config "D:/proj/工作配置.yaml"
  python 校验项目.py --config "D:/proj/工作配置.yaml" --check storyboard
  python 校验项目.py --config "D:/proj/工作配置.yaml" --only 段1,段2
  python 校验项目.py --config "D:/proj/工作配置.yaml" --report 校验报告.md
  python 校验项目.py --config "D:/proj/工作配置.yaml" --strict   # WARN 也算失败
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import 生成首尾帧与背景 as g   # read_config / load_role_map / parse_storyboard / get_role_names / _unquote / _is_yes
import 项目路径 as pp          # seg_key / _seg_blocks

# 工作配置.yaml 8 个中文字段（初始化文档.md）
CFG_FIELDS = [
    "角色资源所在目录", "背景资源所在目录", "图片输出目录", "视频输出目录",
    "角色背景一览表", "剧情生成文件", "提示词生成文件", "世界书",
]
# 指向文件的配置字段（存在性校验）
CFG_FILE_FIELDS = ["角色背景一览表", "剧情生成文件", "提示词生成文件", "世界书"]
# 指向目录的配置字段
CFG_DIR_FIELDS = ["角色资源所在目录", "背景资源所在目录", "图片输出目录", "视频输出目录"]

VIDEO_EXTS = (".mp4", ".webm", ".gif", ".mov", ".mkv")


# ── 结果收集 ───────────────────────────────────────────────────────────────
class Report:
    def __init__(self):
        self.items = []  # (level, scope, msg)
        self.n_pass = self.n_warn = self.n_fail = 0

    def add(self, level, scope, msg):
        if level == "PASS":
            self.n_pass += 1
        elif level == "WARN":
            self.n_warn += 1
        elif level == "FAIL":
            self.n_fail += 1
        self.items.append((level, scope, msg))

    def line(self, level, scope, msg):
        self.add(level, scope, msg)

    def __str__(self):
        return f"PASS={self.n_pass} WARN={self.n_warn} FAIL={self.n_fail}"


# ── 小工具 ─────────────────────────────────────────────────────────────────
def _is_filled_path(v):
    """回写字段是否已填成有效地址（而非占位文字）。"""
    v = (v or "").strip()
    if not v:
        return False
    if "占位" in v or v.startswith("（"):
        return False
    return (v.endswith(VIDEO_EXTS) or v.lower().endswith(".png")
            or "/" in v or "\\" in v)


def _read_top_seed(storyboard):
    try:
        txt = open(storyboard, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r'^(?![\t ])视频抽卡种子\s*[:：]\s*"?(\d+)"?', txt, re.M)
    return m.group(1) if m else None


def _read_seg_seed(storyboard, key):
    try:
        txt = open(storyboard, encoding="utf-8").read()
    except OSError:
        return None
    for start, end, name in pp._seg_blocks(txt):
        if pp.seg_key(name) == key:
            m = re.search(r'(?m)^[ \t]{2,}视频抽卡种子\s*[:：]\s*"?(\d+)"?', txt[start:end])
            return m.group(1) if m else None
    return None


def _chapter_exists(overview_text, title):
    return bool(re.search(r'(?m)^#{1,6}[ \t]*' + re.escape(title) + r'[ \t]*$', overview_text))


def _chapter_body(overview_text, title):
    m = re.search(r'(?m)^#{1,6}[ \t]*' + re.escape(title) + r'[ \t]*$', overview_text)
    if not m:
        return ""
    rest = overview_text[m.end():]
    # 仅在同一级（##）章节处截断；忽略章节内部的 ### 子标题（如「现有资源角色清单」
    # 下按角色名分组的「### 角色名（性别）」），与 生成剧情角色表.py 的 section_text 一致。
    nxt = re.search(r'(?m)^##[ \t]', rest)
    return rest[: nxt.start()] if nxt else rest


# ── 各层校验 ───────────────────────────────────────────────────────────────
def check_init(R, cfg, base):
    for f in CFG_FIELDS:
        if not cfg.get(f):
            R.add("FAIL", "init", f"工作配置.yaml 缺少字段「{f}」")
        else:
            R.add("PASS", "init", f"字段「{f}」= {cfg[f]}")
    # 文件字段存在性
    for f in CFG_FILE_FIELDS:
        fn = cfg.get(f)
        if fn:
            p = os.path.join(base, fn)
            if os.path.isfile(p):
                R.add("PASS", "init", f"「{f}」指向文件存在：{fn}")
            else:
                R.add("WARN", "init", f"「{f}」指向文件不存在：{fn}（可能尚未填充）")
    # 目录字段存在性
    for f in CFG_DIR_FIELDS:
        d = cfg.get(f)
        if d:
            p = os.path.join(base, d)
            if os.path.isdir(p):
                R.add("PASS", "init", f"「{f}」目录存在：{d}")
            else:
                R.add("WARN", "init", f"「{f}」目录不存在：{d}（出图/出视频前需建）")


def check_assets(R, cfg, base, overview, role_dir):
    if not os.path.isfile(overview):
        R.add("FAIL", "assets", f"角色背景一览表.md 不存在：{overview}")
        return
    text = open(overview, encoding="utf-8").read()
    for ch in ("现有资源角色清单", "背景清单", "剧情角色清单"):
        if _chapter_exists(text, ch):
            R.add("PASS", "assets", f"一览表含章节「{ch}」")
        else:
            R.add("FAIL", "assets", f"一览表缺少章节「{ch}」")
    # 剧情角色清单 5 列表格
    body = _chapter_body(text, "剧情角色清单")
    header = ""
    for line in body.splitlines():
        if line.strip().startswith("|") and "剧情角色" in line:
            header = line
            break
    if header:
        cols = [c.strip() for c in header.strip().strip("|").split("|")]
        cols = [c for c in cols if c]
        if len(cols) == 5:
            R.add("PASS", "assets", f"剧情角色清单为 5 列表格：{cols}")
        else:
            R.add("WARN", "assets", f"剧情角色清单应为 5 列，实为 {len(cols)} 列：{cols}")
    else:
        R.add("WARN", "assets", "剧情角色清单未找到 5 列表头（列数无法校验）")
    # 各清单行数 + 角色参考图文件存在性
    # 说明：现有资源角色清单 / 背景清单 按 图片重命名规范.md §六 为
    #       「- `相对路径` | 角色（性别）」列表格式；剧情角色清单 为 5 列管道表。
    #       两类都计为有效记录（旧版只数管道行，会把列表格式的清单误判为空）。
    for ch in ("现有资源角色清单", "背景清单", "剧情角色清单"):
        if not _chapter_exists(text, ch):
            continue
        b = _chapter_body(text, ch)
        rows = 0
        for line in b.splitlines():
            line = line.strip()
            if line.startswith("|"):
                # 管道表（剧情角色清单）：非表头非分隔行的数据行
                if re.match(r'\|[\s\-:|]+\|$', line):
                    continue
                if ch == "剧情角色清单" and "剧情角色" in line:
                    continue
                if len(line.strip("|").split("|")) >= 2:
                    rows += 1
            elif line.startswith("-") and "`" in line:
                # 列表条目（现有资源角色清单 / 背景清单，§六 格式）
                rows += 1
        if rows == 0:
            R.add("WARN", "assets", f"「{ch}」为空（对应功能尚未登记："
                                f"{'功能2' if ch!='剧情角色清单' else '功能3/分镜'}）")
        else:
            R.add("PASS", "assets", f"「{ch}」含 {rows} 条记录")
    # 剧情角色清单每行的匹配资源角色参考图文件存在性（func5/func6 路由硬依赖）
    role_map = g.load_role_map(overview)
    if role_map:
        missing = []
        for name, fn in role_map.items():
            if not role_dir:
                missing.append(f"{name}（缺少 角色资源所在目录）")
                continue
            if not os.path.exists(os.path.join(role_dir, fn)):
                missing.append(f"{name}→{fn}")
        if missing:
            for m in missing:
                R.add("FAIL", "assets", f"剧情角色参考图缺失：{m}（Ref2VA 路由将失败）")
        else:
            R.add("PASS", "assets", f"全部 {len(role_map)} 条剧情角色参考图文件存在")


def check_storyboard(R, cfg, base, storyboard, overview, role_dir, only=None):
    if not os.path.isfile(storyboard):
        R.add("FAIL", "storyboard", f"提示词生成.md 不存在：{storyboard}")
        return
    if not _read_top_seed(storyboard):
        R.add("WARN", "storyboard", "顶部全局字段「视频抽卡种子」缺失"
              "（mp>=0.3 成品档无种子可复用，需先跑 0.1 抽卡）")
    else:
        R.add("PASS", "storyboard", "顶部全局字段「视频抽卡种子」存在")
    role_map = g.load_role_map(overview) if os.path.isfile(overview) else {}
    text = open(storyboard, encoding="utf-8").read()
    segs = g.parse_storyboard(text)
    segs = [s for s in segs if not only or s[1] in only]
    if not segs:
        R.add("WARN", "storyboard", "提示词生成.md 未解析到任何「## 段<N>」块")
        return
    R.add("PASS", "storyboard", f"解析到 {len(segs)} 个分镜段")
    for name, key, fields in segs:
        _check_segment_schema(R, key, fields, role_map)
    if role_dir:
        role_dir = os.path.abspath(role_dir)


def _check_segment_schema(R, key, fields, role_map):
    scope = f"段[{key}]"
    gen_wf = g._unquote(fields.get("生成视频的工作流"))
    gen_img_wf = g._unquote(fields.get("生成图片的工作流"))
    first_yes = g._is_yes(fields.get("是否生成首帧图片"))
    bg_yes = g._is_yes(fields.get("是否生成背景图片"))
    dur_raw = g._unquote(fields.get("视频时长"))
    bg_img = g._unquote(fields.get("场景背景图"))
    bg_desc = g._unquote(fields.get("场景背景描述"))
    prompt = (fields.get("生成视频的提示词") or "").strip()
    use_role = fields.get("使用角色") or ""
    names = g.get_role_names(use_role)

    # 首帧/背景 是否字段取值
    if not g._unquote(fields.get("是否生成首帧图片")):
        R.add("WARN", scope, "「是否生成首帧图片」为空（应填 是/否）")
    if not g._unquote(fields.get("是否生成背景图片")):
        R.add("WARN", scope, "「是否生成背景图片」为空（应填 是/否）")

    # 主渲染工作流取值
    if not gen_wf:
        R.add("WARN", scope, "「生成视频的工作流」为空（分镜须二选一指定）")
    elif gen_wf not in ("视频-首尾帧", "视频-多参考"):
        R.add("FAIL", scope, f"「生成视频的工作流」={gen_wf!r}，必须是 视频-首尾帧/视频-多参考")

    # 视频时长
    m = re.match(r'^\s*(\d+(?:\.\d+)?)', dur_raw)
    if m:
        d = float(m.group(1))
        if d <= 14:
            R.add("PASS", scope, f"视频时长 {d}s ≤ 14")
        else:
            R.add("FAIL", scope, f"视频时长 {d}s > 14（硬上限，须拆段）")
    else:
        R.add("WARN", scope, f"视频时长无法解析：{dur_raw!r}")

    # 场景背景图 / 描述 二选一
    if bg_img and bg_desc:
        R.add("WARN", scope, "「场景背景图」与「场景背景描述」同时非空（规则：二选一，不同时填）")
    elif not bg_img and not bg_desc:
        R.add("FAIL", scope, "「场景背景图」与「场景背景描述」均为空（必须二选一指定背景）")
    else:
        R.add("PASS", scope, "背景二选一已填（图/描述其一）")
    if bg_yes and not bg_desc:
        R.add("FAIL", scope, "是否生成背景图片=是 但 场景背景描述 为空（无图可出）")
    if (not bg_yes) and not bg_img:
        R.add("FAIL", scope, "是否生成背景图片=否 但 场景背景图 为空（复用无源）")

    # 首帧 ↔ 工作流联动
    if first_yes and gen_img_wf != "图片工作流":
        R.add("FAIL", scope, f"是否生成首帧图片=是 但 生成图片的工作流={gen_img_wf!r}（应=图片工作流）")
    if (not first_yes) and gen_wf == "视频-首尾帧":
        R.add("FAIL", scope, "是否生成首帧图片=否 却选 视频-首尾帧（FL2VA 必需要首帧）")

    # 使用角色 解析 + 取自剧情角色清单
    if not names:
        if use_role.strip():
            R.add("FAIL", scope, "使用角色 块格式错误（应为「图片1: 角色名」每行一个）")
        else:
            R.add("WARN", scope, "使用角色 为空（Ref2VA 段将导致无参考图）")
    else:
        for nm in names:
            if role_map and nm not in role_map:
                R.add("FAIL", scope, f"使用角色「{nm}」不在 角色背景一览表.md 剧情角色清单"
                      f"（路由会找不到参考图）")
        R.add("PASS", scope, f"使用角色解析到 {len(names)} 个：{names}")

    # R1 路由一致性（出镜人数 × 是否含人物首尾帧）
    cnt = len(names)
    if gen_wf == "视频-首尾帧" and cnt > 2:
        R.add("FAIL", scope, f"R1 路由矛盾：出镜 {cnt} 人 > 2 却选 视频-首尾帧（应 视频-多参考）")
    elif gen_wf == "视频-多参考" and first_yes and cnt <= 2:
        R.add("WARN", scope, f"R1：{cnt} 人且首帧有人，可选 FL2VA（现用 Ref2VA，较慢但可行）")
    if first_yes and cnt > 2:
        R.add("WARN", scope, f"是否生成首帧图片=是 但出镜 {cnt} 人 > 2（图片工作流无法合成，应走 Ref2VA）")

    # 视频提示词
    if not prompt:
        R.add("FAIL", scope, "生成视频的提示词 为空")
    else:
        if gen_wf == "视频-首尾帧":
            if "Picture 1 (start)" not in prompt or "Picture 2 (end)" not in prompt:
                R.add("WARN", scope, "FL2VA 提示词缺少「Picture 1 (start)」/「Picture 2 (end)」单行锁起止格式")
        elif gen_wf == "视频-多参考":
            if "subject_definitions" not in prompt or "Subject" not in prompt:
                R.add("WARN", scope, "Ref2VA 提示词缺少六段式（subject_definitions / <Subject N>）")
        if "字幕" not in prompt:
            R.add("WARN", scope, "生成视频的提示词 未含「字幕」要求（分镜转视频 §8.2：成片须带中文字幕）")
        # 无对白段应标注全程无人物发声
        dlg = (fields.get("对话处理") or "")
        if any(k in dlg for k in ("无对白", "纯动作", "无人物发声")) and "无人物发声" not in prompt:
            R.add("WARN", scope, "对话处理表明无对白，但提示词未含「全程无人物发声」（防 H3 自发人声）")


def check_frames(R, cfg, base, storyboard, img_out, only=None):
    if not os.path.isfile(storyboard):
        R.add("FAIL", "frames", f"提示词生成.md 不存在：{storyboard}")
        return
    text = open(storyboard, encoding="utf-8").read()
    segs = g.parse_storyboard(text)
    segs = [s for s in segs if not only or s[1] in only]
    for name, key, fields in segs:
        scope = f"段[{key}]"
        first_yes = g._is_yes(fields.get("是否生成首帧图片"))
        bg_yes = g._is_yes(fields.get("是否生成背景图片"))
        if first_yes:
            for fld in ("生成图片首帧地址", "生成图片尾帧地址"):
                v = g._unquote(fields.get(fld))
                if not _is_filled_path(v):
                    R.add("FAIL", scope, f"func5 回写缺失：{fld} 为空（首帧段须有首/尾帧图）")
                elif not os.path.exists(v):
                    R.add("FAIL", scope, f"func5 回写文件不存在：{fld}={v}")
                else:
                    R.add("PASS", scope, f"func5 回写有效：{fld}")
        else:
            for fld in ("生成图片首帧地址", "生成图片尾帧地址"):
                v = g._unquote(fields.get(fld))
                if _is_filled_path(v):
                    R.add("WARN", scope, f"是否生成首帧图片=否 但 {fld} 有残留值（应清空）")
        if bg_yes:
            for fld in ("场景背景图", "背景图片存放位置"):
                v = g._unquote(fields.get(fld))
                if not _is_filled_path(v):
                    R.add("FAIL", scope, f"func5 回写缺失：{fld} 为空（背景段须有背景图）")
                elif not os.path.exists(v):
                    R.add("FAIL", scope, f"func5 回写文件不存在：{fld}={v}")
                else:
                    R.add("PASS", scope, f"func5 回写有效：{fld}")


def check_video(R, cfg, base, storyboard, vid_out, only=None):
    if not os.path.isfile(storyboard):
        R.add("FAIL", "video", f"提示词生成.md 不存在：{storyboard}")
        return
    text = open(storyboard, encoding="utf-8").read()
    segs = g.parse_storyboard(text)
    segs = [s for s in segs if not only or s[1] in only]
    for name, key, fields in segs:
        scope = f"段[{key}]"
        gen_wf = g._unquote(fields.get("生成视频的工作流"))
        if gen_wf not in ("视频-首尾帧", "视频-多参考"):
            continue  # 非视频段不校验
        addr = g._unquote(fields.get("生成视频地址"))
        if not _is_filled_path(addr):
            R.add("FAIL", scope, "func6/7 回写缺失：生成视频地址 为空/占位（成片未落盘或漏回写）")
        elif not os.path.exists(addr):
            R.add("FAIL", scope, f"func6/7 回写文件不存在：生成视频地址={addr}")
        else:
            R.add("PASS", scope, f"func6/7 回写有效：生成视频地址={os.path.basename(addr)}")
        # 段内抽卡种子固化（mp>=0.3 复用防串段）
        if _is_filled_path(addr):
            seg_seed = _read_seg_seed(storyboard, key)
            if not seg_seed:
                R.add("WARN", scope, "段内「视频抽卡种子」未固化（若以 mp>=0.3 重跑本段将重新随机抽卡）")
            else:
                R.add("PASS", scope, f"段内 视频抽卡种子 已固化={seg_seed}")


# ── 入口 ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="项目一致性只读校验（文档规则固化）")
    ap.add_argument("--config", required=True, help="工作配置.yaml")
    ap.add_argument("--check", default="all",
                    choices=["init", "assets", "storyboard", "frames", "video", "all"],
                    help="只跑指定层（默认 all）")
    ap.add_argument("--only", default=None, help="只校验指定段，逗号分隔（如对 storyboard/frames/video 生效）")
    ap.add_argument("--report", default=None, help="把报告写成 markdown 到该路径")
    ap.add_argument("--strict", action="store_true", help="WARN 也计为失败（退出码 1）")
    args = ap.parse_args()

    config_path = os.path.abspath(args.config)
    if not os.path.isfile(config_path):
        print(f"[FAIL] 找不到 工作配置.yaml：{config_path}")
        sys.exit(1)

    cfg = g.read_config(config_path)
    base = os.path.dirname(config_path)
    role_dir = cfg.get("角色资源所在目录")
    role_dir = os.path.abspath(role_dir) if role_dir else ""
    img_out = cfg.get("图片输出目录") or os.path.join(base, "图片")
    img_out = os.path.abspath(img_out)
    vid_out = cfg.get("视频输出目录") or os.path.join(base, "视频")
    vid_out = os.path.abspath(vid_out)
    overview = os.path.join(base, cfg.get("角色背景一览表", "角色背景一览表.md"))
    storyboard = os.path.join(base, cfg.get("提示词生成文件", "提示词生成.md"))

    R = Report()
    only = set(s.strip() for s in (args.only or "").split(",") if s.strip())

    # init / assets 与段无关
    if args.check in ("init", "all"):
        check_init(R, cfg, base)
    if args.check in ("assets", "all"):
        check_assets(R, cfg, base, overview, role_dir)
    if args.check in ("storyboard", "all"):
        check_storyboard(R, cfg, base, storyboard, overview, role_dir, only)
    if args.check in ("frames", "all"):
        check_frames(R, cfg, base, storyboard, img_out, only)
    if args.check in ("video", "all"):
        check_video(R, cfg, base, storyboard, vid_out, only)

    # 渲染
    print("\n══════════════════ 项目校验报告 ════════════════")
    print(f"配置: {config_path}")
    print(f"工作目录: {base}")
    print(f"校验层: {args.check}   段过滤: {args.only or '全部'}")
    print("─" * 60)
    cur = None
    for level, scope, msg in R.items:
        if scope != cur:
            cur = scope
            print(f"\n[{scope}]")
        mark = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(level, "·")
        print(f"  {mark} {msg}")
    print("─" * 60)
    print(f"汇总：{R}")
    verdict = "OK" if (R.n_fail == 0 and (not args.strict or R.n_warn == 0)) else "有问题"
    print(f"结论：{verdict}")

    if args.report:
        _write_report(args.report, config_path, base, args.check, args.only, R)
        print(f"报告已写入：{args.report}")

    sys.exit(1 if (R.n_fail > 0 or (args.strict and R.n_warn > 0)) else 0)


def _write_report(path, config_path, base, check, only, R):
    lines = []
    lines.append("# 项目校验报告\n")
    lines.append(f"- 配置：`{config_path}`")
    lines.append(f"- 工作目录：`{base}`")
    lines.append(f"- 校验层：`{check}`　段过滤：`{only or '全部'}`")
    lines.append(f"- 汇总：**PASS={R.n_pass}　WARN={R.n_warn}　FAIL={R.n_fail}**\n")
    lines.append("| 级别 | 范围 | 说明 |")
    lines.append("|---|---|---|")
    for level, scope, msg in R.items:
        lines.append(f"| {level} | {scope} | {msg} |")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
