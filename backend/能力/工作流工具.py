# -*- coding: utf-8 -*-
"""工作流工具：ComfyUI 工作流 JSON 的装载与节点填充、输入文件上传。

只做「怎么把参数写进工作流」这一件事；提交/等待/状态/取消在 提交并等待.py。
节点填充约定来自旧项目实测（_meta.title 标记定位、COMBO 节点必须先上传再写文件名），
但等待与返回逻辑不搬旧代码。
"""
import json
import os
import random
import time
import urllib.error
import urllib.request


# 内网直连：本机环境变量可能带 HTTP_PROXY（沙箱代理），访问 Comfy/LLM 必须绕开，
# 否则代理会间歇性掐断连接（10053/10054/503），任务被误判中断。
直连opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# ResolutionSelector.aspect_ratio 的 combo 完整标签映射。
# 必须传完整标签（如 '9:16 (Portrait Widescreen)'），裸 '9:16' 会校验失败。
宽高比标签 = {
    '1:1': '1:1 (Square)',
    '2:3': '2:3 (Portrait Photo)',
    '3:2': '3:2 (Photo)',
    '3:4': '3:4 (Portrait Standard)',
    '4:3': '4:3 (Standard)',
    '9:16': '9:16 (Portrait Widescreen)',
    '16:9': '16:9 (Widescreen)',
    '21:9': '21:9 (Ultrawide)',
}


def 任务文件(相对路径):
    """task 输入列存的相对路径（'上传/xxx.png'）→ 资源目录下的绝对路径。"""
    from django.conf import settings
    return settings.RESOURCE_DIR / 相对路径


def 装载工作流(路径):
    """读工作流 JSON（API 格式），返回 dict。"""
    with open(路径, 'r', encoding='utf-8') as f:
        return json.load(f)


def 按标题找节点(api, 标题):
    """按 _meta.title 精确匹配，返回节点 id 列表。"""
    return [nid for nid, v in api.items()
            if isinstance(v, dict) and v.get('_meta', {}).get('title') == 标题]


def 按类型找节点(api, 类名):
    """按 class_type 找节点 id 列表（按数值排序，保证 LoadImage 多个时顺序稳定）。"""
    ids = [nid for nid, v in api.items()
           if isinstance(v, dict) and v.get('class_type') == 类名]
    try:
        ids.sort(key=lambda x: int(x))
    except (TypeError, ValueError):
        pass
    return ids


def 写文本(api, 节点标识, 文本):
    """按标题或节点 id 写多行文本节点的 value/text。"""
    ids = 按标题找节点(api, 节点标识) or ([节点标识] if 节点标识 in api else [])
    for nid in ids:
        inputs = api[nid].get('inputs', {})
        if 'value' in inputs:
            inputs['value'] = 文本
        elif 'text' in inputs:
            inputs['text'] = 文本
        else:
            inputs['value'] = 文本
    return ids


def 写参数(api, 节点标识, 参数名, 值):
    """按标题或节点 id 写指定参数。"""
    ids = 按标题找节点(api, 节点标识) or ([节点标识] if 节点标识 in api else [])
    for nid in ids:
        api[nid].setdefault('inputs', {})[参数名] = 值
    return ids


def 上传到Comfy(url, 文件路径):
    """上传本地文件到 ComfyUI input 目录（图片/视频/音频通用），返回存储文件名。

    COMBO 节点（LoadImage/VHS_LoadVideo/VHS_LoadAudioUpload）只认 ComfyUI input
    目录内的文件名，本机绝对路径会被校验拒绝，所以必须先上传再写文件名。
    源文件名（中文/超长）会触发远端 Windows MAX_PATH，改用短随机名。
    """
    后缀 = os.path.splitext(文件路径)[1].lower() or '.png'
    名字 = 'u%d%s' % (time.time_ns(), 后缀)
    with open(文件路径, 'rb') as f:
        数据 = f.read()
    边界 = '----aicomfy%d' % int(time.time() * 1000)
    crlf = b'\r\n'
    body = b''
    body += ('--' + 边界 + '\r\n').encode()
    body += ('Content-Disposition: form-data; name="image"; filename="%s"\r\n' % 名字).encode('utf-8')
    body += b'Content-Type: application/octet-stream\r\n\r\n'
    body += 数据
    body += crlf
    body += ('--' + 边界 + '--\r\n').encode()
    req = urllib.request.Request(
        url + '/upload/image', data=body,
        headers={'Content-Type': 'multipart/form-data; boundary=' + 边界})
    with 直连opener.open(req, timeout=120) as resp:
        结果 = json.loads(resp.read().decode('utf-8', 'replace'))
    return 结果.get('name', 名字)


def 装填图片(api, 类名, 文件路径, 序号=0, url=''):
    """把第 序号 个「类名」节点的输入设为上传后的文件名。文件不存在则原样写入。"""
    ids = 按类型找节点(api, 类名)
    if 序号 >= len(ids):
        raise IndexError('%s 只有 %d 个，不够第 %d 个' % (类名, len(ids), 序号 + 1))
    if os.path.isfile(文件路径):
        名字 = 上传到Comfy(url, 文件路径)
    else:
        名字 = 文件路径
    api[ids[序号]].setdefault('inputs', {})[_输入名(类名)] = 名字
    return ids[序号]


def _输入名(类名):
    """不同 COMBO 节点的文件字段名不同。"""
    if 'Video' in 类名:
        return 'video'
    if 'Audio' in 类名:
        return 'audio'
    return 'image'


def 摘除节点(api, 节点id):
    """柔性摘除未用到的输入节点，并清掉消费端指向它的悬空连接。

    空路径留在 VHS_LoadVideo / LoadAudio 的 COMBO 里会被校验判非法 → 400，
    所以未提供的参考位必须整个摘除。
    """
    if 节点id not in api:
        return
    api.pop(节点id, None)
    for _nid, 节点 in api.items():
        inputs = 节点.get('inputs', {})
        for 键 in list(inputs.keys()):
            值 = inputs[键]
            if isinstance(值, list) and len(值) >= 1 and str(值[0]) == str(节点id):
                del inputs[键]


def 写宽高比(api, 比例, 兆像素=None, 节点id=None):
    """写 ResolutionSelector 的 aspect_ratio / megapixels。比例要映射成完整标签。"""
    ids = [节点id] if 节点id else 按类型找节点(api, 'ResolutionSelector')
    for nid in ids:
        if nid not in api:
            continue
        inputs = api[nid].setdefault('inputs', {})
        if 比例 and 比例 in 宽高比标签:
            inputs['aspect_ratio'] = 宽高比标签[比例]
        if 兆像素 is not None:
            inputs['megapixels'] = round(float(兆像素), 4)


def 宽高算比例(宽, 高):
    """由宽高算最接近的支持比例标签键，找不到返回 None。"""
    if not 宽 or not 高:
        return None
    值 = float(宽) / float(高)
    候选 = {'1:1': 1.0, '2:3': 2.0 / 3.0, '3:2': 1.5, '3:4': 0.75, '4:3': 4.0 / 3.0,
            '9:16': 0.5625, '16:9': 16.0 / 9.0, '21:9': 21.0 / 9.0}
    最佳 = min(候选, key=lambda k: abs(候选[k] - 值))
    return 最佳


def 随机种子():
    return random.randint(0, 2 ** 48)
