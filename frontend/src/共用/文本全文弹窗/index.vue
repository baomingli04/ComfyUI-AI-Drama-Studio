<template>
  <el-dialog
    :visible="显示"
    width="760px"
    top="8vh"
    custom-class="全文弹窗"
    :show-close="false"
    append-to-body
    @close="$emit('关闭')"
  >
    <div class="全文容器">
      <div class="全文头">
        <span class="全文标题">{{ 标题 || '全文' }}</span>
        <span class="全文字数">{{ 内容 ? 内容.length : 0 }} 字</span>
        <i class="el-icon-close 全文关闭" @click="$emit('关闭')"></i>
      </div>

      <div class="全文主体">{{ 内容 || '（空）' }}</div>

      <div class="全文底">
        <el-button size="small" type="primary" icon="el-icon-document-copy" @click="复制()">复制全文</el-button>
        <span class="全文提示">可框选，也可直接复制</span>
      </div>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
