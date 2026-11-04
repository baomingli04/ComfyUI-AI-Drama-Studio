<template>
  <div class="测试页">
    <div class="页标题">T11 音频剪辑</div>

    <!-- 区1：视频提取音频 -->
    <div class="卡片">
      <div class="卡片标题">① 视频提取音频</div>
      <el-form label-width="100px">
        <el-form-item label="视频文件">
          <el-upload :action="上传地址" :headers="上传头" name="文件" :show-file-list="false" :on-success="视频成功" accept="video/*">
            <el-button size="small" icon="el-icon-upload2">上传视频</el-button>
          </el-upload>
          <span class="灰字">{{ 视频原名 || 视频路径 || '未上传' }}</span>
        </el-form-item>
        <el-form-item label="输出格式">
          <el-radio-group v-model="输出格式">
            <el-radio label="wav">WAV</el-radio>
            <el-radio label="mp3">MP3</el-radio>
          </el-radio-group>
          <span class="行内标签">采样率</span>
          <el-select v-model="输出采样率" size="small" class="窄选">
            <el-option :value="0" label="保持原样"></el-option>
            <el-option :value="44100" label="44100"></el-option>
            <el-option :value="48000" label="48000"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="提取中" @click="提取音频()">提取音频</el-button>
          <span class="灰字">提取结果会自动载入下面的剪辑区</span>
        </el-form-item>
      </el-form>
    </div>

    <!-- 区2：音频剪辑 -->
    <div class="卡片">
      <div class="卡片标题">② 音频剪辑（在波形上拖拽选段 → 合并 / 分别导出）</div>

      <div class="来源行">
        <el-upload :action="上传地址" :headers="上传头" name="文件" :show-file-list="false" :on-success="音频成功" accept="audio/*">
          <el-button size="small" icon="el-icon-upload2">上传音频</el-button>
        </el-upload>
        <span class="灰字">{{ 音频路径 || '未载入音频' }}</span>
        <span v-if="音频路径" class="灰字">时长 {{ 格式化秒(音频时长) }} · {{ 音频采样率 }}Hz · {{ 声道文字 }}</span>
      </div>

      <div class="波形区">
        <canvas ref="波形" class="波形" width="1200" height="170"
          @mousedown="波形按下($event)" @mousemove="波形移动($event)" @mouseup="波形抬起()" @mouseleave="波形抬起()"></canvas>
        <div class="波形提示">按住鼠标左键在波形上拖拽 = 选中一段，松开即加入片段列表</div>
      </div>

      <div class="播放行">
        <el-button size="small" icon="el-icon-video-play" @click="切换播放()">{{ 播放中 ? '暂停' : '播放' }}</el-button>
        <el-button size="small" icon="el-icon-refresh-left" @click="回到开头()">回到开头</el-button>
        <el-button size="small" :disabled="!片段列表.length" @click="连播片段()">连播片段</el-button>
        <el-button size="small" :disabled="!片段列表.length" @click="清空片段()">清空片段</el-button>
        <span class="灰字">{{ 格式化秒(播放位置) }} / {{ 格式化秒(音频时长) }}</span>
        <audio ref="音频" :src="当前音频地址" @timeupdate="时间更新()" @ended="播放中 = false" class="隐藏音频"></audio>
      </div>

      <el-table :data="片段列表" border size="mini" empty-text="还没有片段：在波形上拖拽选中即可">
        <el-table-column label="序号" width="60">
          <template slot-scope="s">{{ s.$index + 1 }}</template>
        </el-table-column>
        <el-table-column label="开始(秒)" width="150">
          <template slot-scope="s">
            <el-input-number v-model="s.row.开始" :min="0" :max="音频时长" :step="0.1" size="mini"
              controls-position="right" @change="片段改了()"></el-input-number>
          </template>
        </el-table-column>
        <el-table-column label="结束(秒)" width="150">
          <template slot-scope="s">
            <el-input-number v-model="s.row.结束" :min="0" :max="音频时长" :step="0.1" size="mini"
              controls-position="right" @change="片段改了()"></el-input-number>
          </template>
        </el-table-column>
        <el-table-column label="时长" width="100">
          <template slot-scope="s">{{ 格式化秒(s.row.结束 - s.row.开始) }}</template>
        </el-table-column>
        <el-table-column label="操作">
          <template slot-scope="s">
            <el-button size="mini" @click="试听片段(s.row)">试听</el-button>
            <el-button size="mini" @click="上移片段(s.$index)">上移</el-button>
            <el-button size="mini" @click="下移片段(s.$index)">下移</el-button>
            <el-button size="mini" type="danger" @click="删除片段(s.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="导出行">
        <span class="行内标签">导出方式</span>
        <el-radio-group v-model="导出模式">
          <el-radio label="合并">合并成一条</el-radio>
          <el-radio label="分别">分别导出多条</el-radio>
        </el-radio-group>
        <span class="行内标签">格式</span>
        <el-radio-group v-model="导出格式">
          <el-radio label="wav">WAV</el-radio>
          <el-radio label="mp3">MP3</el-radio>
        </el-radio-group>
        <el-button type="primary" :loading="导出中" :disabled="!片段列表.length" @click="导出()">开始导出</el-button>
      </div>

      <div v-if="导出结果.length" class="结果区">
        <div class="卡片标题">导出结果</div>
        <div v-for="(项, i) in 导出结果" :key="i" class="结果行">
          <span class="灰字">{{ 项.名称 }}</span>
          <audio :src="项.地址" controls class="结果播放器"></audio>
          <a :href="项.地址" :download="项.名称" target="_blank" class="下载链接">下载/打开</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script src="./index.js"></script>
<style src="./index.css"></style>
