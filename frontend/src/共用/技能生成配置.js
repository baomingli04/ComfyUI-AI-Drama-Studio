// 技能生成配置：每页「用哪个技能 + 该技能的引导提示词」。
//
// 引导提示词走现成的 /api/提示词/配置，按「页面:技能id」各存一份
// （类型 = 生成:<前端路由>:<技能id>，如 生成:/script/episode:12）——
// 一个页面可以配多个技能，每个技能有自己的引导提示词；
// 老版本是整页一份（类型 无技能后缀），读不到按技能那份时会回退读它，兼容历史数据。
// 「本页上次选的技能id」记在 localStorage，保存时也一并 POST 上去（后端现在会忽略多余字段）。
import { 取, 发 } from '@/接口/请求'

const 技能键前缀 = '技能生成:技能id:'
const 引入键前缀 = '技能生成:引入:'
const 创意键前缀 = '技能生成:创意:'

// 后端按页面存配置的 key，形如 生成:/script/new
export function 取配置类型(路由) {
  return '生成:' + (路由 || '')
}

// 读引导提示词：优先读「页面:技能id」那份；没存过回退读整页那份（老数据）。
// 技能id 不传时用 localStorage 里本页上次选的技能。
export async function 读引导(类型, 技能id) {
  const id = 技能id || 读技能id(类型)
  try {
    if (id) {
      const 数据 = await 取('/api/提示词/配置?类型=' + encodeURIComponent(类型 + ':' + id))
      if (数据 && 数据.内容) return 数据.内容
    }
    // 回退：整页一份的老 key
    const 数据2 = await 取('/api/提示词/配置?类型=' + encodeURIComponent(类型))
    return (数据2 && 数据2.内容) || ''
  } catch (e) {
    // 拉不到就当没配过，不阻塞页面
    return ''
  }
}

// 保存引导提示词：写到「页面:技能id」这份，同时记住本页选的技能
export async function 存配置(类型, 技能id, 引导) {
  await 发('/api/提示词/配置/保存', {
    类型: 类型 + ':' + (技能id || ''),
    内容: 引导 || '',
    技能id: 技能id || ''
  })
  try {
    localStorage.setItem(技能键前缀 + 类型, String(技能id || ''))
  } catch (e) {
    /* 隐私模式下 localStorage 可能不可写，忽略 */
  }
}

// 只记住本页/本场景选的技能 id（不落库引导词）
export function 记技能id(类型, 技能id) {
  try {
    localStorage.setItem(技能键前缀 + 类型, String(技能id || ''))
  } catch (e) {
    /* 忽略 */
  }
}

// 读本页上次选的技能 id
export function 读技能id(类型) {  try {
    return localStorage.getItem(技能键前缀 + 类型) || ''
  } catch (e) {
    return ''
  }
}

// ---- 默认技能适配：页面第一次选技能时不死选第一个，而是选「最适配」的 ----
// 每个页面一组匹配关键词，对技能 名称(×3)/分类名称(×2)/简介(×1) 打分，分高者当选；
// 都打不到分就回退列表第一个（后端按 id 倒序，即最新的）。
const 适配关键词表 = {
  '/script/new': ['创意', '脑洞', '灵感', '梗概', '策划'],
  '/script/plan': ['方案', '策划', '梗概', '钩子'],
  '/script/detail': ['方案', '策划', '卖点', '结构'],
  '/script/character': ['人物', '角色', '人设', '设定', '框架'],
  '/script/outline': ['大纲', '分集', '钩子', '卡点', '节奏', '每集'],
  '/script/episode': ['剧本', '单集', '场次', '可拍'],
  '/video/shot': ['分镜', '镜头', '节拍', '脚本'],
  '/video/assets': ['资产', '文生图', '图片', '出图', '形象'],
  // /video/art 的 AI 编辑按任务类型各配默认关键词（子场景键必须排在 /video/art 之前才会先命中）
  '/video/art:三图编辑一致版': ['一致性', '改图', '编辑', '修图', '提示词'],
  '/video/art:多图编辑多人合并版': ['多人', '合并', '融合', '人物', '一致'],
  '/video/art:动漫转真人': ['真人', '写实', '风格转换', '动漫', '真人化'],
  '/video/art': ['图片', '扩写', '提示词', '出图', '绘图'],
  // /video/director 的扩写按生成方式各配默认关键词（子场景键必须排在 /video/director 之前才会先命中）
  '/video/director:图生视频': ['图生视频', '首帧', '视频', '提示词'],
  '/video/director:文生视频': ['文生视频', '文生', '视频'],
  '/video/director:首尾帧': ['首尾帧', '首尾', '视频'],
  '/video/director:参考主体': ['参考主体', '一致性', '参考', '视频'],
  '/video/director:视频转视频': ['视频转视频', '重绘', '视频'],
  '/video/director:参考改视频': ['参考改', '换装', '视频'],
  '/video/director:参考生视频': ['参考', '视频', '提示词'],
  '/video/director:多参考生视频': ['多参考', '多人', '同框', '视频'],
  '/video/director:二采重绘': ['重绘', '二采', '改视频', '视频'],
  '/video/director': ['视频', '提示词', '出片', '运镜', '导演']
}

export function 适配技能id(技能列表, 配置类型) {
  const 列 = 技能列表 || []
  if (!列.length) return ''
  const 路由 = String(配置类型 || '').replace(/^生成:/, '')
  // 支持子场景前缀：/script/character:新增 也命中 /script/character 那组关键词
  let 关键词们 = null
  for (const 键 in 适配关键词表) {
    if (路由 === 键 || 路由.indexOf(键 + ':') === 0) { 关键词们 = 适配关键词表[键]; break }
  }
  if (!关键词们 || !关键词们.length) return 列[0].id
  let 首选 = null
  let 首分 = -1
  for (let i = 0; i < 列.length; i++) {
    const 技 = 列[i]
    const 名 = String(技.名称 || '')
    const 类 = String(技.分类名称 || '')
    const 简 = String(技.简介 || '')
    let 分 = 0
    for (let j = 0; j < 关键词们.length; j++) {
      const 词 = 关键词们[j]
      if (名.indexOf(词) >= 0) 分 += 3
      if (类.indexOf(词) >= 0) 分 += 2
      if (简.indexOf(词) >= 0) 分 += 1
    }
    // 同分保持先到先得（列表靠前的优先）
    if (分 > 首分) { 首分 = 分; 首选 = 技 }
  }
  return (首分 > 0 ? 首选 : 列[0]).id
}

// ---- 引入数据：哪些上下文数据要跟着需求一起发给 AI（按「区」各记一份）----

// 返回 null = 这个区没存过，调用方按「默认全选」处理
export function 读引入(类型) {
  try {
    const 原 = localStorage.getItem(引入键前缀 + 类型)
    if (!原) return null
    const 值 = JSON.parse(原)
    return Array.isArray(值) ? 值 : null
  } catch (e) {
    return null
  }
}

export function 存引入(类型, 键们) {
  try {
    localStorage.setItem(引入键前缀 + 类型, JSON.stringify(键们 || []))
  } catch (e) {
    /* 忽略 */
  }
}

// ---- 一句话创意：剧本里填过的会随路由带过来；直接开链接时用户可在「引入数据」里补，按剧名记住 ----

export function 读创意(剧名) {
  try {
    return localStorage.getItem(创意键前缀 + (剧名 || '')) || ''
  } catch (e) {
    return ''
  }
}

export function 存创意(剧名, 值) {
  try {
    localStorage.setItem(创意键前缀 + (剧名 || ''), 值 || '')
  } catch (e) {
    /* 忽略 */
  }
}
