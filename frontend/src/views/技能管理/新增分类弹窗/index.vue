<template>
  <el-dialog title="新增技能分类" :visible="显示" width="420px" @close="$emit('关闭')">
    <el-form label-width="80px">
      <el-form-item label="分类名称">
        <el-input v-model="名称" placeholder="如：漫画分镜"></el-input>
      </el-form-item>
    </el-form>
    <div slot="footer">
      <el-button @click="$emit('关闭')">取 消</el-button>
      <el-button type="primary" :loading="提交中" @click="提交()">确 定</el-button>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
