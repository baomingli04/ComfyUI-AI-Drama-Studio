// 分集目录页的节奏 / 钩子算法。
// 关键约定：钩子台账不单独存一份，全部由每集的「点位」派生，避免两处数据打架。
// 这里只放纯函数，不碰 Vue，页面和组件都可以引。

/* 七种钩子动作。假兑 = 看着兑现了其实没兑，必须在后面三集内补一次真兑。 */
export const 钩子类型们 = ['埋', '露', '压', '兑', '假兑', '回收', '转']

/* 类型配色（色板取自 全局主题.css，同色系深浅） */
export const 钩子色 = {
  埋: '#60a5fa',
  露: '#818cf8',
  压: '#ef4444',
  兑: '#22c55e',
  假兑: '#f59e0b',
  回收: '#2dd4bf',
  转: '#c084fc'
}

/* 情绪分 → 颜色：1–2 红（低谷）、3 黄、4–5 绿 */
export function 情绪色(分) {
  const 值 = Number(分) || 0
  if (值 <= 2) return '#ef4444'
  if (值 === 3) return '#f59e0b'
  return '#22c55e'
}

/* 取字符串的全部三字片段，用来做「埋 ↔ 兑」的内容初筛 */
function 三字集(文) {
  const 集 = new Set()
  const 串 = String(文 || '')
  for (let i = 0; i < 串.length - 2; i++) 集.add(串.slice(i, i + 3))
  return 集
}

/* 台账：行 = 动作类型，列 = 集号，格 = 该集该类型的点位数组 */
export function 建台账(集们) {
  const 表 = {}
  钩子类型们.forEach(类 => { 表[类] = {} })
  ;(集们 || []).forEach(集 => {
    ;(集.点位 || []).forEach(点 => {
      if (!表[点.类型]) 表[点.类型] = {}
      if (!表[点.类型][集.集]) 表[点.类型][集.集] = []
      表[点.类型][集.集].push(点)
    })
  })
  return 表
}

/* 未回收：埋了，但全剧找不到对应的兑 / 假兑 / 转 / 回收。
   只是内容三字重叠的初筛——像「埋 小组积分制」→「转 轮值小队长制」这种升级关系
   字符串比不出来，所以点位支持手动标「已关联」（点位.已关联 = true）。 */
export function 找未回收(集们) {
  const 表 = 建台账(集们)
  const 兑文 = []
  ;['兑', '假兑', '转', '回收'].forEach(类 => {
    const 行 = 表[类] || {}
    Object.keys(行).forEach(集号 => {
      行[集号].forEach(点 => 兑文.push(三字集(点.内容)))
    })
  })
  const 出 = []
  const 行 = 表['埋'] || {}
  Object.keys(行).forEach(集号 => {
    行[集号].forEach(点 => {
      if (点.已关联) return
      const 己 = 三字集(点.内容)
      let 命中 = false
      兑文.forEach(组 => {
        if (命中) return
        己.forEach(片 => { if (组.has(片)) 命中 = true })
      })
      if (!命中) 出.push({ 集: Number(集号), 点: 点.点, 内容: 点.内容 })
    })
  })
  return 出
}

/* 连续低谷：情绪分连续 ≥2 集都 ≤2 的区间，返回 [{起, 止}]（集号） */
export function 连续低谷(集们) {
  const 列 = (集们 || []).filter(集 => typeof 集.情绪分 === 'number')
  const 段 = []
  let 起 = null
  for (let i = 0; i < 列.length; i++) {
    const 低 = 列[i].情绪分 <= 2
    if (低 && 起 === null) 起 = i
    if (!低 && 起 !== null) {
      if (i - 起 >= 2) 段.push({ 起: 列[起].集, 止: 列[i - 1].集 })
      起 = null
    }
  }
  if (起 !== null && 列.length - 起 >= 2) 段.push({ 起: 列[起].集, 止: 列[列.length - 1].集 })
  return 段
}

/* 按梗概里的冲突词 + 关键/卡点，给一个 1–5 的初值。
   新增集用它兜底，用户可以随时改。 */
export function 估情绪分(集) {
  const 文 = String((集 && 集.梗概) || '')
  const 冲突词 = ['打', '战', '追', '逃', '崩', '怒', '哭', '血', '杀', '爆', '反', '揭', '断', '撕', '抢', '逼', '威胁', '死', '摔', '吼']
  let 分 = 3
  let 命中 = 0
  冲突词.forEach(词 => { if (文.indexOf(词) >= 0) 命中++ })
  if (命中 >= 2) 分 += 1
  if (命中 >= 4) 分 += 1
  if (集 && (集.关键 || 集.卡点)) 分 += 1
  if (分 > 5) 分 = 5
  if (分 < 1) 分 = 1
  return 分
}
