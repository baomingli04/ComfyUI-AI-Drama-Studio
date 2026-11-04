// 分集剧本的结构化解析与体检。
//
// 一集剧本 = 正文（按场次）+ 五个档案块：
//   能力档案 / 世界状态 / 关系网络 / 记忆回廊 / 行动推荐
// 约定：AI 输出用【块名】分段。解析要能容忍这些写法差异：
//   【能力档案】 / ## 能力档案 / 能力档案： / 能力档案
// 这里只有纯函数，不碰 Vue，页面和组件都能引。

/* 五个档案块的字段表。顺序就是渲染顺序，也是喂给 AI 时的字段顺序。 */
export const 档案块们 = [
  {
    键: '能力档案', 名: '能力档案', 注: '本集之后主角的状态面板', 型: '键值',
    字段: ['所属势力', '声望影响', '阶级', '评级', '拥有技能', '当前体力', '能量状态', '健康状态', '拥有物品', '目前目标']
  },
  {
    键: '世界状态', 名: '世界状态', 注: '时间地点 + 周边情报', 型: '键值',
    字段: ['当前世界', '当前日期', '当前区域', '当前环境', '当前事件', '区域布局', '区域情报', '区域角色', '传闻', '附近热议', '附近动向']
  },
  {
    键: '关系网络', 名: '关系网络', 注: '主线、预告与蝴蝶效应', 型: '键值',
    字段: ['当前主线', '预告1', '预告2', '蝴蝶效应', '历史进程', '角色记录']
  },
  {
    键: '记忆回廊', 名: '记忆回廊', 注: '长期记忆 + 短期滚动 6 条', 型: '键值',
    字段: ['长期记忆', '短期记忆1', '短期记忆2', '短期记忆3', '短期记忆4', '短期记忆5', '短期记忆6']
  },
  {
    键: '行动推荐', 名: '行动推荐', 注: '给下一集的 3 个可选方向', 型: '列表',
    字段: []
  }
]

/* 块名别名：AI 有时候会写「剧本正文」「能力面板」这类近义词，一起认。 */
const 块别名 = {
  正文: ['正文', '剧本正文', '剧本', '场次正文', '正文剧本', '分集剧本'],
  能力档案: ['能力档案', '能力面板', '能力状态', '角色状态', '能力档案面板'],
  世界状态: ['世界状态', '世界面板', '环境状态', '世界状态面板'],
  关系网络: ['关系网络', '关系面板', '关系网', '关系网络面板'],
  记忆回廊: ['记忆回廊', '记忆面板', '记忆', '记忆回廊面板'],
  行动推荐: ['行动推荐', '行动建议', '推荐行动', '下一步行动'],
  人物变化: ['人物变化', '人物变动', '人物状态变化', '人物档案变化']
}

/* 反向表：别名 -> 标准块名 */
const 名到块 = {}
Object.keys(块别名).forEach(块 => {
  块别名[块].forEach(别 => { 名到块[别] = 块 })
})

/* 认一行是不是块标题；是就返回标准块名，不是返回 '' */
function 认块标题(原行) {
  let 行 = String(原行 || '').trim()
  if (!行) return ''
  // 去掉 markdown 记号与列表符号
  行 = 行.replace(/^[#>*\-·\s]+/, '').replace(/[#*\s]+$/, '')
  // 去掉包裹符号
  行 = 行.replace(/^[【\[「（(]+/, '').replace(/[】\]」）)]+$/, '')
  // 去掉尾部冒号
  行 = 行.replace(/[:：]+$/, '').trim()
  if (!行) return ''
  if (名到块[行]) return 名到块[行]
  // 「能力档案（第1集）」这种带括号说明的
  const 主 = 行.replace(/[（(].*$/, '').trim()
  if (名到块[主]) return 名到块[主]
  return ''
}

/* 认一行是不是场次头，是就返回 { 场, 地点, 人物 } */
export function 认场头(原行) {
  const 行 = String(原行 || '').trim()
  if (!行) return null
  const 号 = 行.match(/^(\d+)\s*[-－—]\s*(\d+)/)
  if (!号) return null
  const 场 = 号[1] + '-' + 号[2]
  let 余 = 行.slice(号[0].length).replace(/^[\s·・|｜:：\-]+/, '').trim()
  if (!余) return { 场: 场, 地点: '', 人物: '' }
  if (余.indexOf('｜') >= 0 || 余.indexOf('|') >= 0) {
    const 段 = 余.split(/[｜|]/).map(s => s.trim()).filter(s => s)
    // 约定是「地点｜时间｜人物」；只有两段时按「地点｜人物」认
    if (段.length >= 3) return { 场: 场, 地点: [段[0], 段[1]].join(' · '), 人物: 段[2] }
    if (段.length === 2) return { 场: 场, 地点: 段[0], 人物: 段[1] }
    return { 场: 场, 地点: 段[0] || '', 人物: '' }
  }
  return { 场: 场, 地点: 余, 人物: '' }
}

/* 认「出场人物：」「出场道具：」这类场次附属行 */
function 认场字段(行) {
  const 段 = String(行 || '').trim().match(/^(出场人物|人物|出场道具|道具|场景|地点|时间)\s*[:：]\s*(.*)$/)
  if (!段) return null
  const 键 = 段[1]
  const 值 = 段[2].trim()
  if (键 === '出场人物' || 键 === '人物') return { 键: '人物', 值: 值 }
  if (键 === '出场道具' || 键 === '道具') return { 键: '道具', 值: 值 }
  if (键 === '时间') return { 键: '时间', 值: 值 }
  return { 键: '地点', 值: 值 }
}

/* 正文 -> 场次数组。认不出场次头时返回空数组，调用方退回纯文本展示。 */
export function 拆场次(正文) {
  const 行们 = String(正文 || '').replace(/\r\n?/g, '\n').split('\n')
  const 场们 = []
  let 当前 = null
  for (let i = 0; i < 行们.length; i++) {
    const 行 = 行们[i].trim()
    if (!行) continue
    const 头 = 认场头(行)
    if (头) {
      当前 = { 场: 头.场, 地点: 头.地点, 人物: 头.人物, 道具: '', 时间: '', 正文: [] }
      场们.push(当前)
      continue
    }
    if (!当前) continue
    const 附 = 认场字段(行)
    if (附) {
      if (附.键 === '人物' && !当前.人物) 当前.人物 = 附.值
      else if (附.键 === '道具') 当前.道具 = 附.值
      else if (附.键 === '时间') 当前.时间 = 附.值
      else if (附.键 === '地点' && !当前.地点) 当前.地点 = 附.值
      continue
    }
    当前.正文.push(行)
  }
  return 场们
}

/* 「键：值」行 -> { 键值, 余 }。余 = 没认出键的行，留着兜底展示。 */
function 解析键值(行们, 字段) {
  const 表 = {}
  const 余 = []
  ;(行们 || []).forEach(原 => {
    const 行 = String(原 || '').replace(/^[\s>*\-·]+/, '').trim()
    if (!行) return
    const 位 = 行.search(/[:：]/)
    if (位 <= 0) { 余.push(行); return }
    const 键 = 行.slice(0, 位).replace(/[【】\[\]]/g, '').trim()
    const 值 = 行.slice(位 + 1).trim()
    if (!键 || 键.length > 12) { 余.push(行); return }
    表[键] = 值
  })
  const 键值 = {}
  ;(字段 || []).forEach(k => { 键值[k] = 表[k] == null ? '' : 表[k] })
  Object.keys(表).forEach(k => { if (键值[k] === undefined) 键值[k] = 表[k] })
  return { 键值: 键值, 余: 余 }
}

/* 编号 / 项目符号行 -> 字符串数组 */
function 解析列表(行们) {
  const 出 = []
  ;(行们 || []).forEach(原 => {
    const 行 = String(原 || '').trim()
    if (!行) return
    const 净 = 行.replace(/^[\s>*\-·]+/, '').replace(/^\d+\s*[.、)）]\s*/, '').trim()
    if (净) 出.push(净)
  })
  return 出
}

/* 空档案骨架：5 个块都在，值全空，方便组件直接渲染 */
export function 造空档案() {
  const 出 = {}
  档案块们.forEach(块 => {
    if (块.型 === '列表') { 出[块.键] = [] ; return }
    const 键值 = {}
    块.字段.forEach(k => { 键值[k] = '' })
    出[块.键] = 键值
  })
  return 出
}

/* 空剧本：一集还没生成时的占位 */
export function 造空剧本() {
  return { 正文: '', 场们: [], 档案: 造空档案(), 命中: [], 缺: 档案块们.map(块 => 块.键), 状态: '未生成', 时间: '' }
}

/*
 * 解析 AI 返回的整段文本。
 * 返回 { 正文, 场们, 档案, 命中, 缺, 原文 }
 * 一个块都没认出来时，整段当正文（老提示词出来的就是纯剧本），档案留空。
 */
export function 解析生成结果(文本) {
  const 原文 = String(文本 || '').replace(/\r\n?/g, '\n')
  const 行们 = 原文.split('\n')
  const 段 = {}
  const 命中 = []
  let 当前 = ''

  for (let i = 0; i < 行们.length; i++) {
    const 块 = 认块标题(行们[i])
    if (块) {
      当前 = 块
      if (!段[块]) {
        段[块] = []
        // 人物变化是附加块，不计入档案命中/缺的计数（命中 X/6 只算 5 个档案块 + 正文）
        if (块 !== '人物变化') 命中.push(块)
      }
      continue
    }
    if (当前) 段[当前].push(行们[i])
  }

  // 【人物变化】每行「人物名｜字段｜第N集：内容」→ { 名, 字段, 内容 }；认不出的行丢弃
  const 人物变化们 = (段['人物变化'] || []).map(function (原) {
    const 行 = String(原 || '').replace(/^[\s>*\-·\d]+/, '').trim()
    if (!行) return null
    const 片们 = 行.split(/[｜|]/).map(function (s) { return s.trim() })
    if (片们.length < 3) return null
    return { 名: 片们[0], 字段: 片们[1], 内容: 片们.slice(2).join('｜') }
  }).filter(Boolean)

  // 一块都没认出来 = 纯正文
  const 有块 = 命中.length > 0
  const 正文 = 有块
    ? (段['正文'] || []).join('\n').trim()
    : 原文.trim()

  const 档案 = 造空档案()
  const 余文 = {}
  档案块们.forEach(块 => {
    const 行们 = 段[块.键] || []
    if (块.型 === '列表') {
      档案[块.键] = 解析列表(行们)
      return
    }
    const 结 = 解析键值(行们, 块.字段)
    档案[块.键] = 结.键值
    if (结.余.length) 余文[块.键] = 结.余.join('\n')
  })

  const 缺 = 档案块们.filter(块 => {
    if (块.型 === '列表') return !(档案[块.键] || []).length
    return !Object.keys(档案[块.键] || {}).some(k => String(档案[块.键][k] || '').trim())
  }).map(块 => 块.键)

  return {
    正文: 正文,
    场们: 拆场次(正文),
    档案: 档案,
    余文: 余文,
    命中: 命中,
    缺: 缺,
    人物变化: 人物变化们,
    原文: 原文
  }
}

/* 正文去空白后的字数（中文按字算） */
export function 数字数(正文) {
  return String(正文 || '').replace(/\s+/g, '').length
}

/* 建议场数：按正文推算。短剧一场约 2 分钟，一集建议 2–3 场，硬上限 4 场。 */
export function 建议场数(字数) {
  const 数 = Number(字数) || 0
  const 时长 = 数 ? Math.max(1, Math.round(数 / 650)) : 0
  let 多 = Math.round(时长 / 2)
  if (多 < 2) 多 = 2
  if (多 > 4) 多 = 4
  return { 少: Math.max(2, 多 - 1), 多: 多, 上限: 4 }
}

/* 是动作行（△ 或 ▲ 开头） */
export function 是动作行(行) {
  return /^[△▲]/.test(String(行 || '').trim())
}

/* 是台词行（「角色名（动作）：台词」或「角色名：台词」） */
export function 是台词行(行) {
  const 文 = String(行 || '').trim()
  if (!文 || 是动作行(文)) return false
  if (/^（/.test(文)) return false
  return /^[^：:]{1,12}[：:]/.test(文)
}

/*
 * 剧本体检：可演 / 对白 / 场数 / 字数 / 时长。
 * 全部由正文算出来，不靠 AI 自评。
 */
export function 体检剧本(剧) {
  const 场们 = (剧 && 剧.场们) || []
  const 正文 = (剧 && 剧.正文) || ''
  const 字数 = 数字数(正文)
  const 场数 = 场们.length
  const 可演 = 场数 > 0 && 场们.every(function (场) { return !!场.地点 && !!场.人物 })
  let 对白 = false
  场们.forEach(function (场) {
    ;(场.正文 || []).forEach(function (行) { if (是台词行(行)) 对白 = true })
  })
  const 建议 = 建议场数(字数)
  const 时长 = 字数 ? Math.max(1, Math.round(字数 / 650)) : 0
  // 达标 = 不少于建议下限、不超过 4 场硬上限（4 场是允许的，只是不建议）
  const 场数达标 = 场数 >= 建议.少 && 场数 <= 建议.上限
  return {
    可演: 可演, 对白: 对白, 场数: 场数, 字数: 字数, 时长: 时长,
    建议: 建议, 场数达标: 场数达标
  }
}

/* 关键词：从这一集的钩子点位里抽，最多 5 条，每条截 10 字 */
export function 提关键词(集) {
  const 出 = []
  ;((集 && 集.点位) || []).forEach(function (点) {
    const 文 = String((点 && 点.内容) || '').trim()
    if (!文) return
    if (出.indexOf(文) >= 0) return
    出.push(文.length > 10 ? 文.slice(0, 10) : 文)
  })
  return 出.slice(0, 5)
}

/* 场次数组 -> 正文。改了场次以后用它重算正文，保证「正文」和「场次」永远一致。 */
export function 拼正文(场们) {
  const 行们 = []
  ;(场们 || []).forEach(function (场) {
    行们.push(场.场 + ' · ' + (场.地点 || ''))
    if (场.人物) 行们.push('出场人物：' + 场.人物)
    if (场.道具) 行们.push('出场道具：' + 场.道具)
    ;(场.正文 || []).forEach(function (行) { 行们.push(行) })
    行们.push('')
  })
  return 行们.join('\n').trim()
}

/* 把一集剧本拼回可复制的纯文本（正文 + 5 个档案块） */export function 拼全文(剧) {
  if (!剧) return ''
  const 行们 = ['【正文】', 剧.正文 || '']
  档案块们.forEach(function (块) {
    const 值 = (剧.档案 || {})[块.键]
    行们.push('', '【' + 块.键 + '】')
    if (块.型 === '列表') {
      ;(值 || []).forEach(function (条, 序) { 行们.push((序 + 1) + '. ' + 条) })
      return
    }
    ;(块.字段 || []).forEach(function (k) {
      const 文 = (值 && 值[k]) || ''
      if (文) 行们.push(k + '：' + 文)
    })
  })
  return 行们.join('\n').trim()
}
