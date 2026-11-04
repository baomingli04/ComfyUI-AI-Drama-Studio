<template>
  <!-- 场次编辑 / 新增弹窗（已从 分集剧本.vue 拆分为独立组件，逻辑与视觉保持不变） -->
  <el-dialog
    :visible="显示"
    @update:visible="$emit('update:显示', $event)"
    width="720px"
    top="6vh"
    custom-class="场次编辑弹窗"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">{{ 新增模式 ? '新增一场' : '编辑 ' + 草稿.场 }}</div>
        <div class="弹窗副题">{{ 新增模式 ? '填完点「加入本集」，这一场会排到最后' : '改完点保存，直接写回这一场' }}</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="$emit('update:显示', false)"></i>
    </div>
    <div class="弹窗体">
      <el-form label-width="72px" size="small">
        <el-form-item label="场次号">
          <el-input v-model="草稿.场" maxlength="10" placeholder="例：1-3"></el-input>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="草稿.地点" maxlength="40" placeholder="例：内 · 忍校三班教室 · 日"></el-input>
        </el-form-item>
        <el-form-item label="人物">
          <el-input v-model="草稿.人物" maxlength="80" placeholder="这一场出场的人，顿号分隔"></el-input>
        </el-form-item>
        <el-form-item label="道具">
          <el-input v-model="草稿.道具" maxlength="120" placeholder="这一场要用到的道具，顿号分隔"></el-input>
        </el-form-item>
        <el-form-item label="正文">
          <el-input
            v-model="草稿.正文"
            type="textarea"
            :rows="14"
            placeholder="一行一句。动作行以 △ 开头；台词写成「角色名（动作）：台词」"></el-input>
          <div class="字段注">一行一句，保存时按行拆开；动作行以 △ 开头，台词写「角色名（动作）：台词」</div>
        </el-form-item>
      </el-form>
    </div>
    <div class="弹窗底">
      <el-button v-if="!新增模式" type="text" class="删除钮" @click="删除这一场()">删除这一场</el-button>
      <div style="flex:1"></div>
      <el-button @click="$emit('update:显示', false)">取消</el-button>
      <el-button type="primary" @click="保存这一场()">{{ 新增模式 ? '加入本集' : '保存' }}</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { 拼正文 } from '@/共用/剧本档案'

// 场次编辑 / 新增弹窗（分集剧本页专用）。
// 显隐由父组件 编辑显示 字段控制（:显示.sync）；剧本库写入通过 @写库 交回父组件 $set，
// 落库 / 目录同步复用父组件的 存本集 / 同步目录（方法引用经 props 传入，保持 await 语义不变）。
export default {
  name: 'EpisodeSceneDialog',
  props: {
    显示: { type: Boolean, default: false },
    当前剧: { type: Object, default: null },
    当前集: { type: Number, default: 1 },
    存本集: { type: Function, required: true },
    同步目录: { type: Function, required: true }
  },
  data() {
    return {
      新增模式: false,
      编辑对象: null,
      编辑序: -1,
      草稿: { 场: '', 地点: '', 人物: '', 道具: '', 正文: '' }
    }
  },
  methods: {
    /* ---------------- 场次编辑 / 新增 ---------------- */
    打开编辑场(场, 序) {
      if (!场) return
      this.新增模式 = false
      this.编辑对象 = 场
      this.编辑序 = 序
      this.草稿 = {
        场: 场.场, 地点: 场.地点, 人物: 场.人物,
        道具: 场.道具 || '',
        正文: (场.正文 || []).join('\n')
      }
      this.$emit('update:显示', true)
    },
    新增一场() {
      if (!this.当前剧) {
        this.$message.warning('这一集还没生成剧本，先让 AI 出一版再改')
        return
      }
      const 场们 = this.当前剧.场们 || []
      this.新增模式 = true
      this.编辑对象 = null
      this.编辑序 = -1
      this.草稿 = {
        场: this.当前集 + '-' + (场们.length + 1),
        地点: '内 · ',
        人物: '',
        道具: '',
        正文: ''
      }
      this.$emit('update:显示', true)
    },
    async 保存这一场() {
      const 剧 = this.当前剧
      if (!剧) return
      const 正文行 = String(this.草稿.正文 || '')
        .split(/\r?\n/)
        .map(s => s.trim())
        .filter(s => s)
      const 条 = {
        场: (this.草稿.场 || '').trim(),
        地点: (this.草稿.地点 || '').trim(),
        人物: (this.草稿.人物 || '').trim(),
        道具: (this.草稿.道具 || '').trim(),
        正文: 正文行
      }
      if (!条.场) {
        this.$message.warning('先填场次号')
        return
      }
      const 场们 = (剧.场们 || []).slice()
      if (this.新增模式) {
        场们.push(条)
      } else {
        const 位 = 场们.indexOf(this.编辑对象)
        if (位 < 0) {
          this.$emit('update:显示', false)
          return
        }
        场们[位] = 条
      }
      // 剧本库写入交回父组件（父组件里 $set，同步触发视图更新）
      this.$emit('写库', this.当前集, Object.assign({}, 剧, {
        场们: 场们,
        正文: 拼正文(场们),
        状态: '待复核'
      }))
      this.$emit('update:显示', false)
      if (!(await this.存本集(this.当前集))) return
      await this.同步目录(this.当前集)
      this.$message.success(this.新增模式 ? '已加入第 ' + this.当前集 + ' 集' : '已保存 ' + 条.场)
    },
    删除这一场() {
      const 剧 = this.当前剧
      const 场 = this.编辑对象
      if (!剧 || !场) return
      const 页 = this
      this.$confirm('确定删除 ' + 场.场 + '？', '删除这一场', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async function () {
        const 场们 = (剧.场们 || []).filter(function (项) { return 项 !== 场 })
        页.$emit('写库', 页.当前集, Object.assign({}, 剧, {
          场们: 场们,
          正文: 拼正文(场们),
          状态: '待复核'
        }))
        页.$emit('update:显示', false)
        if (!(await 页.存本集(页.当前集))) return
        await 页.同步目录(页.当前集)
        页.$message.success('已删除 ' + 场.场)
      }).catch(function () {})
    }
  }
}
</script>

<style scoped>
/* ---- 弹窗（场次编辑专用部分） ---- */
.弹窗头 {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding-bottom: 14px; border-bottom: 1px solid var(--描边);
}
.弹窗标题 { font-size: 16px; font-weight: 700; color: var(--字); }
.弹窗副题 { font-size: 12px; color: var(--字弱); margin-top: 4px; }
.弹窗关闭 { cursor: pointer; color: var(--字弱); font-size: 16px; }
.弹窗体 { padding: 16px 0 4px; max-height: 64vh; overflow-y: auto; }
.弹窗底 {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
  padding-top: 14px; border-top: 1px solid var(--描边);
}
.删除钮 { color: #ef4444; }
.字段注 { margin-top: 6px; font-size: 12px; color: var(--字弱); line-height: 1.6; }
</style>
