<template>
  <el-dialog
    :title="标题 || ('运行日志 - 任务 ' + 任务id)"
    :visible="显示"
    width="760px"
    @close="$emit('关闭')"
  >
    <pre class="日志框">{{ 日志 || '（暂无日志）' }}</pre>
    <div slot="footer">
      <el-button @click="$emit('关闭')">关 闭</el-button>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
