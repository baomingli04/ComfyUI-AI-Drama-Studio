# -*- coding: utf-8 -*-
"""提示词资源库：直连 comfyit.cn 提示词广场取「图片 + 提示词」。

站点接口（旧项目已实测，**不需要登录**）：
  - 列表：POST https://api.comfyit.cn/promptPlaza/list
          body {"keyword":"","sortType":"copy","pageNumber":N,"pageSize":20}
          请求头必须带 platform: comfyit.cn，且**不能带 Origin**
          （带了会被站点 CORS 校验拒掉：Invalid CORS request 403）。
          返回 result.datas[] + result.total。
  - 详情：GET https://api.comfyit.cn/promptPlaza/details?id=<id>
          列表里的 positive/negative 是 null，**只有详情才有完整提示词**。
  - 封面：datas[].frontCover 是 alicdn 外链，前端 <img> 可直接显示。

本项目按 docs/02「提示词资源库不建表」：不入库、不下载封面到 media，
只在进程内做一次轻量缓存（翻回同一页 / 点同一条不再重复请求外网），重启即失效。
"""
import json
import urllib.error
import urllib.request

# 站点是外网，走直连：本机环境变量可能带代理，代理连 comfyit.cn 不通（ProxyError），
# 与 LLM调用/Comfy 调用同一套做法。
直连opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

列表地址 = 'https://api.comfyit.cn/promptPlaza/list'
详情地址 = 'https://api.comfyit.cn/promptPlaza/details'

_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/132.0.6834.159 Safari/537.36')
_头 = {'Content-Type': 'application/json', 'platform': 'comfyit.cn', 'User-Agent': _UA}

# 每页条数固定 20：站点 UI 就是这个值，不能改。
每页条数 = 20
超时 = 30

_列表缓存 = {}   # 页码 -> (条目列表, 总数)
_详情缓存 = {}   # 站点id -> {正向提示词, 反向提示词, 标题, 封面}


def _发请求(地址, 数据=None):
    """POST（有 data）或 GET（无 data）请求站点，返回 result 字典。"""
    if 数据 is None:
        请求 = urllib.request.Request(地址, headers=_头)
    else:
        请求 = urllib.request.Request(
            地址, data=json.dumps(数据).encode('utf-8'), headers=_头, method='POST')
    try:
        with 直连opener.open(请求, timeout=超时) as 响应:
            文本 = 响应.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        明细 = e.read().decode('utf-8', 'replace')[:300]
        raise RuntimeError('提示词广场返回 HTTP %s：%s' % (e.code, 明细))
    except urllib.error.URLError as e:
        raise RuntimeError('连不上提示词广场（%s）：%s' % (地址, e.reason))
    try:
        结果 = json.loads(文本)
    except ValueError:
        raise RuntimeError('提示词广场返回不是 JSON：%s' % 文本[:200])
    return (结果 or {}).get('result') or {}


def _转整数(值):
    """站点字段可能是空串/None，统一转 int。"""
    try:
        return int(值 or 0)
    except (TypeError, ValueError):
        return 0


def _条目(行):
    """站点列表一行 → 前端要的字段。"""
    作者 = 行.get('author') or {}
    return {
        'id': 行.get('id'),
        '标题': 行.get('title') or '',
        '封面': 行.get('frontCover') or '',
        '作者': 作者.get('nickname') or 作者.get('nickName') or '匿名',
        '复制数': _转整数(行.get('copyCount')),
        '浏览数': _转整数(行.get('viewCount')),
        '模型': 行.get('models') or '',
        '创建时间': 行.get('createTimeStr') or '',
    }


def 取列表(页码=1):
    """拉站点第 页码 页，返回 (条目列表, 总数)。带进程内缓存。"""
    页码 = int(页码 or 1)
    if 页码 < 1:
        页码 = 1
    if 页码 in _列表缓存:
        return _列表缓存[页码]
    结果 = _发请求(列表地址, {
        'keyword': '', 'sortType': 'copy',
        'pageNumber': 页码, 'pageSize': 每页条数,
    })
    行列表 = 结果.get('datas') or []
    条目列表 = [_条目(行) for 行 in 行列表 if 行.get('id') is not None]
    总数 = _转整数(结果.get('total'))
    _列表缓存[页码] = (条目列表, 总数)
    return _列表缓存[页码]


def 取详情(站点id):
    """按站点 id 拉详情，返回 {'正向提示词','反向提示词','标题','描述','封面'}。带缓存。"""
    站点id = str(站点id)
    if 站点id in _详情缓存:
        return _详情缓存[站点id]
    结果 = _发请求(详情地址 + '?id=' + 站点id)
    详情 = {
        '正向提示词': 结果.get('positive') or '',
        '反向提示词': 结果.get('negative') or '',
        '标题': 结果.get('title') or '',
        '描述': 结果.get('description') or '',
        '封面': 结果.get('frontCover') or '',
    }
    _详情缓存[站点id] = 详情
    return 详情
