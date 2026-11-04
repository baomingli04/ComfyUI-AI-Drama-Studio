<template>
  <!-- 编辑出图提示词弹窗（从 美术资产.vue 拆出）。
       编辑组对象由父组件 编辑提示词() 传入，保存逻辑（存提示词）保留在父组件，
       本组件点「保存」发 保存 事件，取消/关闭经 update:visible 通知父组件。 -->
  <el-dialog :visible="visible" :title="编辑组 ? '编辑出图提示词 · ' + 编辑组.名称 : ''"
             width="640px" append-to-body
             @update:visible="$emit('update:visible', $event)">
    <template v-if="编辑组">
      <div class="表单块"><div class="表单标">生图提示词</div>
        <el-input type="textarea" :rows="4" v-model="编辑组.生图提示词" placeholder="出图正向提示词" /></div>
      <div class="表单块"><div class="表单标">必须保持（每行一条）</div>
        <el-input type="textarea" :rows="4" v-model="编辑组.必须保持" placeholder="如：眯眼&#10;右眉骨被碎发遮住" /></div>
      <div class="表单块"><div class="表单标">禁止出现（每行一条）</div>
        <el-input type="textarea" :rows="3" v-model="编辑组.禁止出现" placeholder="如：长发" /></div>
    </template>
    <div slot="footer">
      <el-button size="small" @click="$emit('update:visible', false)">取消</el-button>
      <el-button size="small" type="primary" :loading="存中" @click="$emit('保存')">保存</el-button>
    </div>
  </el-dialog>
</template>

<script>
/* 编辑出图提示词弹窗（从 美术资产.vue 拆出）：纯表单模板，业务方法保留在父组件 */
export default {
  name: 'ArtSetPromptDialog',
  props: {
    visible: { type: Boolean, default: false },
    编辑组: { type: Object, default: null },
    存中: { type: Boolean, default: false }
  }
}
</script>

<style scoped>
/* 表单块/表单标 在本组件 scoped 内单独声明（与父组件同名同款，父组件 AI 编辑/音色弹窗仍在用故两边都有） */
.表单块 { margin-bottom: 14px; }
.表单标 { font-size: 12px; color: var(--字次); margin-bottom: 6px; }
</style>
