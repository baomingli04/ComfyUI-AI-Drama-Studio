<!-- 角色表单弹窗（从 人物设定.vue 拆出的独立组件）：新增和编辑共用一套字段。
     新增时标题写「新增角色」，底部是「加入人物设定」；编辑时是「保存」+ 左侧「删除」。
     共享数据（角色表 / 关系表 / 选中角色 / 关系筛选）由父组件用 props 传入；
     保存 / 加入 成功后 $emit('已保存') 让父组件落库；显隐用 显示 的 .sync 模式。 -->
<template>
  <el-dialog
    :visible.sync="弹窗显示"
    width="680px"
    top="6vh"
    custom-class="角色编辑弹窗"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">{{ 新增模式 ? '新增角色' : '编辑角色 · ' + 草稿.名 }}</div>
        <div class="弹窗副题">{{ 新增模式 ? '填完点「加入人物设定」，这张卡会出现在「本剧角色」里' : '改完点保存，直接写回这张角色卡。会随剧情变的字段点「按集拆分」，写成第1-5集 / 第6-8集' }}</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="弹窗显示 = false"></i>
    </div>
    <div class="弹窗体">
      <div v-if="新增原文" class="AI原文">
        <div class="行间" style="margin-bottom:6px">
          <span class="AI原文标">AI 原文</span>
          <span class="AI原文注">下面各字段是从这段原文里拆出来的，拆错了直接改字段</span>
          <div style="flex:1"></div>
          <el-button type="text" size="mini" @click="新增原文 = ''">收起</el-button>
        </div>
        <pre class="原文">{{ 新增原文 }}</pre>
      </div>
      <el-form label-width="76px" size="small">
        <el-form-item label="名">
          <el-input v-model="草稿.名" maxlength="20" placeholder="角色名，别和已有角色重名"></el-input>
        </el-form-item>
        <el-form-item label="本剧关系">
          <el-input v-model="草稿.关系" maxlength="20" placeholder="主角 / 核心成员 / 功能性角色 / 反派"></el-input>
        </el-form-item>
        <el-form-item label="性别">
          <el-input v-model="草稿.性别" maxlength="4"></el-input>
        </el-form-item>
        <el-form-item label="年龄">
          <el-input v-model="草稿.年龄" maxlength="6"></el-input>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="草稿.简介" type="textarea" :autosize="{ minRows: 1, maxRows: 3 }"></el-input>
        </el-form-item>
      </el-form>

      <!-- 详情字段按 字段分组 铺：基本信息 / 外形 / 当前状态 / 能力与目标 / 关系 / 背景与台词 -->
      <div v-for="组 in 编辑分组" :key="'编' + 组.名" class="编辑组">
        <div class="编辑组名">{{ 组.名 }}</div>
        <el-form label-width="76px" size="small">
          <el-form-item v-for="键 in 组.字段" :key="键" :label="String(键)">
            <!-- 分阶段：一条字段拆成「第1-5集 / 第6-8集」几段，各自一个值 -->
            <div v-if="是分段值(键)" class="段编辑列">
              <div v-for="(段, 序) in 草稿.详[键]" :key="序" class="段编辑行">
                <span class="段编辑字">第</span>
                <el-input-number
                  v-model="段.起" :min="1" :max="总集" :controls="false"
                  size="mini" style="width:54px"></el-input-number>
                <span class="段编辑字">–</span>
                <el-input-number
                  v-model="段.止" :min="1" :max="总集" :controls="false"
                  size="mini" style="width:54px"></el-input-number>
                <span class="段编辑字">集</span>
                <el-input
                  v-model="段.值"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 3 }"
                  class="段编辑值"></el-input>
                <i class="el-icon-close 段编辑删" title="删掉这一段" @click="删一段(键, 序)"></i>
              </div>
              <div class="段编辑底">
                <el-button type="text" size="mini" icon="el-icon-plus" @click="加一段(键)">加一段</el-button>
                <el-button type="text" size="mini" @click="合并字段(键)">合并成单值</el-button>
              </div>
            </div>
            <!-- 单值：全剧不变，一句话写完 -->
            <template v-else>
              <el-input
                v-model="草稿.详[键]"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 4 }"></el-input>
              <el-button
                v-if="可分段(键)"
                type="text"
                size="mini"
                class="拆分钮"
                @click="拆分字段(键)">按集拆分（会随剧情变就拆）</el-button>
            </template>
          </el-form-item>
        </el-form>
      </div>
    </div>
    <div class="弹窗底">
      <el-button v-if="!新增模式" type="text" class="删除钮" @click="$emit('删除', 编辑对象)">删除这个角色</el-button>
      <div style="flex:1"></div>
      <el-button @click="弹窗显示 = false">取消</el-button>
      <el-button type="primary" @click="保存角色()">{{ 新增模式 ? '加入人物设定' : '保存' }}</el-button>
    </div>
  </el-dialog>
</template>

<script>
import {
  字段分组, 可分段字段, 空角色详, 规整详, 规整段, 是分段,
  拆分段, 合分段, 集标签, 文本转值
} from '@/共用/人物工具'

// 一行角色的字段顺序，必须和 共用/人物工具.js 的 角色字段 对齐（姓名/性别/年龄/简介已在前面单独占位）
// （与 人物设定.vue 里的同名常量保持一致，供 填入新角色 按列对号入座）
const 行字段 = [
  '性格', '身份', '关系', '态度', '外貌', '身材', '穿搭',
  '身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法',
  '技能', '核心目标', '关系网', '背景故事', '台词风格', '口头禅', '概括'
]

// 新角色卡的配色盘（和假数据里的暗色系一致；与 人物设定.vue 保持同一套）
const 角色色盘 = ['#3b4a63', '#35435a', '#3f4652', '#4a3b57', '#524033', '#334a45', '#3a4a52', '#2f3a4a']

// 一行文本按 ｜ 拆成字段：先认全角竖线，再退到半角 |、再退到制表符
function 拆行(文本) {
  const 行 = String(文本 || '').split(/\r?\n/).map(s => s.trim()).filter(s => s)
  for (let i = 0; i < 行.length; i++) {
    let 段 = 行[i].split('｜')
    if (段.length < 3) 段 = 行[i].split('|')
    if (段.length < 3) 段 = 行[i].split('\t')
    if (段.length >= 3) return 段.map(s => s.trim())
  }
  return []
}

export default {
  name: 'JueseEditDialog',
  props: {
    /* 显隐：父组件用 :显示.sync 控制 */
    显示: { type: Boolean, default: false },
    总集: { type: Number, default: 0 },
    /* 共享数据：父组件的人物列表 / 关系网（数组引用，弹窗内直接读写同一份） */
    角色表: { type: Array, default: function () { return [] } },
    关系表: { type: Array, default: function () { return [] } },
    选中角色: { type: Object, default: null },
    关系筛选: { type: String, default: '全部' }
  },
  data() {
    return {
      /* 角色表单弹窗（新增 / 编辑共用） */
      新增模式: false,
      编辑对象: null,
      新增原文: '',
      草稿: { 名: '', 关系: '', 性别: '', 年龄: '', 简介: '', 详: 空角色详() }
    }
  },
  computed: {
    /* el-dialog 的 :visible.sync 落到父组件的 显示 上 */
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    },
    // 编辑弹窗里的详情字段：按 字段分组 铺；姓名/性别/年龄 顶部已经单独有输入框，这里跳过
    编辑分组() {
      const 跳 = ['姓名', '性别', '年龄']
      return 字段分组.map(function (组) {
        return {
          名: 组.名,
          字段: 组.字段.filter(function (键) { return 跳.indexOf(键) < 0 })
        }
      }).filter(function (组) { return 组.字段.length > 0 })
    }
  },
  methods: {
    打开编辑(人) {
      if (!人) return
      this.新增模式 = false
      this.新增原文 = ''
      this.编辑对象 = 人
      this.草稿 = JSON.parse(JSON.stringify({
        名: 人.名, 关系: 人.关系, 性别: 人.性别, 年龄: 人.年龄,
        简介: 人.简介, 详: 规整详(人.详)
      }))
      this.$emit('update:显示', true)
    },
    // 手动新增：空白草稿，字段和编辑一样（23 个字段先铺满，缺的显示空）
    打开新增() {
      this.新增模式 = true
      this.新增原文 = ''
      this.编辑对象 = null
      this.草稿 = {
        名: '', 关系: '功能性角色', 性别: '', 年龄: '', 简介: '',
        详: 空角色详()
      }
      this.$emit('update:显示', true)
    },
    /* ---- 编辑弹窗里的「按集分段」：把一句话拆成第1-5集 / 第6-8集几段 ---- */
    // 这个字段允不允许按集拆分（姓名/性别/年龄这种永远不变的就不给按钮）
    可分段(键) {
      return 可分段字段.indexOf(键) >= 0
    },
    // 草稿的这个字段现在是不是分段形态
    是分段值(键) {
      return 是分段(this.草稿 && this.草稿.详 ? this.草稿.详[键] : '')
    },
    // 单值 → 分段：先包成「第1集到最后一集」的一段，再自己拆
    拆分字段(键) {
      this.草稿.详[键] = 拆分段(this.草稿.详[键], this.总集)
    },
    // 分段 → 单值：取最新一段，并说清取的是哪一段（不静默丢信息）
    合并字段(键) {
      const 段们 = 规整段(this.草稿.详[键], this.总集)
      const 末 = 段们[段们.length - 1]
      this.草稿.详[键] = 合分段(this.草稿.详[键], this.总集)
      if (末) {
        this.$message({
          message: '已合并成单值，取的是「' + 集标签(末.起, 末.止, this.总集) + '」这一段',
          type: 'info'
        })
      }
    },
    // 加一段：从上一段结束的下一集开始，到最后一集
    加一段(键) {
      const 段们 = 规整段(this.草稿.详[键], this.总集)
      const 末 = 段们[段们.length - 1]
      const 起 = 末 ? Math.min(末.止 + 1, this.总集) : 1
      this.草稿.详[键] = 段们.concat([{ 起: 起, 止: this.总集, 值: '', 类型: '', 说明: '' }])
    },
    删一段(键, 序) {
      const 段们 = 规整段(this.草稿.详[键], this.总集)
      if (段们.length <= 1) {
        this.$message.warning('至少留一段；想变回一句话就点「合并成单值」')
        return
      }
      段们.splice(序, 1)
      this.草稿.详[键] = 段们
    },
    保存角色() {
      if (this.新增模式) {
        this.加入角色()
        return
      }
      const 人 = this.编辑对象
      if (!人) {
        this.$emit('update:显示', false)
        return
      }
      const 旧名 = 人.名
      人.名 = this.草稿.名
      人.关系 = this.草稿.关系
      人.性别 = this.草稿.性别
      人.年龄 = this.草稿.年龄
      人.简介 = this.草稿.简介
      // 详情里的姓名/性别/年龄跟着顶部改，避免两处对不上
      人.详 = Object.assign({}, 规整详(人.详), 规整详(this.草稿.详), {
        姓名: this.草稿.名, 性别: this.草稿.性别, 年龄: this.草稿.年龄
      })
      // 改名要带着关系网一起改，否则边会指向一个不存在的角色
      if (旧名 && 人.名 && 旧名 !== 人.名) {
        this.关系表.forEach(function (边) {
          if (边.甲 === 旧名) 边.甲 = 人.名
          if (边.乙 === 旧名) 边.乙 = 人.名
        })
        if (this.关系筛选 === 旧名) this.$emit('update:关系筛选', '全部')
      }
      this.$emit('update:显示', false)
      this.$emit('已保存')
      this.$message.success('已保存「' + 人.名 + '」的设定')
    },
    // 新角色的 资产ID / id 接着现有的往下排，别和已有角色撞号
    下一个角色编号() {
      let 最大 = 0
      let 最大id = 0
      this.角色表.forEach(人 => {
        if (人.id > 最大id) 最大id = 人.id
        const 号 = parseInt(String(人.资产ID || '').replace('CHAR_', ''), 10)
        if (!isNaN(号) && 号 > 最大) 最大 = 号
      })
      return { 号: 最大 + 1, id: 最大id + 1 }
    },
    加入角色() {
      const 名 = (this.草稿.名 || '').trim()
      if (!名) {
        this.$message.warning('先给这个角色起个名')
        return
      }
      const 编 = this.下一个角色编号()
      const 新 = {
        分组: '本剧角色',
        来源: this.新增原文 ? 'AI新增' : '手动新增',
        id: 编.id,
        资产ID: 'CHAR_' + String(编.号).padStart(3, '0'),
        关系: this.草稿.关系 || '功能性角色',
        名: 名,
        性别: this.草稿.性别 || '-',
        年龄: this.草稿.年龄 || '-',
        简介: this.草稿.简介 || '',
        色: 角色色盘[(编.号 - 1) % 角色色盘.length],
        详: Object.assign({}, 规整详(this.草稿.详), {
          姓名: 名, 性别: this.草稿.性别 || '-', 年龄: this.草稿.年龄 || '-'
        })
      }
      this.角色表.push(新)
      this.$emit('update:选中角色', 新)
      this.$emit('update:显示', false)
      this.$emit('已保存')
      this.$message.success('已把「' + 名 + '」加进人物设定')
    },
    // 把 AI 返回的一行文本拆成表单字段，拆不出来就把原文塞进简介，让人工接着改
    // （AI 新增人物弹窗生成成功后，由父组件转调到这里打开本弹窗）
    填入新角色(文本) {
      const 段 = 拆行(文本)
      const 详 = 空角色详()

      const 草 = { 名: '', 关系: '功能性角色', 性别: '', 年龄: '', 简介: '', 详: 详 }
      if (段.length >= 3) {
        草.名 = 段[0] || ''
        草.关系 = 段[1] || '功能性角色'
        草.性别 = 段[2] || ''
        草.年龄 = 段[3] || ''
        草.简介 = 段[4] || ''
        // 从第 6 段开始按 行字段 的顺序对号入座（和默认引导里写的格式一致）。
        // 值里如果带了「第1-5集：…；第6集起：…」，顺手拆成分段，编辑弹窗里直接就是时间轴
        for (let i = 0; i < 行字段.length; i++) {
          const 值 = 段[5 + i]
          if (值) 详[行字段[i]] = 文本转值(值, this.总集)
        }
      } else {
        // 格式没认出来：名字留空让人填，原文整段放进简介当参考
        草.简介 = 文本
      }
      详.姓名 = 草.名
      详.性别 = 草.性别
      详.年龄 = 草.年龄

      this.新增模式 = true
      this.编辑对象 = null
      this.新增原文 = 文本
      this.草稿 = 草
      this.$emit('update:显示', true)
      this.$message.success(段.length >= 3 ? 'AI 已出新角色，确认后再点「加入人物设定」' : 'AI 格式没认出来，已把原文放进表单，手动改一下')
    }
  }
}
</script>

<style scoped>
/* ---- 编辑弹窗 ---- */
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
.删除钮 { color: #ef4444; }

/* 编辑弹窗里的字段分组 */
.编辑组 {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--描边);
}
.编辑组名 {
  font-size: 12px;
  font-weight: 600;
  color: var(--主);
  margin-bottom: 8px;
}

/* 编辑弹窗里的分段编辑器：第 [起] – [止] 集 [值] × */
.段编辑列 { width: 100%; }
.段编辑行 { display: flex; align-items: flex-start; gap: 6px; margin-bottom: 6px; }
.段编辑字 { font-size: 12px; color: var(--字弱); line-height: 28px; white-space: nowrap; }
.段编辑值 { flex: 1; min-width: 0; }
.段编辑删 { cursor: pointer; color: var(--字弱); line-height: 28px; }
.段编辑删:hover { color: #ef4444; }
.段编辑底 { display: flex; align-items: center; gap: 10px; }
.拆分钮 { margin-top: 2px; padding: 0; }

/* 新增角色时摊开的 AI 原文：方便对照是哪个字段拆歪了 */
.AI原文 {
  background: var(--卡片二);
  border: 1px solid var(--描边);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 14px;
}
.AI原文标 { font-size: 12px; font-weight: 700; color: var(--主); }
.AI原文注 { font-size: 12px; color: var(--字弱); }
.AI原文 .原文 {
  margin: 0;
  max-height: 140px;
  overflow: auto;
  font-family: inherit;
  font-size: 12px;
  line-height: 1.7;
  color: var(--字次);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
