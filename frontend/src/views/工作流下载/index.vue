<template>
  <div class="工作流页">
    <div class="页标题">工作流下载</div>

    <div class="表格卡">
      <div class="表格头">
        <el-upload
          :action="上传地址"
          :headers="上传头"
          name="文件"
          :show-file-list="false"
          :on-success="上传成功"
          :on-error="上传失败"
          accept=".json,.zip"
        >
          <el-button size="small" type="primary" icon="el-icon-upload2">上传工作流</el-button>
        </el-upload>
        <el-button size="small" icon="el-icon-refresh" @click="拉列表()">刷新</el-button>
      </div>

      <el-table :data="文件列表" border>
        <el-table-column prop="名" label="文件名" show-overflow-tooltip></el-table-column>
        <el-table-column label="大小" width="120">
          <template slot-scope="s">{{ 大小文本(s.row.大小) }}</template>
        </el-table-column>
        <el-table-column prop="修改时间" label="修改时间" width="180"></el-table-column>
        <el-table-column label="操作" width="100">
          <template slot-scope="s">
            <el-button size="mini" icon="el-icon-download" @click="下载(s.row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
