<template>
  <div class="用户页" v-loading="加载中">
    <div class="页标题">用户</div>

    <el-alert v-if="错误文字" :title="错误文字" type="error" show-icon style="margin-bottom: 12px"></el-alert>

    <div v-if="用户信息" class="用户卡">
      <div class="用户行"><span class="用户字段">ID</span><span>{{ 用户信息.id }}</span></div>
      <div class="用户行"><span class="用户字段">用户名</span><span>{{ 用户信息.用户名 }}</span></div>
      <div class="用户行"><span class="用户字段">昵称</span><span>{{ 用户信息.昵称 }}</span></div>
    </div>

    <el-button icon="el-icon-refresh" @click="拉用户()">刷新</el-button>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
