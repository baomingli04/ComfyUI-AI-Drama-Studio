<template>
  <el-form-item :label="标题">
    <div class="扩写行">
      <el-select v-model="本地技能id" :placeholder="技能提示" class="扩写技能" size="small">
        <el-option v-for="s in 技能列表" :key="s.id" :label="s.名称" :value="s.id"></el-option>
      </el-select>
      <el-input
        v-model="本地需求"
        :placeholder="需求提示"
        size="small"
        class="扩写需求"
        @keyup.enter.native="生成()"
      ></el-input>
      <el-button size="small" type="primary" plain :loading="载入中" @click="生成()">{{ 按钮文字 }}</el-button>
      <el-button size="small" @click="打开配置()">{{ 配置文字 }}</el-button>
    </div>

    <!-- 配置弹窗：与其他页「技能生成弹窗」同风格（深色卡片 + 头/体/底三段式）。
         以前是行内展开式（测试页遗留观感），现在统一为弹窗，所有用扩写行的页面观感一致 -->
    <el-dialog
      :visible="配置展开"
      width="760px"
      top="8vh"
      custom-class="扩写配置弹窗"
      :show-close="false"
      :close-on-click-modal="false"
      @update:visible="配置展开 = $event"
    >
      <div class="弹窗头">
        <div>
          <div class="弹窗标题">{{ 配置文字 }}</div>
          <div class="弹窗副题">{{ 本地配置类型 }} —— {{ 配置说明 }}</div>
        </div>
        <i class="el-icon-close 弹窗关闭" title="关闭" @click="配置展开 = false"></i>
      </div>
      <div class="弹窗体">
        <el-input v-model="配置文本" type="textarea" :rows="14" placeholder="每行一条规则"></el-input>
        <div class="段注">{{ 配置文本.length }} 字 · 这些规则会原样附加到本次扩写的系统提示词里（优先级最高）</div>

        <!-- 引入数据（只读）：与页面提交扩写时发给 AI 的清单完全同源，随上传实时变化。
             AI 扩写时后端会把这份清单（含每张图是什么）写进系统提示词——
             这里和其他页「技能生成弹窗」的做法一致，收进弹窗展示，不在页面行内占位 -->
        <div v-if="引入数据们.length" class="引入块">
          <div class="引入块题"><i class="el-icon-document-copy"></i> 引入数据（点「{{ 按钮文字 }}」时自动带上，随上传实时变化）<span class="引入块数">{{ 引入数据们.length }} 项</span></div>
          <div v-for="(行, 序) in 引入数据们" :key="序" class="引入块单">{{ 行 }}</div>
        </div>
      </div>
      <div class="弹窗底">
        <span class="底注">保存后按页面存库，本页下次打开自动带出。</span>
        <el-button size="small" @click="配置展开 = false">取 消</el-button>
        <el-button size="small" type="primary" :loading="保存中" @click="保存配置()">保 存</el-button>
      </div>
    </el-dialog>
  </el-form-item>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
