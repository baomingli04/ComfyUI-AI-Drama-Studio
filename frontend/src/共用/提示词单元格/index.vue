<template>
  <div class="提示词单元格">
    <div
      v-if="文本"
      class="提示词文本"
      :class="{ 可点: true }"
      :style="{ '-webkit-line-clamp': 行数 }"
      @click="打开全文()"
    >{{ 文本 }}</div>
    <span v-else class="提示词空">—</span>

    <el-button v-if="文本" size="mini" type="text" class="复制按钮" @click.stop="复制()">复制</el-button>

    <text-dialog :显示="弹窗显示" :标题="标题" :内容="文本" @关闭="弹窗显示 = false"></text-dialog>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
