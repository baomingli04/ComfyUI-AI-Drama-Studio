// 人物设定的字段口径 + 关系网常量 + 「按集分阶段」的读写工具。
//
// 一个角色的「详」有 23 个字段，顺序在这里定死，四处共用：
//   ① 详情卡渲染  ② 编辑 / 新增弹窗  ③ AI 输出解析（拆行顺序）  ④ 喂给其它页的「人物列表」
// 加字段只改这个文件，四处一起跟着变。
//
// 字段值有两种形态：
//   · 字符串          → 全剧不变（姓名、性别、背景故事…）
//   · 分段数组        → 会随集数变（身份、态度、情感情况…），形如
//                       [{ 起: 1, 止: 5, 值: '下忍' }, { 起: 6, 止: 8, 值: '上忍' }]
//   「哪些字段允许分段」由 可分段字段 说了算，其余字段永远按字符串处理。

export const 角色字段 = [
  '姓名', '性别', '年龄', '性格', '身份', '关系', '态度',
  '外貌', '身材', '穿搭',
  '身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法',
  '技能', '核心目标',
  '关系网',
  '背景故事', '台词风格', '口头禅', '概括'
]

/* 会随剧情变的字段：这些字段可以写成「第1-5集 值；第6-8集 值」 */
export const 可分段字段 = [
  '身份', '关系', '态度',
  '外貌', '穿搭',
  '身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法',
  '技能', '核心目标'
]

/* 详情卡按组铺，一组一个小区块 */
export const 字段分组 = [
  { 名: '基本信息', 字段: ['姓名', '性别', '年龄', '性格', '身份', '关系', '态度'] },
  { 名: '外形', 字段: ['外貌', '身材', '穿搭'] },
  { 名: '状态与心理', 字段: ['身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法'] },
  { 名: '能力与目标', 字段: ['技能', '核心目标'] },
  { 名: '关系', 字段: ['关系网'] },
  { 名: '背景与台词', 字段: ['背景故事', '台词风格', '口头禅', '概括'] }
]

/* 关系网的边有类型，颜色跟 .创作模块 的主题走 */
export const 关系类型们 = ['羁绊', '协作', '认可', '对立', '利用', '亲情']

export const 关系色 = {
  羁绊: '#22c55e',
  协作: '#60a5fa',
  认可: '#2dd4bf',
  对立: '#ef4444',
  利用: '#f59e0b',
  亲情: '#c084fc'
}

/* ============ 分阶段：判定 / 规整 / 显示 ============ */

/* 这个值是「分段数组」还是普通字符串 */
export function 是分段(值) {
  return Array.isArray(值) && 值.length > 0 && typeof 值[0] === 'object' && 值[0] !== null
}

export function 可分段(键) {
  return 可分段字段.indexOf(键) >= 0
}

/* 规整分段：数字化成整数、按起集排序、止集不小于起集、不超过总集。
   字段段用 值，关系段用 类型 + 说明，两种都留着，谁用谁取。 */
export function 规整段(段们, 总集) {
  const 上限 = Number(总集) > 0 ? Number(总集) : 0
  const 列 = (段们 || []).map(function (段, 序) {
    const 源 = 段 || {}
    let 起 = parseInt(源.起, 10)
    if (isNaN(起) || 起 < 1) 起 = 序 === 0 ? 1 : 1
    let 止 = parseInt(源.止, 10)
    if (isNaN(止) || 止 < 起) 止 = 起
    if (上限 && 止 > 上限) 止 = 上限
    if (上限 && 起 > 上限) 起 = 上限
    return {
      起: 起,
      止: 止,
      值: 源.值 == null ? '' : String(源.值),
      类型: 源.类型 == null ? '' : String(源.类型),
      说明: 源.说明 == null ? '' : String(源.说明)
    }
  })
  列.sort(function (a, b) { return a.起 - b.起 })
  return 列
}

/* 「第1-5集」/「第6集」/「第13集起」（到最后一集就写成「起」） */
export function 集标签(起, 止, 总集) {
  const 头 = parseInt(起, 10) || 1
  let 尾 = parseInt(止, 10)
  if (isNaN(尾) || 尾 < 头) 尾 = 头
  const 上限 = Number(总集) > 0 ? Number(总集) : 0
  if (头 === 尾) return '第' + 头 + '集'
  if (上限 && 尾 >= 上限) return '第' + 头 + '集起'
  return '第' + 头 + '-' + 尾 + '集'
}

/* 第 N 集落在哪一段：落在缝里就沿用上一段 */
export function 取段(段们, 集) {
  const 列 = 段们 || []
  const 号 = parseInt(集, 10)
  if (!号 || !列.length) return null
  for (let i = 0; i < 列.length; i++) {
    if (号 >= 列[i].起 && 号 <= 列[i].止) return 列[i]
  }
  let 中 = null
  列.forEach(function (段) { if (段.起 <= 号) 中 = 段 })
  return 中
}

/* 一段铺成一行：「第1-5集：下忍」 */
export function 段文本(段, 总集) {
  if (!段) return ''
  const 值 = 段.值 || 段.说明 || ''
  return 集标签(段.起, 段.止, 总集) + '：' + 值
}

/* 整组段铺成一句：「第1-5集：下忍；第6-8集：上忍」 */
export function 分段文本(段们, 总集) {
  return 规整段(段们, 总集).map(function (段) { return 段文本(段, 总集) }).join('；')
}

/* 取值文本：静态值原样返回；分段值传了 集 就只取那一段，没传就铺全时间轴 */
export function 值文本(值, 总集, 集) {
  if (!是分段(值)) return 值 == null ? '' : String(值)
  const 段们 = 规整段(值, 总集)
  if (!段们.length) return ''
  const 号 = parseInt(集, 10)
  if (号) {
    const 段 = 取段(段们, 号)
    return 段 ? 段.值 : ''
  }
  return 分段文本(段们, 总集)
}

/* 变化点：除第一段以外每一段的起集，用来标「第6集、第13集变过」 */
export function 变化点(值) {
  if (!是分段(值)) return []
  return 规整段(值).filter(function (段, 序) { return 序 > 0 }).map(function (段) { return 段.起 })
}

/* 有几段：静态值算 1 段 */
export function 几段(值) {
  return 是分段(值) ? 规整段(值).length : (值 ? 1 : 0)
}

/* 单值 → 分段：把现有值包成「第1集到最后一集」的一段 */
export function 拆分段(值, 总集) {
  if (是分段(值)) return 规整段(值, 总集)
  const 上限 = Number(总集) > 0 ? Number(总集) : 1
  return [{ 起: 1, 止: 上限, 值: 值 == null ? '' : String(值), 类型: '', 说明: '' }]
}

/* 分段 → 单值：取最新一段（用户主动点「合并」时用，会提示取了哪一段） */
export function 合分段(值, 总集) {
  if (!是分段(值)) return 值 == null ? '' : String(值)
  const 段们 = 规整段(值, 总集)
  if (!段们.length) return ''
  return 段们[段们.length - 1].值 || 段们[段们.length - 1].说明 || ''
}

/* 从 AI 文本里认「第1-5集：下忍；第6-8集：上忍；第9集起：…」这种写法。
   认不出（不足两段、或某段没有集数）就返回 null，交给调用方当普通字符串处理。
   「第9集起」的止集补成总集，不然往返一圈会缩成「只有第9集」。 */
export function 解析分段(文本, 总集) {
  const 块们 = String(文本 || '')
    .split(/[；;\n]+/)
    .map(function (s) { return String(s || '').trim() })
    .filter(function (s) { return s })
  if (块们.length < 2) return null
  const 上限 = Number(总集) > 0 ? Number(总集) : 0
  const 段们 = []
  for (let i = 0; i < 块们.length; i++) {
    const 配 = 块们[i].match(/^第?\s*(\d{1,4})\s*(?:[-–—~～至到]\s*(\d{1,4}))?\s*集?\s*(起|开始)?\s*[：:、]?\s*([\s\S]+)$/)
    if (!配) return null
    const 起 = parseInt(配[1], 10)
    const 开 = !!配[3]
    let 止 = 配[2] ? parseInt(配[2], 10) : (开 && 上限 ? 上限 : 起)
    const 值 = String(配[4] || '').trim()
    if (!值) return null
    段们.push({ 起: 起, 止: 止, 值: 值, 类型: '', 说明: '' })
  }
  return 规整段(段们, 总集)
}

/* AI 文本 → 字段值：能拆成段就拆，拆不出来就是一句普通文本 */
export function 文本转值(文本, 总集) {
  const 段们 = 解析分段(文本, 总集)
  if (段们 && 段们.length >= 2) return 段们
  return 文本 == null ? '' : String(文本)
}

/* 从关系的一条说明里认「第1-5集 协作（说明）；第6集起 羁绊（说明）」这种写法。
   和 关系一行 输出给 AI 的格式互为逆运算，AI 补关系网时能直接带阶段回来。 */
export function 解析关系阶段(文本, 总集) {
  const 块们 = String(文本 || '')
    .split(/[；;\n]+/)
    .map(function (s) { return String(s || '').trim() })
    .filter(function (s) { return s })
  if (块们.length < 2) return null
  const 上限 = Number(总集) > 0 ? Number(总集) : 0
  const 段们 = []
  for (let i = 0; i < 块们.length; i++) {
    const 配 = 块们[i].match(/^第?\s*(\d{1,4})\s*(?:[-–—~～至到]\s*(\d{1,4}))?\s*集?\s*(起|开始)?\s*[：:、]?\s*([\s\S]+)$/)
    if (!配) return null
    const 起 = parseInt(配[1], 10)
    const 开 = !!配[3]
    const 止 = 配[2] ? parseInt(配[2], 10) : (开 && 上限 ? 上限 : 起)
    let 余 = String(配[4] || '').trim()
    let 型 = ''
    for (let j = 0; j < 关系类型们.length; j++) {
      if (余.indexOf(关系类型们[j]) === 0) {
        型 = 关系类型们[j]
        余 = 余.slice(型.length).trim()
        break
      }
    }
    const 说明 = 余.replace(/^[（(]/, '').replace(/[）)]$/, '').trim()
    if (!型 && !说明) return null
    段们.push({ 起: 起, 止: 止, 类型: 型, 说明: 说明, 值: '' })
  }
  return 规整段(段们, 总集)
}

/* ============ 角色 / 关系 的读写 ============ */

/* 空档案：新增角色时铺满字段，表单和详情卡都不会缺行 */
export function 空角色详(名, 性别, 年龄) {
  const 详 = {}
  角色字段.forEach(function (键) { 详[键] = '' })
  详.姓名 = 名 || ''
  详.性别 = 性别 || ''
  详.年龄 = 年龄 || ''
  return 详
}

/* 规整：按固定顺序补齐缺失字段，多出来的字段放最后（AI 加了新字段也不丢）。
   分段值保持数组形态，不会被 String() 拍成 "[object Object]"。 */
export function 规整详(详) {
  const 出 = {}
  const 源 = 详 || {}
  const 收 = function (键) {
    const 值 = 源[键]
    if (是分段(值)) return 规整段(值)
    return 值 == null ? '' : String(值)
  }
  角色字段.forEach(function (键) { 出[键] = 收(键) })
  Object.keys(源).forEach(function (键) {
    if (出[键] === undefined) 出[键] = 收(键)
  })
  return 出
}

/* 一个角色铺成一行竖线文本：详情卡、AI 参考块都用这个口径。
   传了 集 就取那一集的状态，不传就铺全时间轴。 */
export function 角色一行(人, 字段们, 总集, 集) {
  const 详 = 规整详(人 && 人.详)
  const 列 = (字段们 || 角色字段).map(function (键) { return 值文本(详[键], 总集, 集) || '—' })
  return 列.join('｜')
}

/* 关系的一条边当前是什么类型：有阶段就看那一集，没传集就看最后一段 */
export function 关系类型(边, 总集, 集) {
  const 源 = 边 || {}
  const 阶段 = 是分段(源.阶段) ? 规整段(源.阶段, 总集) : []
  if (!阶段.length) return 源.类型 || ''
  const 号 = parseInt(集, 10)
  const 段 = 号 ? 取段(阶段, 号) : 阶段[阶段.length - 1]
  return (段 && 段.类型) || 源.类型 || ''
}

/* 关系的一条边当前是什么说明 */
export function 关系说明(边, 总集, 集) {
  const 源 = 边 || {}
  const 阶段 = 是分段(源.阶段) ? 规整段(源.阶段, 总集) : []
  if (!阶段.length) return 源.说明 || ''
  const 号 = parseInt(集, 10)
  const 段 = 号 ? 取段(阶段, 号) : 阶段[阶段.length - 1]
  return (段 && 段.说明) || 源.说明 || ''
}

/* 关系的一条边铺成一行：甲 ↔ 乙｜类型｜关键词1、关键词2｜说明（有阶段就写阶段） */
export function 关系一行(边, 总集) {
  const 源 = 边 || {}
  const 词 = (源.关键词 || []).join('、')
  const 阶段 = 是分段(源.阶段) ? 规整段(源.阶段, 总集) : []
  if (阶段.length) {
    const 段文 = 阶段.map(function (段) {
      return 集标签(段.起, 段.止, 总集) + ' ' + (段.类型 || '') + (段.说明 ? '（' + 段.说明 + '）' : '')
    }).join('；')
    return [源.甲 + ' ↔ ' + 源.乙, 关系类型(源, 总集), 词, 段文].join('｜')
  }
  return [源.甲 + ' ↔ ' + 源.乙, 源.类型 || '', 词, 源.说明 || ''].join('｜')
}

/* 按角色筛关系：'全部' 或某个角色名 */
export function 筛关系(边们, 角色名) {
  const 列 = 边们 || []
  if (!角色名 || 角色名 === '全部') return 列
  return 列.filter(function (边) { return 边.甲 === 角色名 || 边.乙 === 角色名 })
}

/* 两个名字是不是同一条边（无向） */
export function 是同一条边(边, 甲, 乙) {
  return (边.甲 === 甲 && 边.乙 === 乙) || (边.甲 === 乙 && 边.乙 === 甲)
}
