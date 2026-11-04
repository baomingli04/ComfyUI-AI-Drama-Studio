<template>
  <div class="技能页">
    <div class="页标题">技能管理</div>

    <el-row :gutter="16">
      <el-col :span="6">
        <div class="分类卡">
          <div class="分类头">
            <span>技能分类</span>
            <el-button size="mini" type="primary" icon="el-icon-plus" @click="打开新增分类()">新增</el-button>
          </div>
          <div
            v-for="分类 in 分类列表"
            :key="分类.id"
            class="分类项"
            :class="{ 选中: 分类.id === 当前分类id }"
            @click="选分类(分类)"
          >
            <span>{{ 分类.名称 }}</span>
            <span class="系统标记" v-if="分类.系统内置">内置</span>
            <el-button
              v-else
              class="分类删除钮"
              size="mini"
              type="text"
              icon="el-icon-delete"
              title="删除分类"
              @click.stop="删分类(分类)"
            ></el-button>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="16" :lg="18">
        <div class="技能表格卡">
          <div class="技能表格头">
            <el-button size="small" type="primary" icon="el-icon-upload2" @click="打开上传弹窗()">上传技能包</el-button>
            <el-button size="small" icon="el-icon-refresh" @click="拉技能()">刷新</el-button>
          </div>
          <el-table :data="技能列表" border>
            <el-table-column prop="id" label="ID" width="70"></el-table-column>
            <el-table-column prop="名称" label="名称" show-overflow-tooltip></el-table-column>
            <el-table-column prop="分类名称" label="分类" width="120"></el-table-column>
            <el-table-column prop="目录名" label="目录名" show-overflow-tooltip></el-table-column>
            <el-table-column prop="原压缩包名" label="原压缩包" show-overflow-tooltip></el-table-column>
            <el-table-column prop="创建时间" label="创建时间" width="160"></el-table-column>
            <el-table-column label="操作" width="150">
              <template slot-scope="s">
                <el-button size="mini" type="primary" @click="打开编辑技能(s.row)">编辑</el-button>
                <el-button size="mini" type="danger" @click="删技能(s.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <add-category-dialog :显示="新增弹窗显示" @关闭="新增弹窗显示 = false" @已新增="已新增分类()"></add-category-dialog>
    <edit-skill-dialog
      :显示="编辑弹窗显示"
      :技能="当前技能"
      :分类列表="分类列表"
      @关闭="编辑弹窗显示 = false"
      @已保存="已保存技能()"
    ></edit-skill-dialog>
    <upload-skill-dialog :显示="上传弹窗显示" :分类列表="分类列表" @关闭="上传弹窗显示 = false" @已上传="已上传技能()"></upload-skill-dialog>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
