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
      <el-button size="small" @click="打开配置()">
        {{ 配置展开 ? '收起配置' : 配置文字 }}
      </el-button>
    </div>

    <div v-if="配置展开" class="配置区">
      <div class="配置提示">
        {{ 配置键 || 本地配置类型 }} —— {{ 配置说明 }}
      </div>
      <el-input v-model="配置文本" type="textarea" :rows="12" placeholder="每行一条规则"></el-input>
      <div class="配置按钮行">
        <button type="button" class="配置按钮" @click="配置展开 = false">取 消</button>
        <button type="button" class="配置按钮 主" :disabled="保存中" @click="保存配置()">
          {{ 保存中 ? '保存中…' : '保 存' }}
        </button>
      </div>
    </div>
  </el-form-item>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
