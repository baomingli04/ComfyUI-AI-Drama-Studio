<template>
  <!-- 单集编辑 / 新增弹窗（从 分集目录.vue 拆出，模板/样式与拆分前完全一致） -->
  <el-dialog
    :visible.sync="弹窗显示"
    width="680px"
    top="6vh"
    custom-class="集编辑弹窗"
    :show-close="false"
    :close-on-click-modal="false">
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">{{ 新增模式 ? '新增一集' : '编辑第 ' + 草稿.集 + ' 集' }}</div>
        <div class="弹窗副题">{{ 新增模式 ? '填完点「加入目录」，这一集会排到最后' : '改完点保存，直接写回这一行' }}</div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="弹窗显示 = false"></i>
    </div>
    <div class="弹窗体">
      <el-form label-width="80px" size="small">
        <div class="表单两列">
          <el-form-item label="集">
            <el-input-number v-model="草稿.集" :min="1" :max="999" controls-position="right"></el-input-number>
          </el-form-item>
          <el-form-item label="幕">
            <el-select v-model="草稿.幕" style="width:170px">
              <el-option label="第一幕 · 建置" value="第一幕 · 建置"></el-option>
              <el-option label="第二幕 · 对抗" value="第二幕 · 对抗"></el-option>
              <el-option label="第三幕 · 收束" value="第三幕 · 收束"></el-option>
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="标题">
          <el-input v-model="草稿.标题" maxlength="30" placeholder="这一集的看点，12 字内最好"></el-input>
        </el-form-item>
        <el-form-item label="梗概">
          <el-input v-model="草稿.梗概" type="textarea" :rows="4" placeholder="1~2 句：这一集发生什么、结尾卡在哪"></el-input>
        </el-form-item>
        <el-form-item label="出场">
          <el-input v-model="草稿.出场" maxlength="80" placeholder="顿号分隔，例如：李宝明、雏田、天天"></el-input>
        </el-form-item>
        <el-form-item label="开场钩子">
          <el-input v-model="草稿.钩子" maxlength="80" placeholder="开场三拍里最先抓住人的那个画面"></el-input>
        </el-form-item>
        <el-form-item label="尾钩">
          <el-input v-model="草稿.尾钩" maxlength="80" placeholder="这一集卡在哪，让观众必须看下一集"></el-input>
        </el-form-item>
        <el-form-item label="中心句">
          <el-input v-model="草稿.中心句" type="textarea" :rows="2" placeholder="一句话说清这一集的内核"></el-input>
        </el-form-item>
        <div class="表单两列">
          <el-form-item label="情绪分">
            <el-rate v-model="草稿.情绪分" :max="5" :colors="['#ef4444', '#f59e0b', '#22c55e']"></el-rate>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="草稿.状态" style="width:140px">
              <el-option label="待创作" value="待创作"></el-option>
              <el-option label="进行中" value="进行中"></el-option>
              <el-option label="已完成" value="已完成"></el-option>
            </el-select>
          </el-form-item>
        </div>
        <div class="表单两列">
          <el-form-item label="字数">
            <el-input-number v-model="草稿.字数" :min="0" :max="20000" :step="100" controls-position="right"></el-input-number>
          </el-form-item>
          <el-form-item label="目标字数">
            <el-input-number v-model="草稿.目标" :min="0" :max="20000" :step="100" controls-position="right"></el-input-number>
          </el-form-item>
        </div>
        <div class="字段注">2 分钟短剧一般 2500~3000 字；偏离目标 20% 以上会在集卡上标红</div>
        <div class="表单两列 开关行">
          <el-form-item label="关键集">
            <el-switch v-model="草稿.关键"></el-switch>
          </el-form-item>
          <el-form-item label="付费卡点">
            <el-switch v-model="草稿.卡点"></el-switch>
          </el-form-item>
        </div>
      </el-form>
    </div>
    <div class="弹窗底">
      <el-button v-if="!新增模式" type="text" class="删除钮" @click="删除这一集()">删除这一集</el-button>
      <div style="flex:1"></div>
      <el-button @click="弹窗显示 = false">取消</el-button>
      <el-button type="primary" @click="保存这一集()">{{ 新增模式 ? '加入目录' : '保存' }}</el-button>
    </div>
  </el-dialog>
</template>

<script>
// 单集编辑 / 新增弹窗（从 分集目录.vue 拆出）。
// 职责划分（与拆分前行为逐字一致）：
//  - 草稿的构建（打开编辑 / 新增一集）留在父组件，草稿对象经 prop 传入、表单直接改同一对象；
//  - 本组件负责 保存这一集 / 删除这一集 / 草稿转集：对 目录表（prop，同一数组引用）做增删改，
//    页面状态类动作通过 $emit 通知父组件（重置筛选 / 翻到集 / 关闭弹窗 / 落库提示）；
//  - 落库（存全库）与其成功/失败提示留在父组件，见父组件的 编辑弹窗新增落库 等方法。
export default {
  name: 'OutlineEpisodeEditDialog',
  props: {
    显示: { type: Boolean, default: false },
    新增模式: { type: Boolean, default: false },
    编辑对象: { type: Object, default: null },
    草稿: { type: Object, required: true },
    目录表: { type: Array, required: true }
  },
  computed: {
    弹窗显示: {
      get() { return this.显示 },
      set(值) { this.$emit('update:显示', 值) }
    }
  },
  methods: {
    草稿转集(草稿) {
      return {
        集: 草稿.集,
        幕: 草稿.幕,
        标题: 草稿.标题,
        关键: !!草稿.关键,
        卡点: !!草稿.卡点,
        梗概: 草稿.梗概,
        出场: String(草稿.出场 || '').split(/[、,，\s]+/).filter(function (人) { return !!人 }),
        钩子: 草稿.钩子,
        尾钩: 草稿.尾钩,
        中心句: 草稿.中心句,
        情绪分: 草稿.情绪分 || 3,
        字数: 草稿.字数,
        目标: 草稿.目标,
        状态: 草稿.状态
      }
    },
    保存这一集() {
      if (this.新增模式) {
        if (!String(this.草稿.标题 || '').trim()) {
          this.$message.warning('先给这一集起个标题')
          return
        }
        const 新集 = this.草稿转集(this.草稿)
        新集.点位 = []
        this.目录表.push(新集)
        this.目录表.sort(function (a, b) { return a.集 - b.集 })
        this.$emit('重置筛选')
        this.$emit('翻到集', 新集.集)
        this.弹窗显示 = false
        this.$emit('已新增', 新集.集)
        return
      }
      const 集 = this.编辑对象
      if (!集) {
        this.弹窗显示 = false
        return
      }
      const 改后 = this.草稿转集(this.草稿)
      // 整条替换而不是逐字段赋值：老数据可能没有 幕/关键/卡点/情绪分 这些新键，
      // 直接赋新键 Vue 2 不认（不是响应式），卡片不会刷新。
      const 序 = this.目录表.indexOf(集)
      const 新集 = Object.assign({}, 集, 改后)
      if (序 >= 0) this.$set(this.目录表, 序, 新集)
      this.目录表.sort(function (a, b) { return a.集 - b.集 })
      this.弹窗显示 = false
      this.$emit('已保存', 新集.集)
    },
    删除这一集() {
      const 集 = this.编辑对象
      if (!集) return
      const 页 = this
      this.$confirm('确定删除第 ' + 集.集 + ' 集「' + 集.标题 + '」？', '删除这一集', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(function () {
        const 序 = 页.目录表.indexOf(集)
        if (序 >= 0) 页.目录表.splice(序, 1)
        页.弹窗显示 = false
        页.$emit('已删除', 集)
      }).catch(function () {})
    }
  }
}
</script>

<style scoped>
/* ---------- 弹窗骨架（与拆分前分集目录页相同） ---------- */
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
.字段注 { font-size: 12px; color: var(--字弱); margin: -4px 0 14px 80px; }

.表单两列 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
.开关行 { margin-top: 4px; }

@media (max-width: 1100px) {
  .表单两列 { grid-template-columns: 1fr; }
}
</style>
