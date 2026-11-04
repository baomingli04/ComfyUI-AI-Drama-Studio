<template>
  <div class="测试页">
    <div class="页标题">D6 加速版生视频（导演台 r2v + Sage Attention 加速）</div>

    <div class="表单卡">
      <el-form label-width="110px">
        <el-form-item label="参考图">
          <el-upload :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                     :on-success="图成功" accept="image/*" multiple>
            <el-button size="small" icon="el-icon-upload2">上传参考图</el-button>
          </el-upload>
          <media-thumbs class="表单缩略" :媒体列表="表单媒体列表()" @点击="预览表单媒体()"></media-thumbs>
          <span v-if="!表单.输入图1" class="上传路径">未上传。提示词里用 &lt;Picture 1&gt;、&lt;Picture 2&gt;… 按上传顺序引用</span>
          <el-button v-if="表单.输入图1" size="mini" type="text" @click="清空参考()">清空</el-button>
        </el-form-item>
        <el-form-item label="参考视频">
          <el-upload :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                     :on-success="视频成功" accept="video/*">
            <el-button size="small" icon="el-icon-upload2">上传参考视频</el-button>
          </el-upload>
          <span class="上传路径">可选，最多 3 个。提示词里用 &lt;Video 1&gt; 引用</span>
          <el-button v-if="有参考视频" size="mini" type="text" @click="清空参考视频()">清空</el-button>
        </el-form-item>
        <el-form-item label="参考音频">
          <el-upload :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                     :on-success="音频成功" accept="audio/*">
            <el-button size="small" icon="el-icon-upload2">上传参考音频</el-button>
          </el-upload>
          <span class="上传路径">可选，最多 3 个。音频不进文本编码，只留 &lt;Audio 1&gt; 标签</span>
          <el-button v-if="有参考音频" size="mini" type="text" @click="清空参考音频()">清空</el-button>
        </el-form-item>
        <ai-expand :技能列表="技能列表" :技能id.sync="扩写技能id" :需求.sync="扩写需求" :载入中="扩写中" @生成="扩写($event)"></ai-expand>
        <el-form-item label="正向提示词">
          <el-input type="textarea" :rows="3" v-model="表单.正向提示词" placeholder="用 <Picture 1> 指代参考图，<Video 1> 指代参考视频，描述要生成的画面"></el-input>
        </el-form-item>
        <el-form-item label="反向提示词">
          <el-input type="textarea" :rows="2" v-model="表单.反向提示词" placeholder="不想出现的内容"></el-input>
        </el-form-item>
        <el-form-item label="seed">
          <el-input v-model="表单.seed" placeholder="留空随机" style="width: 100%; max-width: 220px"></el-input>
        </el-form-item>
        <el-form-item label="cfg">
          <el-input-number v-model="表单.cfg" :min="0" :max="20" :step="0.1" controls-position="right"></el-input-number>
        </el-form-item>
        <el-form-item label="帧率">
          <span class="上传路径">24 fps（沿用工作流默认）· 总帧数 {{ 总帧数 }}（MiniMax 规则 17k+5，约 {{ (总帧数 / 24).toFixed(2) }} 秒）</span>
        </el-form-item>
        <el-form-item label="比例">
          <el-select v-model="表单.比例" size="small">
            <el-option v-for="项 in 比例选项" :key="项" :label="项" :value="项"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="一采MP">
          <el-input-number v-model="表单.一采MP" :min="0.1" :max="16" :step="0.1" controls-position="right"></el-input-number>
        </el-form-item>
        <el-form-item label="画布">
          <span class="上传路径">{{ 画布宽高 ? 画布宽高.宽 + ' × ' + 画布宽高.高 + '（比例 + 一采MP 算出，32 倍数，只读）' : '沿用工作流默认' }}</span>
        </el-form-item>
        <el-form-item label="时长(秒)">
          <el-input-number v-model="表单.视频时长" :min="1" :max="60" :step="1" controls-position="right"></el-input-number>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="提交中" @click="提交任务()">提交任务</el-button>
          <el-button icon="el-icon-refresh" @click="拉任务列表()">刷新列表</el-button>
        </el-form-item>
      </el-form>
      <div class="上传路径">加速说明：工作流已串好 PathchSageAttentionKJ + MiniMaxH3MemoryEfficientSageAttentionPatch，无需页上参数。</div>
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
        <el-table-column label="参数" width="170">
          <template slot-scope="s">
            {{ s.row.视频宽 }}×{{ s.row.视频高 }} · {{ s.row.视频时长 }}s · cfg {{ s.row.cfg }}
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

    <run-log-dialog :显示="日志弹窗显示" :日志="当前日志" :任务id="当前日志id" @关闭="日志弹窗显示 = false"></run-log-dialog>
    <media-preview :显示="预览显示" :列表="预览列表" :索引="预览索引" @关闭="预览显示 = false" @切换="预览切换($event)"></media-preview>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
