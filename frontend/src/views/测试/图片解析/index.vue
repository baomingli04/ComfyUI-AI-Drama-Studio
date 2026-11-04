<template>
  <div class="测试页">
    <div class="页标题">T2 图片解析</div>

    <div class="表单卡">
      <el-form label-width="110px">
        <el-form-item label="解析图片">
          <el-upload :action="上传地址" :headers="上传头" name="文件" :show-file-list="false" :on-success="图1成功" accept="image/*">
            <el-button size="small" icon="el-icon-upload2">上传图片</el-button>
          </el-upload>
          <media-thumbs class="表单缩略" :大号="true" :媒体列表="表单媒体列表()" :可删除="true" @点击="预览表单媒体()" @删除="删表单媒体($event)"></media-thumbs>
          <span v-if="!表单.输入图1" class="上传路径">未上传</span>
        </el-form-item>
        <el-form-item label="正向提示词">
          <el-input type="textarea" :rows="2" v-model="表单.正向提示词" placeholder="可选，解析要求（描述这张图…）"></el-input>
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input type="textarea" :rows="2" v-model="表单.系统提示词" placeholder="可选，模型角色设定"></el-input>
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
        <el-table-column label="输入" width="130">
          <template slot-scope="s">
            <media-thumbs :媒体列表="输入媒体(s.row)" :显示全="true" @点击="打开预览(s.row, $event)"></media-thumbs>
          </template>
        </el-table-column>
        <el-table-column label="回复" show-overflow-tooltip>
          <template slot-scope="s">{{ 结果文本(s.row) }}</template>
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

    <run-log-dialog :显示="日志弹窗显示" :日志="当前日志" :任务id="当前日志id" @关闭="日志弹窗显示 = false"></run-log-dialog>
    <media-preview :显示="预览显示" :列表="预览列表" :索引="预览索引" @关闭="预览显示 = false" @切换="预览切换($event)"></media-preview>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
