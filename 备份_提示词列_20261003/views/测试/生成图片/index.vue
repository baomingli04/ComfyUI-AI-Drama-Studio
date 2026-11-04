<template>
  <div class="测试页">
    <div class="页标题">T3 生成图片</div>

    <div class="表单卡">
      <el-form label-width="110px">
        <ai-expand :技能列表="技能列表" :技能id.sync="扩写技能id" :需求.sync="扩写需求" :载入中="扩写中" @生成="扩写($event)"></ai-expand>
        <el-form-item label="正向提示词">
          <div class="提示词工具">
            <el-button size="mini" icon="el-icon-collection-tag" @click="打开提示词资源库()">提示词资源库</el-button>
            <span class="提示词工具说明">从提示词广场挑一条，正/反向提示词一起填入</span>
          </div>
          <el-input type="textarea" :rows="3" v-model="表单.正向提示词" placeholder="画面描述提示词"></el-input>
        </el-form-item>
        <el-form-item label="反向提示词">
          <el-input type="textarea" :rows="2" v-model="表单.反向提示词" placeholder="可选，不希望出现的内容"></el-input>
        </el-form-item>
        <el-form-item label="图片尺寸">
          <el-input-number v-model="表单.图片宽" :min="64" :max="4096" :step="64" controls-position="right"></el-input-number>
          <span class="尺寸分隔">×</span>
          <el-input-number v-model="表单.图片高" :min="64" :max="4096" :step="64" controls-position="right"></el-input-number>
          <div class="比例行">
            <span
              v-for="项 in 比例示例"
              :key="项.比例"
              :class="['比例钮', { 选中: 表单.图片宽 === 项.宽 && 表单.图片高 === 项.高 }]"
              @click="填宽高(项)"
            >{{ 项.比例 }}</span>
          </div>
        </el-form-item>
        <el-form-item label="seed">
          <el-input v-model="表单.seed" placeholder="留空随机" style="width: 100%; max-width: 220px"></el-input>
        </el-form-item>
        <el-form-item label="水印">
          <el-switch v-model="表单.水印"></el-switch>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="提交中" @click="提交任务()">提交任务</el-button>
          <el-button icon="el-icon-refresh" @click="拉任务列表()">刷新列表</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="表格区">
      <el-table :data="任务列表" border>
        <el-table-column prop="id" label="任务ID" width="80"></el-table-column>
        <el-table-column prop="状态" label="状态" width="100">
          <template slot-scope="s"><span :class="['状态标', '状态-' + s.row.状态]">{{ s.row.状态 }}</span></template>
        </el-table-column>
        <el-table-column prop="正向提示词" label="提示词" show-overflow-tooltip></el-table-column>
        <el-table-column label="输入" width="130">
          <template slot-scope="s">
            <media-thumbs :媒体列表="输入媒体(s.row)" @点击="打开预览(s.row, $event)"></media-thumbs>
          </template>
        </el-table-column>
        <el-table-column label="产物" width="130">
          <template slot-scope="s">
            <media-thumbs :媒体列表="产物媒体(s.row)" @点击="打开预览(s.row, 输入媒体(s.row).length + $event)"></media-thumbs>
          </template>
        </el-table-column>
        <el-table-column prop="生成时长" label="耗时(秒)" width="90"></el-table-column>
        <el-table-column prop="创建时间" label="创建时间" width="160"></el-table-column>
        <el-table-column label="操作" width="150">
          <template slot-scope="s">
            <el-button size="mini" @click="查看日志(s.row)">日志</el-button>
            <el-button v-if="是终态(s.row)" size="mini" type="danger" @click="删除任务(s.row)">删除</el-button>
            <el-button v-else size="mini" type="danger" @click="取消任务(s.row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <prompt-library-dialog :显示="资源库显示" @关闭="资源库显示 = false" @采用="采用提示词($event)"></prompt-library-dialog>
    <run-log-dialog :显示="日志弹窗显示" :日志="当前日志" :任务id="当前日志id" @关闭="日志弹窗显示 = false"></run-log-dialog>
    <media-preview :显示="预览显示" :列表="预览列表" :索引="预览索引" @关闭="预览显示 = false" @切换="预览切换($event)"></media-preview>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
