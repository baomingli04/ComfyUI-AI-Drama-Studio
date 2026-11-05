<!-- AI 新增人物弹窗（从 人物设定.vue 拆出的独立组件）：
     说一句要加什么样的人 → AI 按「技能 + 技能引导提示词 + 引入数据」出一份设定
     → 拆成字段填进角色编辑弹窗 → 你确认后才真正加进列表。
     共享数据（剧名 / 集数 / 题材 / 创意 / 方案 / 角色表 / 技能列表）由父组件用 props 传入；
     生成成功后 $emit('生成成功', 文本) 由父组件转给角色编辑弹窗；报错 $emit('报错', e) 回父组件处理；
     显隐用 显示 的 .sync 模式。 -->
<template>
  <el-dialog
    :visible.sync="弹窗显示"
    width="720px"
    top="6vh"
    custom-class="AI新增弹窗"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">AI 新增人物</div>
        <div class="弹窗副题">说一句要加什么样的人，AI 出一份角色设定；生成后先给你改，确认了才进列表</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="弹窗显示 = false"></i>
    </div>
    <div class="弹窗体">
      <!-- ① 技能 -->
      <div class="AI段">
        <div class="AI段头">
          <span class="AI序">1</span><span class="AI段名">技能</span>
          <span class="AI段说">用哪个技能来写这个角色</span>
        </div>
        <el-select v-model="新增技能id" size="small" style="width:320px" placeholder="选一个技能">
          <el-option v-for="技 in 技能列表" :key="技.id" :label="技.名称" :value="技.id"></el-option>
        </el-select>
      </div>

      <!-- ② 技能引导提示词 -->
      <div class="AI段">
        <div class="AI段头">
          <span class="AI序">2</span><span class="AI段名">技能引导提示词</span>
          <span class="AI段说">这次生成额外遵守的规则，只影响这一次</span>
          <div style="flex:1"></div>
          <el-button type="text" size="mini" @click="新增引导 = 新增默认引导">恢复默认</el-button>
        </div>
        <el-input v-model="新增引导" type="textarea" :rows="8"></el-input>
      </div>

      <!-- ③ 要加的人 -->
      <div class="AI段">
        <div class="AI段头">
          <span class="AI序">3</span><span class="AI段名">要加的人</span>
          <span class="AI段说">一句话说清用途：做什么的、制造什么冲突</span>
        </div>
        <el-input
          v-model="新增需求"
          type="textarea"
          :rows="2"
          placeholder="例：加一个守旧的教务处主任，前 2 集不断给主角使绊子，第 3 集被主角当面打脸"></el-input>
      </div>

      <!-- ④ 引入数据 -->
      <div class="AI段">
        <div class="AI段头">
          <span class="AI序">4</span><span class="AI段名">引入数据</span>
          <span class="AI段说">勾上的会随需求一起发给 AI，不勾就不发</span>
          <div style="flex:1"></div>
          <el-button type="text" size="mini" @click="全选新增引入(true)">全选</el-button>
          <el-button type="text" size="mini" @click="全选新增引入(false)">全不选</el-button>
        </div>
        <div v-for="项 in 新增引入" :key="项.键" class="AI引入项">
          <el-checkbox v-model="项.勾选">{{ 项.名 }}</el-checkbox>
          <div class="AI引入值">{{ 项.值 || '（空）' }}</div>
        </div>
      </div>
    </div>
    <div class="弹窗底">
      <el-button @click="弹窗显示 = false">取消</el-button>
      <el-button type="primary" :loading="新增中" @click="生成新角色()">AI 生成这个角色</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { 提交AI任务 } from '@/共用/AI任务'
import { 适配技能id, 读引导, 读技能id, 读引入, 存引入 } from '@/共用/技能生成配置'
import { 规整详, 值文本, 可分段字段 } from '@/共用/人物工具'

// 一行角色的字段顺序，必须和 共用/人物工具.js 的 角色字段 对齐（姓名/性别/年龄/简介已在前面单独占位）
// （与 人物设定.vue 里的同名常量保持一致）
const 行字段 = [
  '性格', '身份', '关系', '态度', '外貌', '身材', '穿搭',
  '身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法',
  '技能', '核心目标', '关系网', '背景故事', '台词风格', '口头禅', '概括'
]

const 行格式说明 = '「角色名｜本剧关系｜性别｜年龄｜一句话简介｜' + 行字段.join('｜') + '」'

// 「AI 新增人物」的默认技能引导提示词：一个角色一行，字段序和编辑弹窗对得上
const 新增默认引导文本 = [
  '1. 你要写的是短剧「新增角色」的角色设定，不是视频/图片提示词：禁止输出 <Picture N>、<Video N>、<Audio N> 之类标签，也不要写镜头运动、光影、音效。',
  '2. 只写一个新角色，一行，格式固定为 ' + 行格式说明 + '，中间用全角竖线 ｜ 分隔，一共 ' + (5 + 行字段.length) + ' 段。',
  '3. 除「外貌/身材/穿搭」外每段都要写满，不许留空；外貌/身材/穿搭三栏一律留空什么都不写（人物长相、发型、发饰、服装全部以美术定装参考图为准，不用文字定义外观）；当前状态/当前姿势/内心想法写成「这一刻」的样子。',
  '4. 会随剧情变的字段按集分段写：第1-5集：旧状态；第6集起：新状态；不变化就写一句话。会变的字段是：' + 可分段字段.join('、') + '。',
  '5. 不许和已有角色重名，也不许和已有角色功能重复；本剧关系要能挂到已选方案的故事线上。',
  '6. 新角色必须有用：要么制造压力/冲突，要么推动爽点，写清他在前几集干什么。',
  '7. 只输出这一行，不要表头、不要解释、不要前后缀。'
].join('\n')

export default {
  name: 'AiXinzengRenwuDialog',
  props: {
    /* 显隐：父组件用 :显示.sync 控制 */
    显示: { type: Boolean, default: false },
    /* 技能下拉（父组件 created 里异步拉取，这里只读） */
    技能列表: { type: Array, default: function () { return [] } },
    /* 本页生成用的技能 id：没单独配过 AI 新增技能时兜底用它 */
    扩写技能id: { type: [String, Number], default: '' },
    /* 拼 AI 需求 / 引入数据用的剧信息 */
    剧名: { type: String, default: '' },
    集数: { type: String, default: '' },
    题材: { type: String, default: '' },
    创意文本: { type: String, default: '' },
    已选方案名: { type: String, default: '' },
    /* 父组件把 已选方案文本() 的结果算好传进来 */
    已选方案文本: { type: String, default: '' },
    总集: { type: Number, default: 0 },
    /* 现有角色清单：给 AI 看，避免重名、避免功能重复 */
    角色表: { type: Array, default: function () { return [] } }
  },
  data() {
    return {
      /* AI 新增人物弹窗 */
      新增技能id: '',
      新增引导: '',
      新增需求: '',
      新增勾选: null,
      新增中: false
    }
  },
  created() {
    this.载入新增配置()
  },
  computed: {
    /* el-dialog 的 :visible.sync 落到父组件的 显示 上 */
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    },
    // 新增弹窗的配置 key 单独一套：生成:/script/character#新增人物
    新增配置类型() {
      return '生成:' + (this.$route.path || '') + '#新增人物'
    },
    新增默认引导() {
      return 新增默认引导文本
    },
    // 现有角色清单：给 AI 看，避免重名、避免功能重复。
    // 会随集数变的字段按「第1-5集：…；第6集起：…」铺开，AI 才知道这个人是怎么长起来的
    现有角色文本() {
      const 行们 = ['角色名｜本剧关系｜性别｜年龄｜一句话简介｜性格｜身份｜关系网']
      const 总 = this.总集
      this.角色表.forEach(人 => {
        if (String(人.资产ID || '').indexOf('CHAR_') !== 0) return
        const 详 = 规整详(人.详)
        行们.push([
          人.名, 人.关系, 人.性别, 人.年龄, 人.简介,
          值文本(详.性格, 总), 值文本(详.身份, 总), 值文本(详.关系网, 总)
        ].join('｜'))
      })
      return 行们.join('\n')
    },
    新增引入() {
      const 勾 = this.新增勾选
      const 项们 = [
        { 键: '标题', 名: '标题（剧名）', 值: this.剧名 },
        { 键: '创意', 名: '一句话创意', 值: this.创意文本 },
        { 键: '方案', 名: '已选方案（' + this.已选方案名 + '）', 值: this.已选方案文本 },
        { 键: '现有角色', 名: '现有角色（别重名、别重复功能）', 值: this.现有角色文本 }
      ]
      // null/undefined = 没配过，默认全选；[] = 用户点过「全不选」，要尊重
      for (let i = 0; i < 项们.length; i++) {
        项们[i].勾选 = 勾 == null ? true : 勾.indexOf(项们[i].键) >= 0
      }
      return 项们
    }
  },
  methods: {
    async 载入新增配置() {
      const 类型 = this.新增配置类型
      this.新增技能id = 适配技能id(this.技能列表, 类型)
      this.新增引导 = 新增默认引导文本
      try {
        const 引导 = await 读引导(类型)
        if (引导) this.新增引导 = 引导
        const 技能 = 读技能id(类型)
        if (技能) this.新增技能id = 技能
        this.新增勾选 = 读引入(类型)
      } catch (e) {
        /* 拉不到就用默认规则 */
      }
    },
    打开AI新增() {
      this.新增需求 = ''
      this.新增引导 = this.新增引导 || 新增默认引导文本
      if (!this.新增技能id) this.新增技能id = this.扩写技能id
      this.$emit('update:显示', true)
    },
    全选新增引入(值) {
      const 项们 = this.新增引入
      const 勾 = []
      if (值) {
        for (let i = 0; i < 项们.length; i++) 勾.push(项们[i].键)
      }
      // 空数组也要存下来：代表「全不选」，不能退化成默认全选
      this.新增勾选 = 勾
    },
    新增参考块() {
      const 项们 = this.新增引入
      const 行们 = []
      for (let i = 0; i < 项们.length; i++) {
        const 项 = 项们[i]
        const 值 = String(项.值 || '').trim()
        if (!项.勾选 || !值) continue
        行们.push('【' + 项.名 + '】\n' + 值)
      }
      if (!行们.length) return ''
      return ['参考数据（前面步骤已经定下来的，必须遵守，不要改动）：'].concat(行们).join('\n')
    },
    async 生成新角色() {
      if (!this.新增技能id) {
        this.$message.warning('请先选一个技能')
        return
      }
      const 参考 = this.新增参考块()
      const 需求 = (参考 ? [参考, ''] : []).concat([
        '剧名：' + this.剧名,
        '集数：' + this.集数 + ' 集',
        '题材：' + this.题材,
        '要生成的内容：给这部剧补一个新角色的设定',
        '要求：' + (this.新增需求.trim() || '按已选方案补一个能制造冲突、推动爽点的新角色')
      ]).join('\n')

      this.新增中 = true
      try {
        const 文本 = String(await 提交AI任务({
          正向: 需求,
          系统: this.新增引导 || 新增默认引导文本,
          技能id: this.新增技能id
        }) || '').trim()
        if (!文本) {
          this.$message.warning('AI 没有返回内容，可稍后重试')
          return
        }
        // 记住这次的技能 / 引导 / 勾选，下次打开还是这套
        const 勾 = []
        const 项们 = this.新增引入
        for (let i = 0; i < 项们.length; i++) {
          if (项们[i].勾选) 勾.push(项们[i].键)
        }
        this.新增勾选 = 勾
        存引入(this.新增配置类型, 勾)
        this.$emit('update:显示', false)
        // 让父组件把 AI 返回的文本填进角色编辑弹窗
        this.$emit('生成成功', 文本)
      } catch (e) {
        // 报错处理（$message + 401 跳登录）在父组件的 扩写报错 里
        this.$emit('报错', e)
      } finally {
        this.新增中 = false
      }
    }
  }
}
</script>

<style scoped>
/* ---- 编辑弹窗骨架 ---- */
.弹窗头 {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding-bottom: 14px; border-bottom: 1px solid var(--描边);
}
.弹窗标题 { font-size: 16px; font-weight: 700; color: var(--字); }
.弹窗副题 { font-size: 12px; color: var(--字弱); margin-top: 4px; }
.弹窗关闭 { cursor: pointer; color: var(--字弱); font-size: 16px; }
.弹窗体 { padding: 16px 0 4px; max-height: 62vh; overflow-y: auto; }
.弹窗底 {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
  padding-top: 14px; border-top: 1px solid var(--描边);
}

/* ---- AI 新增人物弹窗：四段 ---- */
.AI段 { margin-bottom: 18px; }
.AI段:last-child { margin-bottom: 0; }
.AI段头 {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px;
}
.AI序 {
  width: 18px; height: 18px; border-radius: 999px;
  background: var(--主浅); color: var(--主);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex: 0 0 18px;
}
.AI段名 { font-size: 13px; font-weight: 700; color: var(--字); }
.AI段说 { font-size: 12px; color: var(--字弱); }
.AI引入项 {
  padding: 8px 10px;
  border: 1px solid var(--描边);
  border-radius: 8px;
  margin-bottom: 8px;
  background: var(--卡片二);
}
.AI引入项:last-child { margin-bottom: 0; }
.AI引入值 {
  margin-top: 4px;
  max-height: 96px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.7;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
