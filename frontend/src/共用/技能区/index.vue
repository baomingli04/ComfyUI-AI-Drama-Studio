<template>
  <!-- 技能区：选技能 → 写需求 → 生成本页内容。
       内部复用「扩写行」组件（它渲染成 el-form-item，所以外面要套 el-form），
       整套文案换成“生成本页内容”，不再出现“提示词/扩写”字样。 -->
  <div class="技能区">
    <div class="区头">
      <div class="区名">技能生成本页内容</div>
      <div class="区说">
        选技能 → 写需求 → 点「生成本页内容」；规则可在「本页生成规则」里按本页改，改完即存。
        <span v-if="作用" class="作用标">当前作用：{{ 作用 }}</span>
      </div>
    </div>

    <el-form label-width="110px">
      <ai-expand
        :技能列表="技能列表"
        :技能id.sync="扩写技能id"
        :需求.sync="扩写需求"
        :载入中="载入中"
        :默认规则="默认规则"
        :文案="页文案"
        :配置类型="页配置类型"
        @生成="$emit('生成', $event)"></ai-expand>

      <el-form-item label="技能指引">
        <div v-if="当前技能" class="指引">
          <span class="指引名">{{ 当前技能.名称 }}</span>
          <span class="指引简介">{{ 当前技能.简介 || '该技能未填写简介，可直接在需求里写清要什么内容。' }}</span>
        </div>
        <span v-else class="空">技能列表为空：请检查后端「技能分类 / minimax」下是否有带 SKILL.md 的技能。</span>
      </el-form-item>

      <el-form-item label="生成内容">
        <el-input
          type="textarea"
          :rows="结果行数"
          :value="结果"
          placeholder="生成的内容会出现在这里，可继续手动修改后保存"
          @input="$emit('update:结果', $event)"></el-input>
      </el-form-item>

      <el-form-item>
        <el-button size="small" icon="el-icon-document-copy" :disabled="!结果" @click="$emit('复制')">复制内容</el-button>
        <el-button size="small" :disabled="!结果" @click="$emit('update:结果', '')">清空</el-button>
        <el-button size="small" type="primary" @click="$emit('保存')">保存本页</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import 扩写行 from '@/共用/扩写行/index.vue'

export default {
  name: '技能区',
  components: { 'ai-expand': 扩写行 },
  props: {
    技能列表: { type: Array, default: () => [] },
    技能id: { type: [Number, String], default: '' },
    需求: { type: String, default: '' },
    载入中: { type: Boolean, default: false },
    结果: { type: String, default: '' },
    // 本页默认生成规则：库里没存本页配置时用它，用户之后仍可在「本页生成规则」里改
    默认规则: { type: String, default: '' },
    // 本页生成话术（由混入统一给），不传则退回“扩写/提示词”那套
    页文案: { type: Object, default: () => ({}) },
    // 本页生成规则在后端存的 key，形如 生成:/script/plan
    页配置类型: { type: String, default: '' },
    // 技能指引要展示的那个技能（页面从混入的 当前技能 传进来）
    当前技能: { type: Object, default: null },
    // 生成内容作用在哪一块（分集大纲页按 tab 传，如「人物设定」）
    作用: { type: String, default: '' },
    结果行数: { type: Number, default: 12 }
  }
}
</script>

<style scoped>
.技能区 {
  margin-top: 16px;
  background: var(--卡片);
  border: 1px solid var(--描边);
  border-radius: 12px;
  padding: 16px;
}
.区头 { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }
.区名 { font-size: 15px; font-weight: 600; color: var(--字); }
.区说 { font-size: 12px; color: var(--字弱); }
.作用标 {
  margin-left: 8px; font-size: 12px; color: var(--主);
  background: var(--主浅); border-radius: 4px; padding: 1px 8px;
}
.指引 { line-height: 1.8; }
.指引名 {
  display: inline-block; font-size: 12px; color: var(--主);
  background: var(--主浅); border-radius: 4px; padding: 1px 8px; margin-right: 8px;
}
.指引简介 { font-size: 12px; color: var(--字次); }
.空 { font-size: 12px; color: var(--字弱); }
</style>
