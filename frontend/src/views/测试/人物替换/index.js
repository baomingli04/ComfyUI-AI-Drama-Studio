import { 发, 取 } from '@/接口/请求'
import 混入 from '@/共用/任务页混入'
import 运行日志弹窗 from '@/views/共用/运行日志弹窗/index.vue'
import 媒体缩略图 from '@/共用/媒体缩略图/index.vue'
import 媒体预览弹窗 from '@/共用/媒体预览弹窗/index.vue'
import 扩写行 from '@/共用/扩写行/index.vue'
import 提示词单元格 from '@/共用/提示词单元格/index.vue'

// 三个快捷按钮写死的提示词（多参考 Ref2VA 六段式）。
// 规范：技能 h3-prompt-writing/references/ref-en.txt、video-prompt-studio-v2/参考文档/分镜规则.md §3；
// 写法对齐工作流 H3-全能参考生视频（图9视频3音频3）.json 节点 138 自带的替换人物范例。
// 素材口径：<Picture 1> = 上传的参考图（替换素材）；<Video 1> = 上传的原视频（被替换的素材，只作源视频、不另立 Subject）。
// <Video 1> 的职责 = 动作 + 运镜 + 整体时序结构 + 没被替换掉的那部分画面（替换人物时=场景与背景；替换背景时=人物）
//             + 原声（环境音与动作音效；另传了新音频才改）。
const 快捷提示词 = {
  替换人物: `subject_definitions:
<Subject 1> 是目标视频中的人物，其长相、发型、服装等外观特征取自参考图 <Picture 1>；其动作、姿态与镜头运动来自原视频 <Video 1>。
<Video 1> 是原视频，提供人物的动作、运镜与整体时序结构，以及全程沿用的场景、背景与原声（环境音与动作音效）。

summary:
[video editing + reference generation] 把原视频 <Video 1> 里的人物替换成 <Subject 1> 的外貌（来自参考图 <Picture 1>），保留原视频的动作、镜头、场景与声音，生成一段人物已替换的新视频。

retention_analysis:
<Subject 1> 使用 attribute_transfer —— 将参考图 <Picture 1> 中的人物外貌（脸、发型、服装）转移应用到原视频 <Video 1> 中的人物主体上。
<Video 1> 的动作、运镜、场景结构与原声保持不变，作为时序结构与声音来源参考。

detailed_description:
[Shot 1] <Subject 1> 在原视频 <Video 1> 的场景中做出与原视频一致的动作与运镜，人物的脸、发型、服装与参考图 <Picture 1> 完全一致，背景与光线沿用原视频，全程保持一致、不更换背景。

overall_soundscape:
沿用原视频 <Video 1> 的原声：环境音与动作音效贯穿全片。

non_diegetic_music:
无额外背景音乐。`,

  替换背景: `subject_definitions:
<Subject 1> 是目标视频中的场景与背景，其环境结构、陈设、光线与色调取自参考图 <Picture 1>；人物、动作与镜头运动沿用原视频 <Video 1>。
<Video 1> 是原视频，提供人物的形象、动作、运镜与整体时序结构，以及全程沿用的原声（环境音与动作音效）。

summary:
[video editing + reference generation] 把原视频 <Video 1> 里的背景替换成参考图 <Picture 1> 中的场景（<Subject 1>），保留原视频的人物、动作、镜头运动与声音，生成一段背景已替换的新视频。

retention_analysis:
<Subject 1> 使用 attribute_transfer —— 将参考图 <Picture 1> 中的场景与背景转移应用到原视频 <Video 1> 的画面背景上。
<Video 1> 的人物、动作与运镜、原声保持不变，作为时序结构与声音来源参考。

detailed_description:
[Shot 1] 背景固定为 <Subject 1>，全程保持一致、不更换背景。<Video 1> 中的人物在替换后的场景里做出与原视频一致的动作与运镜，人物的脸、发型、服装与光影沿用原视频，人物与背景衔接自然、光影统一，无抠图痕迹、无接缝、无重影。

overall_soundscape:
沿用原视频 <Video 1> 的原声：环境音与动作音效贯穿全片。

non_diegetic_music:
无额外背景音乐。`,

  替换人物和背景: `subject_definitions:
<Subject 1> 是目标视频中的人物，其长相、发型、服装等外观特征取自参考图 <Picture 1>。
<Subject 2> 是目标视频中的场景与背景，其环境结构、陈设、光线与色调取自参考图 <Picture 1>。
<Video 1> 是原视频，提供人物的动作、运镜与整体时序结构，以及全程沿用的原声（环境音与动作音效）。

summary:
[video editing + reference generation] 用参考图 <Picture 1> 中的人物与背景整体替换原视频 <Video 1> 里的人物与背景：人物取 <Subject 1>、背景取 <Subject 2>，仅保留原视频的动作、运镜、时序结构与声音。

retention_analysis:
<Subject 1> 使用 attribute_transfer —— 将参考图 <Picture 1> 中的人物外貌（脸、发型、服装）转移应用到原视频 <Video 1> 的人物主体上。
<Subject 2> 使用 attribute_transfer —— 将参考图 <Picture 1> 中的场景与背景转移应用到原视频 <Video 1> 的画面背景上。
<Video 1> 的动作、运镜与时序结构、原声保持不变，作为时序结构与声音来源参考。

detailed_description:
[Shot 1] <Subject 1> 在 <Subject 2> 的场景中做出与原视频一致的动作与运镜，人物的脸、发型、服装与背景均与参考图 <Picture 1> 完全一致；背景固定为 <Subject 2>，全程保持一致、不更换背景，人物与背景衔接自然、光影统一，无抠图痕迹、无接缝、无重影。

overall_soundscape:
沿用原视频 <Video 1> 的原声：环境音与动作音效贯穿全片。

non_diegetic_music:
无额外背景音乐。`
}

export default {
  name: 'T6人物替换页',
  mixins: [混入],
  components: { 'run-log-dialog': 运行日志弹窗, 'media-thumbs': 媒体缩略图, 'media-preview': 媒体预览弹窗, 'ai-expand': 扩写行, 'prompt-cell': 提示词单元格 },
  data() {
    return {
      提交中: false,
      扩写模式: 'multi_reference',
      表单: { 输入图1: '', 输入图2: '', 正向提示词: '' }
    }
  },
  methods: {
    套用快捷提示词(名称) {
      const 文本 = 快捷提示词[名称]
      if (!文本) return
      this.$set(this.表单, '正向提示词', 文本)
    },
    图成功(序号, 响应) {
      if (响应.ok) {
        this.$set(this.表单, '输入图' + 序号, 响应.路径)
      } else {
        this.$message.error(响应.error || '上传失败')
      }
    },
    async 提交任务() {
      if (!this.表单.输入图1 || !this.表单.输入图2) {
        this.$message.warning('底图和人物参考图都要上传')
        return
      }
      this.提交中 = true
      try {
        const 数据 = await 发('/api/任务/提交', Object.assign({ 类型: '人物替换' }, this.表单))
        this.$message.success('任务已提交，id=' + 数据.id)
        this.拉任务列表()
      } catch (e) {
        this.报错(e)
      } finally {
        this.提交中 = false
      }
    },
    async 拉任务列表() {
      try {
        const 数据 = await 取('/api/任务列表?类型=' + encodeURIComponent('人物替换'))
        this.任务列表 = 数据.列表
      } catch (e) {
        this.报错(e)
      }
    }
  }
}
