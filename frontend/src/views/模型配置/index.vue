<template>
  <div class="配置页" v-loading="加载中">
    <div class="页标题">模型配置</div>

    <el-alert v-if="错误文字" :title="错误文字" type="error" show-icon style="margin-bottom: 12px"></el-alert>

    <div class="配置卡">
      <el-form label-width="160px">
        <el-form-item label="大模型名称">
          <el-input v-model="表单.大模型名称" placeholder="如：Qwen3-14B"></el-input>
        </el-form-item>
        <el-form-item label="LLM 地址">
          <el-input v-model="表单.LLM地址" placeholder="如：192.168.31.121:8080"></el-input>
        </el-form-item>
        <el-form-item label="LLM 密钥">
          <el-input v-model="表单.LLM密钥" placeholder="无密钥可留空"></el-input>
        </el-form-item>
        <el-form-item label="LLM 模型名">
          <el-input v-model="表单.LLM模型名" placeholder="如：qwen3-14b"></el-input>
        </el-form-item>
        <el-form-item label="ComfyUI 地址">
          <el-input v-model="表单.ComfyUI地址" placeholder="如：192.168.31.121:8188"></el-input>
        </el-form-item>
        <el-form-item label="ComfyUI 工作流目录">
          <el-input v-model="表单.ComfyUI工作流目录" placeholder="如：D:\ComfyUI\workflows"></el-input>
        </el-form-item>
        <el-form-item label="ComfyUI 输出目录">
          <el-input v-model="表单.ComfyUI输出目录" placeholder="如：D:\ComfyUI\output"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="保存中" @click="保存()">保 存</el-button>
          <el-button icon="el-icon-refresh" @click="拉配置()">刷新</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
