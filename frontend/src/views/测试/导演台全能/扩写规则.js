// 导演台全能的「每模式一套扩写规则」。
//
// 为什么按模式分：h3-prompt-writing 技能本身分模式，T2VA / FL2VA(I2VA) / Ref2VA 三种
// 写法的字段结构完全不同（三段式 vs 对齐行+三段式 vs 六段式），用一套规则扩写必然串模式。
// 所以本页按 表单.模式 切六份规则，后端也按模式给不同的 system 提示：
//   t2v  → single_frame（0 张图 → 后端走 T2VA 分支）
//   i2v  → single_frame（1 张图 → I2VA）
//   fl2v → single_frame（1 张图 → I2VA；2 张图 → FL2VA）
//   r2v  → multi_reference（ref-en.txt 六段式）
//   v2v  → single_frame（0 张图 → T2VA 三段式，但正文必须引用 <Video 1>）
//   rv2v → multi_reference（六段式，改的是 <Video 1>，素材来自 <Picture N> / <Audio N>）
//
// 文本放在 扩写规则.json：前端读它当默认规则，后端种子脚本读它写库，一份数据两处用。
// 这六份只是「库里没存本模式配置时的兜底」；用户在「扩写提示词配置」里改过之后，
// 以库里的 扩写:/test/d-all:<模式> 那行为准（改完即时存库，见 扩写行 组件）。
import 规则包 from './扩写规则.json'

const 拼 = 行们 => (行们 || []).join('\n')

// 模式 → 默认规则（库里没存本模式配置时用这套）。
// 用遍历而不是逐条写死：以后 JSON 里加模式，这里不用再改一次（写死过三份，加模式时漏掉过）。
export const 默认规则集 = Object.keys(规则包.规则 || {}).reduce((表, 模式) => {
  表[模式] = 拼(规则包.规则[模式])
  return 表
}, {})

// 模式 → 后端扩写模式（决定读 base-en.txt 还是 ref-en.txt，也决定 T2VA/I2VA/FL2VA 分支）
export const 扩写模式集 = 规则包.扩写模式

// 模式 → 页面上的「本模式要填什么」提示
export const 模式说明集 = 规则包.模式说明
