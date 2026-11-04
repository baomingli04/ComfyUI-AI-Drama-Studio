<template>
  <el-container class="壳">
    <div v-if="平板 && !侧栏收起" class="壳-遮罩" @click="侧栏收起 = true"></div>
    <el-aside :width="侧栏布局宽" :class="['壳-侧栏', { '壳-侧栏-覆盖': 平板 && !侧栏收起, '壳-侧栏-窄': !平板 && 侧栏收起 }]">
      <div class="壳-标题">
        <span class="壳-标题字">AICG 漫剧平台</span>
      </div>
      <el-menu :default-active="当前路径" :collapse="!平板 && 侧栏收起" class="壳-菜单" @select="跳转($event)">
        <template v-for="组 in 菜单">
          <!-- 扁平项：直接一级菜单项，不套子组（docs/12 第 2 节） -->
          <div v-if="组.分隔" :key="组.分组 + '-sep'" class="壳-菜单分隔"></div>
          <el-menu-item v-if="组.扁平" :key="组.分组" :index="组.路径">
            <i :class="组.图标"></i>
            <span slot="title">{{ 组.标题 }}</span>
          </el-menu-item>
          <el-submenu v-else :key="组.分组" :index="组.分组">
            <template slot="title">
              <i class="el-icon-menu"></i>
              <span>{{ 组.标题 }}</span>
            </template>
            <el-menu-item v-for="项 in 组.子项" :key="项.路径" :index="项.路径">
              <i :class="项.图标"></i>
              <span slot="title">{{ 项.标题 }}</span>
            </el-menu-item>
          </el-submenu>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header height="56px" class="壳-顶栏">
        <div class="壳-顶栏左">
          <button type="button" class="壳-折叠钮" @click="切换侧栏()">
            <i :class="侧栏收起 ? 'el-icon-s-unfold' : 'el-icon-s-fold'"></i>
          </button>
          <span class="壳-路径">{{ 当前路径 }}</span>
        </div>
        <div class="壳-顶栏右">
          <span class="壳-用户">{{ 当前昵称 || 当前用户名 }}</span>
          <el-button size="small" @click="退出登录()">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="壳-内容">
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
