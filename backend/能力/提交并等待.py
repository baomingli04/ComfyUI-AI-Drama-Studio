# -*- coding: utf-8 -*-
"""提交并等待：Comfy/LLM 任务的统一执行入口。

职责（docs/08 锁定）：
- Comfy 同时只跑一条；开始时间 = Comfy queue 显示 running 的时刻。
- 状态机：已创建 → 已提交 → 排队中/生成中 → 成功/失败/中断/已取消。
- 全过程追加写该任务日志文件（资源/日志/task_<id>.log）。
- 能被取消打断（interrupt）；超时/连不上 → 中断。
- 不含业务提示词；工作流填充在各能力模块的 构建工作流()。

对外：
- 启动执行器()：Django 启动时调一次，拉起 Comfy / LLM 两个工作线程。
- 入队(任务id)：任务提交后唤醒工作线程。
- 标记取消(任务实例)：取消接口调用。
"""
import json
import threading
import time
import traceback
import urllib.error
import urllib.request


# 内网直连：本机环境变量可能带 HTTP_PROXY（沙箱代理），访问 Comfy/LLM 必须绕开，
# 否则代理会间歇性掐断连接（10053/10054/503），任务被误判中断。
直连opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils import timezone

from 接口.models.task import task
from 接口.models.模型配置 import 模型配置

Comfy类型 = ('生成图片', '文生图8K',
             '三图编辑一致版', '多图编辑多人合并版', '动漫转真人',
             '人物替换',
             '首尾帧', '参考生视频', '去水印', '二采重绘', '文生视频',
             '多参考生视频', '首尾帧生视频',
             '视频生视频', '参考视频生视频', '加速版生视频',
             '二采加速生视频',
            '外部分组图生视频',
            '外部分组多参考生视频',
            '导演台全能')
LLM类型 = ('文本回复', '图片解析')

总超时秒 = 3600          # 单任务从提交到终态的最大等待
轮询间隔秒 = 1.0

# 两张图时按 Comfy 返回文件名的放大标记分流：带标记的是放大图（产物图片2），
# 不带的是原图/成品（产物图片）。文生图8K 用 _4x（1x + 4x 两张），
# 多图编辑多人合并版 / 三图编辑一致版 的 SeedVR2 分块放大用 _hd。
放大图标记 = ('_4x', '_hd')

_唤醒 = threading.Event()
_已启动 = False
_锁 = threading.Lock()


# ---------------------------------------------------------------- 基础

def 取模型配置():
    """读模型配置单行；没有则建空行。"""
    实例 = 模型配置.objects.first()
    if 实例 is None:
        实例 = 模型配置.objects.create(更新时间=timezone.now())
    return 实例


def 补协议(地址):
    地址 = (地址 or '').strip()
    if 地址 and not 地址.startswith('http'):
        地址 = 'http://' + 地址
    return 地址.rstrip('/')


def 记日志(任务id, 文本):
    """追加一行到该任务的日志文件（前端日志弹窗只展示这份文件）。"""
    行 = time.strftime('%Y-%m-%d %H:%M:%S ') + str(文本)
    try:
        目录 = Path(settings.LOG_DIR)
        目录.mkdir(parents=True, exist_ok=True)
        路径 = 目录 / ('task_%s.log' % 任务id)
        with open(路径, 'a', encoding='utf-8') as f:
            f.write(行 + '\n')
        from django.db.models import Q
        task.objects.filter(id=任务id).filter(Q(日志路径__isnull=True) | Q(日志路径='')).update(
            日志路径=str(路径)
        )
    except Exception:
        traceback.print_exc()


def _置状态(任务id, 状态, **字段):
    任务 = task.objects.filter(id=任务id).first()
    if 任务 is None:
        return None
    if 任务.状态 == '已取消' and 状态 != '已取消':
        return 任务  # 已取消的任务不再改状态
    for k, v in 字段.items():
        setattr(任务, k, v)
    if 任务.状态 != 状态:
        旧 = 任务.状态
        任务.状态 = 状态
        记日志(任务id, '[状态] %s -> %s' % (旧, 状态))
    任务.save()
    return 任务


def _取错误位置(异常):
    tb = traceback.extract_tb(异常.__traceback__)
    if tb:
        帧 = tb[-1]
        return {'file': 帧.filename, 'line': 帧.lineno, 'func': 帧.name}
    return {'file': __file__, 'line': 0, 'func': '未知'}


def _末尾(文本, 上限):
    """取末尾若干字符。长报错的真正原因通常压在最后（ffmpeg 之类前面全是 banner）。"""
    文本 = (文本 or '').strip()
    if len(文本) <= 上限:
        return 文本
    return '…（前面 %d 字省略）\n' % (len(文本) - 上限) + 文本[-上限:]


def _取执行错误(状态信息):
    """从 history 的 status.messages 里挖出 execution_error，返回 {'摘要', '日志'}。

    ComfyUI 执行失败时，原因在 messages 的 execution_error 事件里，含 node_id /
    node_type / exception_type / exception_message / traceback。只判 status_str='error'
    而不读这个事件，就只会得到一句「history error」，看不出错在哪个节点、为什么错。
    """
    for 名, 体 in (状态信息.get('messages') or []):
        if 名 == 'execution_error' and isinstance(体, dict):
            节点 = '节点 %s (%s)' % (体.get('node_id') or '?', 体.get('node_type') or '?')
            类型 = 体.get('exception_type') or 'Exception'
            消息 = (体.get('exception_message') or '').strip()
            # ComfyUI 的 traceback 是「一行一个元素的列表」，不是一整个字符串
            堆栈 = 体.get('traceback') or ''
            if isinstance(堆栈, list):
                堆栈 = ''.join(str(x) for x in 堆栈)
            堆栈 = 堆栈.strip()

            日志 = '%s 抛 %s：\n%s' % (节点, 类型, 消息)
            if 堆栈:
                日志 += '\n--- traceback ---\n' + 堆栈
            return {'摘要': '%s 抛 %s：%s' % (节点, 类型, _末尾(消息, 500) or '（无异常信息）'),
                    '日志': 日志}
    return {'摘要': 'ComfyUI 执行出错（history error，且 history 里没有 execution_error 详情）',
            '日志': 'history error（history 里没有 execution_error 详情，可能不是执行期报错）'}


def 标记失败(任务id, 异常):
    位置 = _取错误位置(异常)
    记日志(任务id, '[失败] %s | %s:%s %s' % (异常, 位置['file'], 位置['line'], 位置['func']))
    _置状态(任务id, '失败',
            错误信息=str(异常), 错误文件=位置['file'],
            错误行号=位置['line'], 错误函数=位置['func'], 结束时间=timezone.now())


def 标记取消(任务id):
    记日志(任务id, '[取消] 用户取消')
    _置状态(任务id, '已取消', 结束时间=timezone.now())


def 标记中断(任务id, 原因):
    记日志(任务id, '[中断] ' + 原因)
    _置状态(任务id, '中断', 错误信息=原因, 结束时间=timezone.now())


def 标记取消接口入口(任务):
    """给取消控制器用：排队中的直接取消；生成中的标记后由工作线程 interrupt。"""
    if 任务.状态 == '已创建':
        标记取消(任务.id)
        return True
    if 任务.状态 in ('已提交', '排队中', '生成中'):
        标记取消(任务.id)
        _唤醒.set()
        return True
    return False


# ---------------------------------------------------------------- Comfy HTTP

def _get_json(url, 路径, 超时=10):
    req = urllib.request.Request(url + 路径)
    with 直连opener.open(req, timeout=超时) as resp:
        return json.loads(resp.read().decode('utf-8', 'replace'))


def _post_json(url, 路径, 数据, 超时=30):
    req = urllib.request.Request(
        url + 路径, data=json.dumps(数据).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    with 直连opener.open(req, timeout=超时) as resp:
        return json.loads(resp.read().decode('utf-8', 'replace'))


def _free_vram(url, 任务id=None):
    """任务结束后强制 Comfy 卸载已加载模型并清显存缓存（照旧项目 Comfy客户端.free_vram）。

    /free 不是立即卸载，而是给 prompt_queue 打 flag，真正的 unload_all_models()
    发生在下一段 prompt 启动时。不带 unload_models/free_memory=true 等于没设 flag，
    上一段模型一直缓存 → 显存吃紧 → 下段被迫低显存模式采样，耗时暴涨数十倍。
    best-effort：/free 失败退化为 /api/free，再失败仅 WARN 不影响任务本身。
    """
    payload = json.dumps({'unload_models': True, 'free_memory': True}).encode('utf-8')
    last_err = None
    for 路径 in ('/free', '/api/free'):
        try:
            req = urllib.request.Request(
                url + 路径, data=payload,
                headers={'Content-Type': 'application/json'})
            with 直连opener.open(req, timeout=30) as resp:
                if resp.status == 200:
                    if 任务id is not None:
                        记日志(任务id, '[显存] 已请求 ComfyUI 在下一任务启动时卸载模型')
                    return True
                last_err = 'HTTP %s' % resp.status
        except Exception as 异常:
            last_err = '%s: %s' % (type(异常).__name__, 异常)
            continue
    if 任务id is not None:
        记日志(任务id, '[显存][WARN] 清理显存接口未生效（%s）' % last_err)
    return False


def _下载产物(url, 条目, 目标路径):
    参数 = '?filename=%s&subfolder=%s&type=%s' % (
        urllib.request.quote(条目.get('filename', '')),
        urllib.request.quote(条目.get('subfolder', '')),
        urllib.request.quote(条目.get('type', 'output')))
    req = urllib.request.Request(url + '/view' + 参数)
    with 直连opener.open(req, timeout=300) as resp:
        数据 = resp.read()
    with open(目标路径, 'wb') as f:
        f.write(数据)
    return 目标路径


# ---------------------------------------------------------------- 执行器

def 启动执行器():
    """Django 启动时调一次；重复调用无害。"""
    global _已启动
    with _锁:
        if _已启动:
            return
        _已启动 = True
    threading.Thread(target=_comfy线程, daemon=True, name='comfy执行器').start()
    threading.Thread(target=_llm线程, daemon=True, name='llm执行器').start()


def 入队(任务id):
    """任务提交后调用：唤醒工作线程。"""
    _唤醒.set()


def _取最旧已创建(类型集合):
    return (task.objects.filter(状态='已创建', 类型__in=类型集合)
            .order_by('id').first())


def _线程取任务(类型集合):
    """带异常保护的取任务，绝不让执行器线程因为一次查询失败就退出。

    背景（2026-10-21 任务 109）：执行器线程的 DB 连接空闲超过 MySQL
    wait_timeout（默认 28800 秒 = 8 小时）会被服务端掐断，下一次 filter 抛
    OperationalError(2006, 'MySQL server has gone away')。以前这个调用在
    while 里没有任何 try，线程直接静默退出 —— 之后用户提交的任务全部卡在
    「已创建」无人执行，表现就是「任务建了但不动」。
    这里：先 close() 丢掉失效连接（下次查询 Django 会自动重建），再短睡重试，
    本函数内部消化异常、绝不外抛，调用方不需要再包 try。
    连败时每 12 次（约 1 分钟）才打一次栈，避免库长时间挂掉时日志被刷爆。
    """
    连败 = 0
    while True:
        try:
            return _取最旧已创建(类型集合)
        except Exception:
            连败 += 1
            if 连败 % 12 == 1:
                traceback.print_exc()
            try:
                connection.close()
            except Exception:
                traceback.print_exc()
            time.sleep(5)


def _comfy线程():
    while True:
        # _线程取任务 自带重试、不抛异常，所以这里不需要 try；
        # 保持「无任务时只 wait，不碰 free_vram」的原有语义
        任务 = _线程取任务(Comfy类型)
        if 任务 is None:
            _唤醒.wait(timeout=2.0)
            _唤醒.clear()
            continue
        try:
            _跑comfy任务(任务.id)
        except Exception as 异常:
            traceback.print_exc()
            try:
                标记失败(任务.id, 异常)
            except Exception:
                pass
        finally:
            # 每段结束立刻请求卸载模型，让下一段从干净显存起跑
            #（不清理会导致下段显存吃紧、被逼进低显存模式采样，耗时暴涨数十倍）
            try:
                配置 = 取模型配置()
                if 配置.ComfyUI地址:
                    _free_vram(补协议(配置.ComfyUI地址))
            except Exception:
                traceback.print_exc()


def _llm线程():
    from 能力.文本回复 import 执行文本回复
    from 能力.图片解析 import 执行图片解析
    while True:
        任务 = _线程取任务(LLM类型)
        if 任务 is None:
            _唤醒.wait(timeout=2.0)
            _唤醒.clear()
            continue
        try:
            if 任务.类型 == '文本回复':
                执行文本回复(任务.id)
            else:
                执行图片解析(任务.id)
        except Exception as 异常:
            traceback.print_exc()
            try:
                标记失败(任务.id, 异常)
            except Exception:
                pass


def _跑comfy任务(任务id):
    from 能力.文生图 import 构建文生图
    from 能力.文生图8K import 构建文生图8K
    from 能力.三图编辑一致版 import 构建三图编辑一致版
    from 能力.多图编辑多人合并版 import 构建多图编辑多人合并版
    from 能力.动漫转真人 import 构建动漫转真人
    from 能力.人物替换 import 构建人物替换
    from 能力.首尾帧 import 构建首尾帧
    from 能力.参考生视频 import 构建参考生视频
    from 能力.去水印 import 构建去水印
    from 能力.二采重绘 import 构建二采重绘
    from 能力.文生视频 import 构建文生视频
    from 能力.多参考生视频 import 构建多参考生视频
    from 能力.首尾帧生视频 import 构建首尾帧生视频
    from 能力.视频生视频 import 构建视频生视频
    from 能力.参考视频生视频 import 构建参考视频生视频
    from 能力.加速版生视频 import 构建加速版生视频
    from 能力.二采加速生视频 import 构建二采加速生视频
    from 能力.外部分组图生视频 import 构建外部分组图生视频
    from 能力.外部分组多参考生视频 import 构建外部分组多参考生视频
    from 能力.导演台全能 import 构建导演台全能

    构建表 = {
        '生成图片': 构建文生图,
        '文生图8K': 构建文生图8K,
        '三图编辑一致版': 构建三图编辑一致版,
        '多图编辑多人合并版': 构建多图编辑多人合并版,
        '动漫转真人': 构建动漫转真人,
        '人物替换': 构建人物替换,
        '首尾帧': 构建首尾帧,
        '参考生视频': 构建参考生视频,
        '去水印': 构建去水印,
        '二采重绘': 构建二采重绘,
        '文生视频': 构建文生视频,
        '多参考生视频': 构建多参考生视频,
        '首尾帧生视频': 构建首尾帧生视频,
        '视频生视频': 构建视频生视频,
        '参考视频生视频': 构建参考视频生视频,
        '加速版生视频': 构建加速版生视频,
        '二采加速生视频': 构建二采加速生视频,
        '外部分组图生视频': 构建外部分组图生视频,
        '外部分组多参考生视频': 构建外部分组多参考生视频,
        '导演台全能': 构建导演台全能,
    }

    任务 = task.objects.get(id=任务id)
    配置 = 取模型配置()
    comfy = 补协议(配置.ComfyUI地址)
    记日志(任务id, '[提交] 类型=%s Comfy=%s' % (任务.类型, comfy))

    # 探活：连不上就是中断，不能挂成生成中
    try:
        _get_json(comfy, '/system_stats', 超时=8)
    except Exception as 异常:
        标记中断(任务id, 'ComfyUI 连接失败：%s' % 异常)
        return

    # 显存预检：可用显存过低时告警（LLM 服务与 Comfy 同卡时会挤爆显存，采样降速几十倍）
    try:
        统计 = _get_json(comfy, '/system_stats', 超时=8)
        设备 = (统计.get('devices') or [{}])[0]
        总显存 = 设备.get('vram_total') or 0
        空闲显存 = 设备.get('vram_free') or 0
        if 总显存 and 空闲显存 < 总显存 * 0.12:
            记日志(任务id, '[显存][WARN] 空闲显存 %.1f GB / %.1f GB，不足 12%%，'
                   '本任务可能显著变慢（常见原因：LLM 服务驻留显存）。' % (
                       空闲显存 / 1024**3, 总显存 / 1024**3))
    except Exception:
        pass

    # 组工作流（业务填充在各能力模块）
    try:
        api = 构建表[任务.类型](任务, comfy)
    except Exception as 异常:
        标记失败(任务id, 异常)
        return

    # 提交
    try:
        响应 = _post_json(comfy, '/prompt', {'prompt': api, 'client_id': 'aicg-%s' % 任务id})
        prompt_id = 响应.get('prompt_id') or ''
    except Exception as 异常:
        标记失败(任务id, 异常)
        return
    if not prompt_id:
        _置状态(任务id, '失败', 错误信息='Comfy 未返回 prompt_id',
                错误文件=__file__, 错误行号=0, 错误函数='_跑comfy任务', 结束时间=timezone.now())
        return

    任务 = _置状态(任务id, '已提交', comfy_prompt_id=prompt_id)
    记日志(任务id, '[提交] prompt_id=%s' % prompt_id)

    # 等待循环：queue 判 running/pending，history 判终态
    开始 = time.time()
    已写开始时间 = False
    已存产物 = False
    查询失败秒 = 0          # 连续查询失败容忍（Comfy 忙时会瞬时 503，不该立刻判中断）
    查询容忍秒 = 120
    while time.time() - 开始 < 总超时秒:
        time.sleep(轮询间隔秒)

        # 取消状态查询也用软失败：查询本身抛异常（连接被掐等）时不能拖垮整个任务
        try:
            当前 = task.objects.filter(id=任务id).first()
        except Exception:
            当前 = None
        if 当前 is not None and 当前.状态 == '已取消':
            try:
                _post_json(comfy, '/interrupt', {})
            except Exception:
                pass
            记日志(任务id, '[取消] 已向 Comfy 发送 interrupt')
            return

        # queue：running → 生成中并写开始时间；pending → 排队中
        try:
            队列 = _get_json(comfy, '/queue')
            查询失败秒 = 0
        except Exception as 异常:
            查询失败秒 += 轮询间隔秒
            if 查询失败秒 >= 查询容忍秒:
                标记中断(任务id, '连续 %d 秒查询 Comfy queue 失败：%s' % (查询容忍秒, 异常))
                return
            continue
        运行中 = any(条[1] == prompt_id for 条 in 队列.get('queue_running') or [])
        排队中 = any(条[1] == prompt_id for 条 in 队列.get('queue_pending') or [])
        if 运行中 and not 已写开始时间:
            _置状态(任务id, '生成中', 开始时间=timezone.now())
            已写开始时间 = True
            记日志(任务id, '[开始] Comfy 真正开跑（queue running）')
        elif 排队中 and not 运行中:
            _置状态(任务id, '排队中')

        # history：有记录即终态候选
        try:
            历史 = _get_json(comfy, '/history/%s' % prompt_id)
            查询失败秒 = 0
        except Exception as 异常:
            查询失败秒 += 轮询间隔秒
            if 查询失败秒 >= 查询容忍秒:
                标记中断(任务id, '连续 %d 秒查询 Comfy history 失败：%s' % (查询容忍秒, 异常))
                return
            continue
        if prompt_id not in 历史:
            continue
        条目 = 历史[prompt_id]
        状态信息 = (条目.get('status') or {})
        if 状态信息.get('status_str') == 'error' or 状态信息.get('completed') is False:
            详情 = _取执行错误(状态信息)
            记日志(任务id, '[失败] ' + 详情['日志'])
            _置状态(任务id, '失败', 错误信息=详情['摘要'],
                    错误文件=__file__, 错误行号=0, 错误函数='_跑comfy任务',
                    结束时间=timezone.now())
            return

        输出 = 条目.get('outputs') or {}
        图片, 视频 = 收集输出(输出)
        if not 图片 and not 视频:
            if 状态信息.get('completed') is True or 状态信息.get('status_str') == 'success':
                # 执行已成功结束却没有产物：工作流输出链断了（如节点被误摘/被旁路），立刻失败，不能死等
                记日志(任务id, '[失败] ComfyUI 执行成功但没有产出任何图片/视频（检查工作流输出链）')
                _置状态(任务id, '失败',
                        错误信息='ComfyUI 执行成功但没有产出任何图片/视频，工作流输出链可能已断开。',
                        错误文件=__file__, 错误行号=0, 错误函数='_跑comfy任务',
                        结束时间=timezone.now())
                return
            continue  # 还没出结果，继续等

        # 产物落盘：1~2 图 或 2 视频，超了直接判失败
        # 两张图时按 filename 前缀分流：带放大标记的是放大图（产物图片2），不带的是原图/成品（产物图片）
        try:
            产物目录 = Path(settings.OUTPUT_DIR)
            产物目录.mkdir(parents=True, exist_ok=True)
            字段 = {}
            if 图片:
                if len(图片) > 2:
                    raise ValueError('产出图片 %d 张，平台只允许 2 张' % len(图片))
                排序图 = sorted(图片, key=lambda 条: any(
                    标记 in (条.get('filename') or '') for 标记 in 放大图标记))
                for i, 条 in enumerate(排序图[:2], 1):
                    p = 产物目录 / ('task_%s_%d%s' % (任务id, i, 后缀名(条)))
                    _下载产物(comfy, 条, p)
                    字段['产物图片' if i == 1 else '产物图片2'] = '产物/' + p.name
                    记日志(任务id, '[产物] 图片 %s' % p.name)
            if 视频:
                if len(视频) > 2:
                    raise ValueError('产出视频 %d 个，平台只允许 2 个' % len(视频))
                if 图片:
                    raise ValueError('图片与视频同时产出，互斥规则不允许')
                for i, 条 in enumerate(视频[:2], 1):
                    p = 产物目录 / ('task_%s_%d%s' % (任务id, i, 后缀名(条)))
                    _下载产物(comfy, 条, p)
                    字段['产物视频%d' % i] = '产物/' + p.name
                    记日志(任务id, '[产物] 视频 %s' % p.name)
            if not 字段:
                continue
            已存产物 = True
            _置状态(任务id, '成功', 结束时间=timezone.now(), **字段)
            记日志(任务id, '[完成] 成功，产物 %d 项' % len(字段))
            return
        except Exception as 异常:
            标记失败(任务id, 异常)
            return

    if not 已存产物:
        try:
            _post_json(comfy, '/interrupt', {})
        except Exception:
            pass
        标记中断(任务id, '超过 %d 秒未等到终态' % 总超时秒)


视频后缀 = ('.mp4', '.webm', '.mov', '.avi', '.mkv', '.gif')


def 是视频条目(条目, kinds=None):
    """SaveVideo 的产物在 history 里也挂在 images 键下，只靠 animated 标记区分。"""
    名 = (条目.get('filename') or '').lower()
    if 名.endswith(视频后缀):
        return True
    return bool((kinds or {}).get('animated'))


def 收集输出(输出):
    """从 history.outputs 收集图片与视频条目。"""
    图片, 视频 = [], []
    for _nid, kinds in (输出 or {}).items():
        if not isinstance(kinds, dict):
            continue
        for 条 in kinds.get('images') or []:
            if 条.get('type', 'output') == 'temp':
                continue
            if 是视频条目(条, kinds):
                视频.append(条)
            else:
                图片.append(条)
        for k in ('videos', 'gifs'):
            for 条 in kinds.get(k) or []:
                视频.append(条)
    # 稳定排序：temp 的（预览节点，save_output=False）排到最后。
    # T10 二采重绘有两个 VHS_VideoCombine —— 168 真输出（二采成品）、285 预览（一采中间结果），
    # 不排序时「哪个进 产物视频1」取决于 ComfyUI history 的字典序，不可靠。
    # 排序后 产物视频1 恒为真输出、产物视频2 恒为预览。其他工作流没有 temp 视频，顺序不变。
    视频.sort(key=lambda 条: 1 if 条.get('type') == 'temp' else 0)
    return 图片, 视频


def 后缀名(条目):
    名 = 条目.get('filename') or ''
    点 = 名.rfind('.')
    return 名[点:].lower() if 点 >= 0 else '.bin'
