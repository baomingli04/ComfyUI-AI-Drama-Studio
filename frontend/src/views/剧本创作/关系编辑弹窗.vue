<!-- 关系编辑弹窗（从 人物设定.vue 拆出的独立组件）：一条边 = 甲 ↔ 乙 + 类型 + 关键词 + 一句话说明。
     共享数据（关系表 / 角色名们 / 总集）由父组件用 props 传入；
     保存 / 删除 成功后 $emit('已保存') 让父组件落库；显隐用 显示 的 .sync 模式。 -->
<template>
  <el-dialog
    :visible.sync="弹窗显示"
    width="580px"
    top="10vh"
    custom-class="关系编辑弹窗"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">{{ 关系新增模式 ? '新增关系' : '编辑关系 · ' + 关系草稿.甲 + ' ↔ ' + 关系草稿.乙 }}</div>
        <div class="弹窗副题">两个人之间的这一条边：类型 + 关键词 + 说明。关系在第几集变了，就点「按集拆分」拆成几段</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="弹窗显示 = false"></i>
    </div>
    <div class="弹窗体">
      <el-form label-width="72px" size="small">
        <el-form-item label="甲">
          <el-select v-model="关系草稿.甲" style="width:200px">
            <el-option v-for="人 in 角色名们" :key="'甲' + 人" :label="人" :value="人"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="乙">
          <el-select v-model="关系草稿.乙" style="width:200px">
            <el-option v-for="人 in 角色名们" :key="'乙' + 人" :label="人" :value="人"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item v-if="!关系草稿.阶段.length" label="类型">
          <el-select v-model="关系草稿.类型" style="width:200px">
            <el-option v-for="型 in 关系类型们" :key="型" :label="型" :value="型"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="关系草稿.关键词" placeholder="顿号分隔，例：挡与补位、出手权交接"></el-input>
        </el-form-item>
        <el-form-item v-if="!关系草稿.阶段.length" label="说明">
          <el-input
            v-model="关系草稿.说明"
            type="textarea"
            :rows="3"
            placeholder="一句话写清这两人的关系从什么变成什么"></el-input>
        </el-form-item>
        <!-- 分阶段：这段关系在第几集变了，就拆成几段，各自一个类型 + 说明 -->
        <el-form-item label="分阶段">
          <div v-if="关系草稿.阶段.length" class="段编辑列">
            <div v-for="(段, 序) in 关系草稿.阶段" :key="'关段' + 序" class="段编辑行">
              <span class="段编辑字">第</span>
              <el-input-number
                v-model="段.起" :min="1" :max="总集" :controls="false"
                size="mini" style="width:54px"></el-input-number>
              <span class="段编辑字">–</span>
              <el-input-number
                v-model="段.止" :min="1" :max="总集" :controls="false"
                size="mini" style="width:54px"></el-input-number>
              <span class="段编辑字">集</span>
              <el-select v-model="段.类型" size="mini" style="width:88px">
                <el-option v-for="型 in 关系类型们" :key="'关型' + 型" :label="型" :value="型"></el-option>
              </el-select>
              <el-input
                v-model="段.说明"
                type="textarea"
                :autosize="{ minRows: 1, maxRows: 3 }"
                class="段编辑值"
                placeholder="这一段关系是什么样"></el-input>
              <i class="el-icon-close 段编辑删" title="删掉这一段" @click="删关系段(序)"></i>
            </div>
            <div class="段编辑底">
              <el-button type="text" size="mini" icon="el-icon-plus" @click="加关系段()">加一段</el-button>
              <el-button type="text" size="mini" @click="合并关系()">合并成单值</el-button>
            </div>
          </div>
          <template v-else>
            <el-button type="text" size="mini" @click="拆分关系()">按集拆分（这段关系会变就拆）</el-button>
            <span class="段编辑注">不拆就是全剧一个类型，拆了才能写「第1-5集普通，第6集起情侣」</span>
          </template>
        </el-form-item>
      </el-form>
    </div>
    <div class="弹窗底">
      <el-button v-if="!关系新增模式" type="text" class="删除钮" @click="删除关系()">删除这条关系</el-button>
      <div style="flex:1"></div>
      <el-button @click="弹窗显示 = false">取消</el-button>
      <el-button type="primary" @click="保存关系()">保存</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { 关系类型们, 规整段, 是分段, 是同一条边 } from '@/共用/人物工具'

export default {
  name: 'GuanxiEditDialog',
  props: {
    /* 显隐：父组件用 :显示.sync 控制 */
    显示: { type: Boolean, default: false },
    总集: { type: Number, default: 0 },
    /* 共享数据：只取本剧角色（CHAR_）的名，关系网两端都从这里选 */
    角色名们: { type: Array, default: function () { return [] } },
    /* 父组件的关系网（数组引用，弹窗内直接读写同一份） */
    关系表: { type: Array, default: function () { return [] } }
  },
  data() {
    return {
      关系新增模式: false,
      关系编辑对象: null,
      关系草稿: { 甲: '', 乙: '', 类型: '羁绊', 关键词: '', 说明: '', 阶段: [] },
      /* 字段口径（模板里要用） */
      关系类型们: 关系类型们
    }
  },
  computed: {
    /* el-dialog 的 :visible.sync 落到父组件的 显示 上 */
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    }
  },
  methods: {
    打开新增关系() {
      const 名们 = this.角色名们
      this.关系新增模式 = true
      this.关系编辑对象 = null
      this.关系草稿 = {
        甲: 名们[0] || '', 乙: 名们[1] || '', 类型: '羁绊', 关键词: '', 说明: '', 阶段: []
      }
      this.$emit('update:显示', true)
    },
    打开编辑关系(边) {
      if (!边) return
      this.关系新增模式 = false
      this.关系编辑对象 = 边
      this.关系草稿 = {
        甲: 边.甲, 乙: 边.乙, 类型: 边.类型 || '羁绊',
        关键词: (边.关键词 || []).join('、'), 说明: 边.说明 || '',
        阶段: 是分段(边.阶段) ? 规整段(边.阶段, this.总集) : []
      }
      this.$emit('update:显示', true)
    },
    /* ---- 关系弹窗里的「按集分段」 ---- */
    // 单值 → 分段：用当前的类型 + 说明包成一段，再自己拆
    拆分关系() {
      this.关系草稿.阶段 = [{
        起: 1,
        止: this.总集,
        类型: this.关系草稿.类型 || '羁绊',
        说明: this.关系草稿.说明 || '',
        值: ''
      }]
    },
    // 分段 → 单值：类型和说明取最新一段
    合并关系() {
      const 段们 = 规整段(this.关系草稿.阶段, this.总集)
      const 末 = 段们[段们.length - 1]
      if (末) {
        this.关系草稿.类型 = 末.类型 || this.关系草稿.类型
        this.关系草稿.说明 = 末.说明 || this.关系草稿.说明
      }
      this.关系草稿.阶段 = []
    },
    加关系段() {
      const 段们 = 规整段(this.关系草稿.阶段, this.总集)
      const 末 = 段们[段们.length - 1]
      const 起 = 末 ? Math.min(末.止 + 1, this.总集) : 1
      this.关系草稿.阶段 = 段们.concat([{
        起: 起, 止: this.总集,
        类型: 末 ? (末.类型 || '羁绊') : '羁绊',
        说明: '', 值: ''
      }])
    },
    删关系段(序) {
      const 段们 = 规整段(this.关系草稿.阶段, this.总集)
      if (段们.length <= 1) {
        this.$message.warning('至少留一段；想变回一个类型就点「合并成单值」')
        return
      }
      段们.splice(序, 1)
      this.关系草稿.阶段 = 段们
    },
    保存关系() {
      const 甲 = String(this.关系草稿.甲 || '').trim()
      const 乙 = String(this.关系草稿.乙 || '').trim()
      if (!甲 || !乙) {
        this.$message.warning('两端都要选一个角色')
        return
      }
      if (甲 === 乙) {
        this.$message.warning('同一个人不能和自己连一条边')
        return
      }
      const 词 = String(this.关系草稿.关键词 || '')
        .split(/[、,，/]/)
        .map(function (s) { return s.trim() })
        .filter(function (s) { return s })
      const 说明 = String(this.关系草稿.说明 || '').trim()
      // 有阶段就以阶段为准，顶层的类型/说明跟着最后一段走（筛选、喂 AI 时不用再判断）
      const 阶段 = 规整段(this.关系草稿.阶段, this.总集)
      const 末段 = 阶段[阶段.length - 1]
      const 定型 = 末段 ? (末段.类型 || this.关系草稿.类型 || '羁绊') : (this.关系草稿.类型 || '羁绊')
      const 定说 = 末段 ? (末段.说明 || 说明) : 说明

      if (this.关系新增模式) {
        const 撞 = this.关系表.some(function (边) { return 是同一条边(边, 甲, 乙) })
        if (撞) {
          this.$message.warning('「' + 甲 + '」和「' + 乙 + '」之间已经有一条边了，直接编辑那一条')
          return
        }
        let 最大 = 0
        this.关系表.forEach(function (边) { if (边.id > 最大) 最大 = 边.id })
        this.关系表.push({
          id: 最大 + 1, 甲: 甲, 乙: 乙,
          类型: 定型, 关键词: 词, 说明: 定说, 阶段: 阶段
        })
      } else {
        const 边 = this.关系编辑对象
        if (!边) {
          this.$emit('update:显示', false)
          return
        }
        边.甲 = 甲
        边.乙 = 乙
        边.类型 = 定型
        边.关键词 = 词
        边.说明 = 定说
        边.阶段 = 阶段
      }
      this.$emit('update:显示', false)
      this.$emit('已保存')
      this.$message.success('已保存「' + 甲 + ' ↔ ' + 乙 + '」' + (阶段.length > 1 ? '，按集拆成 ' + 阶段.length + ' 段' : ''))
    },
    删除关系() {
      const 边 = this.关系编辑对象
      if (!边) return
      const 页 = this
      this.$confirm('确定删除「' + 边.甲 + ' ↔ ' + 边.乙 + '」这条关系？', '删除关系', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(function () {
        const 序 = 页.关系表.indexOf(边)
        if (序 >= 0) 页.关系表.splice(序, 1)
        页.$emit('update:显示', false)
        页.$emit('已保存')
        页.$message.success('已删除')
      }).catch(function () {})
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

/* 分段编辑器：第 [起] – [止] 集 [值] ×（与角色编辑弹窗同一套形态） */
.段编辑列 { width: 100%; }
.段编辑行 { display: flex; align-items: flex-start; gap: 6px; margin-bottom: 6px; }
.段编辑字 { font-size: 12px; color: var(--字弱); line-height: 28px; white-space: nowrap; }
.段编辑值 { flex: 1; min-width: 0; }
.段编辑删 { cursor: pointer; color: var(--字弱); line-height: 28px; }
.段编辑删:hover { color: #ef4444; }
.段编辑底 { display: flex; align-items: center; gap: 10px; }
.段编辑注 { font-size: 11px; color: var(--字弱); margin-left: 8px; }
</style>
