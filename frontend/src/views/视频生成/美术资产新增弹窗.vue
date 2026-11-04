<template>
  <!-- 新增美术资产弹窗（全剧共用，不挂集；从 美术资产.vue 拆出）。
       缓冲对象（新增缓冲）由父组件 打开新增() 创建后传入，保存逻辑（保存新增）保留在父组件，
       本组件点「新增」时发 保存 事件，取消/关闭经 update:visible 通知父组件。 -->
  <el-dialog :visible="visible" title="新增美术资产" width="520px" append-to-body
             @update:visible="$emit('update:visible', $event)">
    <div v-if="缓冲">
      <div class="表单块"><div class="表单标"><span style="color:#f56c6c">*</span> 类型（选错会带错功能：只有「人物」才有音色和关联角色）</div>
        <el-select v-model="缓冲.类型" size="small" style="width:100%">
          <el-option v-for="区 in 分区表" :key="区.键" :label="区.名" :value="区.键" />
        </el-select></div>
      <div class="表单块"><div class="表单标">名称（必填）</div>
        <el-input v-model="缓冲.名称" size="small" placeholder="如 李宝明 / 忍者教室 / 苦无" /></div>
      <div class="表单块"><div class="表单标">别名（用 、 分隔）</div>
        <el-input v-model="缓冲.别名" size="small" /></div>
      <div class="表单块"><div class="表单标">级别</div>
        <el-input v-model="缓冲.级别" size="small" placeholder="主角 / 次主场景 / 关键道具等" /></div>
      <div class="表单块"><div class="表单标">摘要（可拍细节，生成定装提示词的依据）</div>
        <el-input v-model="缓冲.摘要" type="textarea" :rows="3" /></div>
      <div class="表单块 新增注">新增资产为全剧共用资源（不挂集），资产 id 自动按类型顺延编号。</div>
    </div>
    <div slot="footer">
      <el-button size="small" @click="$emit('update:visible', false)">取消</el-button>
      <el-button size="small" type="primary" :loading="新增中" @click="$emit('保存')">新增</el-button>
    </div>
  </el-dialog>
</template>

<script>
/* 新增美术资产弹窗（从 美术资产.vue 拆出）：纯表单模板，业务方法保留在父组件 */
export default {
  name: 'ArtCreateDialog',
  props: {
    visible: { type: Boolean, default: false },
    缓冲: { type: Object, default: null },     // 即父组件的 新增缓冲
    分区表: { type: Array, default: function () { return [] } },
    新增中: { type: Boolean, default: false }
  }
}
</script>

<style scoped>
/* 表单块/表单标/新增注 在本组件 scoped 内单独声明（与父组件同名同款，父组件 AI 编辑弹窗仍在用故两边都有） */
.表单块 { margin-bottom: 14px; }
.表单标 { font-size: 12px; color: var(--字次); margin-bottom: 6px; }
.新增注 { font-size: 11px; color: var(--字弱); }
</style>
