<template>
  <div class="登录页">
    <div class="登录卡">
      <div class="登录标题">AICG 漫剧平台</div>
      <div class="登录副标题">本地 ComfyUI 漫剧制作平台</div>

      <el-form @submit.native.prevent>
        <el-form-item>
          <el-input
            v-model="表单.用户名"
            placeholder="用户名"
            prefix-icon="el-icon-user"
            @keyup.enter.native="提交()"
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="表单.密码"
            type="password"
            placeholder="密码"
            prefix-icon="el-icon-lock"
            @keyup.enter.native="提交()"
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="记住账号密码" class="记住账号">记住账号密码</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width: 100%" :loading="提交中" @click="提交()">登 录</el-button>
        </el-form-item>
      </el-form>

      <div v-if="错误文字" class="登录错误">{{ 错误文字 }}</div>
    </div>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
