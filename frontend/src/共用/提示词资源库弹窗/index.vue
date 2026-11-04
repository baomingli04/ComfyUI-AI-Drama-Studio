<template>
  <el-dialog
    title="提示词资源库"
    :visible="显示"
    width="1000px"
    top="6vh"
    custom-class="资源库弹窗"
    :close-on-click-modal="false"
    append-to-body
    @close="$emit('关闭')"
  >
    <div class="资源库" v-loading="载入中" element-loading-text="加载中…" element-loading-background="rgba(13, 20, 36, 0.85)">
      <div class="资源库网格">
        <div
          v-for="项 in 列表"
          :key="项.id"
          class="资源库卡"
          :class="{ 选中: 当前 && 当前.id === 项.id }"
          @click="选条目(项)"
        >
          <img class="资源库图" :src="项.封面" :alt="项.标题" />
          <div class="资源库卡信息">
            <span class="资源库作者">{{ 项.作者 }}</span>
            <span class="资源库复制数">使用 {{ 项.复制数 }}</span>
          </div>
        </div>
      </div>

      <div v-if="当前" class="资源库详情">
        <div class="资源库详情头">
          <span class="资源库详情标题">提示词</span>
          <el-button size="small" type="primary" :loading="详情载入中" @click="采用()">添加</el-button>
        </div>
        <img class="资源库预览" :src="当前.封面" alt="" />
        <div class="资源库字段"><b>正向提示词：</b><span class="资源库文本">{{ 当前.正向提示词 || '（空）' }}</span></div>
        <div class="资源库字段"><b>反向提示词：</b><span class="资源库文本">{{ 当前.反向提示词 || '（空）' }}</span></div>
      </div>
      <div v-else class="资源库详情 资源库详情空">点击左侧图片查看提示词</div>
    </div>

    <div slot="footer" class="资源库底">
      <el-pagination
        layout="total, prev, pager, next, jumper"
        :current-page="页"
        :page-size="每页"
        :total="总数"
        :disabled="载入中"
        @current-change="翻页($event)"
      ></el-pagination>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
