<template>
  <!-- 技能生成弹窗：一页一份「技能 + 技能引导提示词」，保存后页面的「AI 丰富XX」就用这套去生成。
       三段式：① 技能 ② 技能引导提示词 ③ 底部保存。 -->
  <el-dialog
    :visible="显示"
    width="760px"
    top="8vh"
    custom-class="技能生成弹窗"
    :show-close="false"
    :close-on-click-modal="false"
    @update:visible="可见变化($event)"
  >
    <div class="弹窗头">
      <div>
        <div class="弹窗标题">技能生成 · {{ 目标名 }}</div>
        <div class="弹窗副题">
          先定好「用哪个技能」和「技能引导提示词」，之后点页面上的「AI 丰富{{ 目标名 }}」就按这套生成。
        </div>
      </div>
      <i class="el-icon-close 弹窗关闭" title="关闭" @click="关闭()"></i>
    </div>

    <div class="弹窗体">
      <!-- ① 技能 -->
      <div class="段">
        <div class="段头">
          <span class="序号">1</span>
          <span class="段名">技能</span>
          <span class="段说">决定用哪一套生成规范</span>
        </div>
        <el-select
          v-model="本地技能id"
          class="技能选择"
          size="small"
          placeholder="选择技能"
          :loading="载入中"
          @change="技能变化()"
        >
          <el-option v-for="s in 技能列表" :key="s.id" :label="s.名称" :value="s.id">
            <span>{{ s.名称 }}</span>
            <span v-if="s.分类名称" class="选项分类">{{ s.分类名称 }}</span>
          </el-option>
        </el-select>
        <div v-if="当前技能" class="当前技能行">
          <span class="当前标">当前技能</span>
          <b>{{ 当前技能.名称 }}</b>
          <el-tag v-if="当前技能.分类名称" size="mini" type="info">{{ 当前技能.分类名称 }}</el-tag>
        </div>
        <div v-if="当前技能" class="技能简介">
          {{ 当前技能.简介 || '该技能没有填写简介，可直接在下面的引导提示词里写清要什么。' }}
        </div>
        <div v-else class="空提示">
          技能列表为空：请检查后端「技能分类 / minimax」下是否有带 SKILL.md 的技能。
        </div>
      </div>

      <!-- ② 技能引导提示词 -->
      <div class="段">
        <div class="段头">
          <span class="序号">2</span>
          <span class="段名">技能引导提示词</span>
          <span class="段说">优先级最高，与技能规范冲突时以这里为准</span>
          <div class="段右">
            <el-button type="text" size="mini" @click="恢复默认()">恢复本页默认</el-button>
          </div>
        </div>
        <el-input
          v-model="本地引导"
          type="textarea"
          :rows="12"
          placeholder="每行一条规则，例：1. 只写一句话创意，不超过 500 字"
        ></el-input>
        <div class="段注">{{ 本地引导.length }} 字 · 保存后会随技能一起发给 AI</div>
      </div>

      <!-- ③ 引入数据：前面步骤产出的上下文，勾选才随需求一起发给 AI -->
      <div v-if="引入数据.length" class="段">
        <div class="段头">
          <span class="序号">3</span>
          <span class="段名">引入数据</span>
          <span class="段说">勾选的会随需求一起发给 AI，不勾选就不发</span>
          <div class="段右">
            <el-button type="text" size="mini" @click="全选引入(true)">全选</el-button>
            <el-button type="text" size="mini" @click="全选引入(false)">全不选</el-button>
          </div>
        </div>

        <div v-for="项 in 本地引入" :key="项.键" class="引入项">
          <div class="引入头">
            <el-checkbox v-model="项.勾选">{{ 项.名 }}</el-checkbox>
            <span v-if="项.提示" class="引入注">{{ 项.提示 }}</span>
          </div>
          <el-input
            v-if="项.可编辑"
            v-model="项.值"
            type="textarea"
            :rows="3"
            :placeholder="项.占位 || '可在这里补上'"></el-input>
          <div v-else class="引入值">{{ 项.值 || '（空）' }}</div>
        </div>
      </div>
    </div>

    <!-- ③ 保存 -->
    <div class="弹窗底">
      <span class="底注">保存后生效，本页下次打开会自动带出。</span>
      <el-button size="small" @click="关闭()">取消</el-button>
      <el-button size="small" type="primary" :loading="保存中" @click="保存()">保存</el-button>
    </div>
  </el-dialog>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
