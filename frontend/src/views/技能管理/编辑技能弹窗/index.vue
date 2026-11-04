<template>
  <el-dialog title="修改技能分类" :visible="显示" width="420px" @close="$emit('关闭')">
    <el-form label-width="80px">
      <el-form-item label="技能">
        <div class="只读值">{{ 技能 ? 技能.名称 : '' }}</div>
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="分类id" placeholder="选择技能所属分类" style="width: 100%">
          <el-option v-for="分类 in 分类列表" :key="分类.id" :label="分类.名称" :value="分类.id"></el-option>
        </el-select>
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
