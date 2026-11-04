<template>
  <div class="剧集详情 创作模块">
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="回列表()">视频生成</span>
      <span> / </span>
      <span>{{ 剧名 }}</span>
    </div>

    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">{{ 剧名 }}</h1>
        <div class="副题">{{ 副题 }}</div>
      </div>
      <div class="右">
        <el-button size="small" icon="el-icon-arrow-left" @click="回列表()">返回列表</el-button>
      </div>
    </div>

    <!-- 分集列表：进入本项目后才显示（每集=一个关卡卡），分页展示 -->
    <div v-if="载入中" class="卡片" style="text-align:center;padding:48px 0;color:var(--字弱)">
      <i class="el-icon-loading" style="font-size:36px"></i>
      <div style="margin-top:8px">正在读取剧集数据…</div>
    </div>
    <div v-else-if="载入报错" class="卡片" style="text-align:center;padding:48px 0">
      <div style="color:var(--警,#e6a23c)">{{ 载入报错 }}</div>
      <el-button size="small" style="margin-top:10px" @click="载入()">重试</el-button>
    </div>
    <div v-else class="卡片">
      <div class="区头">
        <span class="区名">分集</span>
        <span class="计数">共 {{ 集列表.length }} 集</span>
      </div>

      <div class="集列表">
        <div
          v-for="关 in 分页集列表"
          :key="关.集"
          class="关卡"
          :class="{ 当前: 关.集 === 1, 完成: 关.进度 >= 100 }"
          @click="进关卡(关)"
        >
          <div class="关卡行">
            <div class="集号" :class="{ 亮: 关.集 === 1, 绿: 关.进度 >= 100 }">
              {{ 关.进度 >= 100 ? '✓' : 关.集 }}
            </div>
            <div class="集信息">
              <div class="集标题">第 {{ 关.集 }} 集 · {{ 关.标题 }}</div>
              <div class="集副">{{ 关.状态 }} · {{ 关.分镜 }} 分镜 · {{ 关.字数 }} 字</div>
            </div>
            <div class="集进度">
              <div class="进度轨">
                <div class="进度条" :style="{ width: 关.进度 + '%' }"></div>
              </div>
              <span class="进度字">{{ 关.进度 }}%</span>
            </div>
            <el-button size="small" :type="关.集 === 1 ? 'primary' : 'default'" @click.stop="进关卡(关)">
              进入
              <i class="el-icon-arrow-right"></i>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="集列表.length > 每页" class="分页行">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="集列表.length"
          :page-size="每页"
          :current-page.sync="当前页"
          :pager-count="7"
        />
      </div>
    </div>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
