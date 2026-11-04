<template>
  <div class="测试页">
    <div class="页标题">D全 导演台全能（MiniMax H3 · 一工作流六模式）</div>

    <div class="表单卡">
      <el-form label-width="110px">
        <!-- ① 生成模式 -->
        <div class="分组">
          <div class="分组标题">生成模式</div>
          <el-form-item label="模式">
            <el-radio-group v-model="表单.模式">
              <el-radio-button label="t2v">文生视频</el-radio-button>
              <el-radio-button label="i2v">图生视频</el-radio-button>
              <el-radio-button label="fl2v">首尾帧</el-radio-button>
              <el-radio-button label="r2v">参考主体</el-radio-button>
              <el-radio-button label="v2v">视频转视频</el-radio-button>
              <el-radio-button label="rv2v">参考改视频</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="本模式要填">
            <div class="说明块">{{ 模式说明 }}</div>
          </el-form-item>
          <el-form-item label="当前底膜">
            <div class="底膜">{{ 当前底膜提示 }}</div>
            <div class="说明块 弱">
              官方配对：t2v / i2v / fl2v → fl2va，r2v / v2v / rv2v → ref2va。
              换模式会自动换底膜文件，两个族不是同一个文件，首次切换需要重新加载模型。
            </div>
          </el-form-item>
          <el-form-item label="底膜精度">
            <el-radio-group v-model="表单.底膜精度">
              <el-radio-button v-for="项 in 底膜精度选项" :key="项" :label="项">
                {{ 底膜精度档表[项].简称 }}
              </el-radio-button>
            </el-radio-group>
            <div class="说明块 弱">{{ 当前底膜精度档.说明 }}</div>
            <div v-if="表单.底膜精度 !== 'auto'" class="说明块 警告">
              这会改变实际加载的模型文件（{{ 当前底膜文件 }}）。bf16↔int8 是**不同的文件**，
              切换后要重新加载底膜（int8 约 40 秒，bf16 约 5 分钟），已加载的缓存不会复用。
            </div>
          </el-form-item>
        </div>

        <!-- ② 素材 -->
        <div class="分组">
          <div class="分组标题">素材</div>

          <!-- t2v：无素材 -->
          <template v-if="表单.模式 === 't2v'">
            <el-form-item label="素材">
              <div class="说明块">本模式不使用任何上传素材，画面外观全靠提示词描述。</div>
            </el-form-item>
          </template>

          <!-- i2v：单张首帧图 -->
          <template v-if="表单.模式 === 'i2v'">
            <el-form-item label="首帧图">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="首帧成功" accept="image/*">
                <el-button size="small" icon="el-icon-upload2">上传首帧图</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="首帧媒体" :可删除="true" @点击="预览表单媒体()" @删除="删首帧()"></media-thumbs>
              <span v-if="!表单.输入图1" class="上传路径">必填。这张图就是整条视频的第 0 帧</span>
              <el-button v-if="表单.输入图1" size="mini" type="text" @click="清空首帧()">清空</el-button>
            </el-form-item>
            <el-form-item label="分段">
              <div class="说明块">
                图生视频按<strong>单段</strong>生成（一张图 → 一条片）。插件会给每一段都塞一份源图，
                多段等于每段都从这张图重新开始，中间会看到画面跳回起点，所以本模式不沿用工作流的两段结构。
              </div>
            </el-form-item>
          </template>

          <!-- fl2v：首帧 / 尾帧 -->
          <template v-if="表单.模式 === 'fl2v'">
            <el-form-item label="首帧">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="首帧成功" accept="image/*">
                <el-button size="small" icon="el-icon-upload2">上传首帧</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="首帧媒体" :可删除="true" @点击="预览表单媒体()" @删除="删首帧()"></media-thumbs>
              <span v-if="!表单.输入图1" class="上传路径">必填</span>
              <el-button v-if="表单.输入图1" size="mini" type="text" @click="清空首帧()">清空</el-button>
            </el-form-item>
            <el-form-item label="尾帧">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="尾帧成功" accept="image/*">
                <el-button size="small" icon="el-icon-upload2">上传尾帧</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="尾帧媒体" :可删除="true" @点击="预览表单媒体()" @删除="删尾帧()"></media-thumbs>
              <span class="上传路径">
                {{ 表单.输入图2 ? '首尾帧都有 → 提示词按 FL2VA（对齐行 + 三段）' : '可选。只填首帧也能生成，此时提示词按 I2VA' }}
              </span>
              <el-button v-if="表单.输入图2" size="mini" type="text" @click="清空尾帧()">清空</el-button>
            </el-form-item>
          </template>

          <!-- r2v：参考图 / 参考视频 / 参考音频 -->
          <template v-if="表单.模式 === 'r2v'">
            <el-form-item label="参考图">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="图成功" accept="image/*" multiple>
                <el-button size="small" icon="el-icon-upload2">上传参考图</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="参考图媒体" :可删除="true" @点击="预览表单媒体()" @删除="删图($event)"></media-thumbs>
              <span v-if="!表单.输入图1" class="上传路径">未上传。提示词里用 &lt;Picture 1&gt;、&lt;Picture 2&gt;… 按上传顺序引用</span>
              <span v-else class="上传路径">已传 {{ 已传图数 }}/9</span>
              <el-button v-if="表单.输入图1" size="mini" type="text" @click="清空参考()">清空</el-button>
            </el-form-item>
            <el-form-item label="参考视频">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="视频成功" accept="video/*">
                <el-button size="small" icon="el-icon-upload2">上传参考视频</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="参考视频媒体" :可删除="true" @点击="预览表单媒体()" @删除="删视频($event)"></media-thumbs>
              <span class="上传路径">可选，最多 3 个。提示词里用 &lt;Video 1&gt; 引用</span>
              <el-button v-if="有参考视频" size="mini" type="text" @click="清空参考视频()">清空</el-button>
            </el-form-item>
            <el-form-item label="参考音频">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="音频成功" accept="audio/*">
                <el-button size="small" icon="el-icon-upload2">上传参考音频</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="参考音频媒体" :可删除="true" @点击="预览表单媒体()" @删除="删音频($event)"></media-thumbs>
              <span class="上传路径">可选，最多 3 个。音频不进文本编码，只留 &lt;Audio 1&gt; 标签</span>
              <el-button v-if="有参考音频" size="mini" type="text" @click="清空参考音频()">清空</el-button>
            </el-form-item>
          </template>

          <!-- v2v / rv2v：源视频（输入视频1） -->
          <template v-if="需要源视频">
            <el-form-item label="源视频">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="源视频成功" accept="video/*">
                <el-button size="small" icon="el-icon-upload2">上传源视频</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="源视频媒体" :可删除="true" @点击="预览表单媒体()" @删除="删源视频()"></media-thumbs>
              <span v-if="!表单.输入视频1" class="上传路径">必填。提示词里它就是 &lt;Video 1&gt;</span>
              <el-button v-if="表单.输入视频1" size="mini" type="text" @click="清空源视频()">清空</el-button>
            </el-form-item>
            <el-form-item label="分段">
              <div class="说明块">
                源视频按<strong>单段</strong>重画：源片每一帧都当参考，出片长度跟页面时长一致，
                源片比时长长就截前面一段、短就按现有帧数跑。运镜与剪辑节奏默认保留，要改请在提示词里写清。
              </div>
            </el-form-item>
          </template>

          <!-- rv2v：参考图 / 参考音频（官方不支持参考视频，见下方说明） -->
          <template v-if="表单.模式 === 'rv2v'">
            <el-form-item label="参考图">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="图成功" accept="image/*" multiple>
                <el-button size="small" icon="el-icon-upload2">上传参考图</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="参考图媒体" :可删除="true" @点击="预览表单媒体()" @删除="删图($event)"></media-thumbs>
              <span v-if="!表单.输入图1" class="上传路径">可选。换了谁、换成什么，都靠参考图 + 提示词说清</span>
              <span v-else class="上传路径">已传 {{ 已传图数 }}/9</span>
              <el-button v-if="表单.输入图1" size="mini" type="text" @click="清空参考()">清空</el-button>
            </el-form-item>
            <el-form-item label="参考音频">
              <el-upload class="上传控件" :action="上传地址" :headers="上传头" name="文件" :show-file-list="false"
                         :on-success="音频成功" accept="audio/*">
                <el-button size="small" icon="el-icon-upload2">上传参考音频</el-button>
              </el-upload>
              <media-thumbs class="表单缩略" :大号="true" :媒体列表="参考音频媒体" :可删除="true" @点击="预览表单媒体()" @删除="删音频($event)"></media-thumbs>
              <span class="上传路径">可选，最多 3 个。音频不进文本编码，只留 &lt;Audio 1&gt; 标签</span>
              <el-button v-if="有参考音频" size="mini" type="text" @click="清空参考音频()">清空</el-button>
            </el-form-item>
            <el-form-item label="参考视频">
              <div class="说明块 弱">
                官方 rv2v 只支持「源视频 + 参考图 1–9 + 参考音频 1–3」，<strong>没有参考视频槽</strong>
                （插件 task_prompts.py 的 rv2v 说明，以及 reference_video_for_segment 里
                "not used by v2v" 的硬限制），所以本页不提供参考视频上传。
                要复用别的片子当参考，请改走「参考主体」模式，或直接用源视频本身。
              </div>
            </el-form-item>
          </template>
        </div>

        <!-- ③ 提示词 -->
        <div class="分组">
          <div class="分组标题">提示词</div>
          <ai-expand
            :技能列表="技能列表"
            :技能id.sync="扩写技能id"
            :需求.sync="扩写需求"
            :载入中="扩写中"
            :默认规则="当前扩写规则"
            :文案="扩写文案"
            :配置类型="扩写配置类型"
            @生成="扩写(带子模式规则($event))"></ai-expand>
          <el-form-item label="正向提示词">
            <el-input type="textarea" :rows="6" v-model="表单.正向提示词"
                      :placeholder="'描述要生成的画面（当前模式：' + 模式中文 + '）'"></el-input>
          </el-form-item>
          <el-form-item label="反向提示词">
            <el-input type="textarea" :rows="2" v-model="表单.反向提示词" placeholder="不想出现的内容"></el-input>
          </el-form-item>
        </div>

        <!-- ④ 画面 -->
        <div class="分组">
          <div class="分组标题">画面</div>
          <div class="两列">
            <el-form-item label="比例">
              <el-select v-model="表单.比例" size="small">
                <el-option v-for="项 in 比例选项" :key="项" :label="项" :value="项"></el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="一采MP">
              <el-input-number v-model="表单.一采MP" :min="0.1" :max="16" :step="0.1" controls-position="right"></el-input-number>
              <span class="上传路径">工作流默认 0.4</span>
            </el-form-item>
            <el-form-item label="画布">
              <span class="只读值">
                {{ 画布宽高 ? 画布宽高.宽 + ' × ' + 画布宽高.高 : '沿用工作流默认' }}
              </span>
              <span class="上传路径">比例 + 一采MP 算出，32 倍数，只读</span>
            </el-form-item>
            <el-form-item label="时长(秒)">
              <el-input-number v-model="表单.视频时长" :min="1" :max="60" :step="1" controls-position="right"></el-input-number>
              <span class="上传路径">工作流默认 15</span>
            </el-form-item>
            <el-form-item label="帧率">
              <span class="只读值">24 fps</span>
              <span class="上传路径">{{ 帧数说明 }}</span>
            </el-form-item>
            <el-form-item label="生成声音" v-if="声音可用">
              <el-switch v-model="表单.生成声音"></el-switch>
              <span class="上传路径">{{ 表单.生成声音 ? '生成（带 32kHz 立体声音轨）' : '静音档组件当前不可用，按「生成」提交' }}</span>
            </el-form-item>
          </div>
        </div>

        <!-- ⑤ 生成参数 -->
        <div class="分组">
          <div class="分组标题">生成参数</div>
          <div class="两列">
            <el-form-item label="seed">
              <el-input v-model="表单.seed" placeholder="每次进页面自动换一个；也可手改，清空则后端随机"></el-input>
            </el-form-item>
            <el-form-item label="cfg">
              <el-input-number v-model="表单.cfg" :min="0" :max="20" :step="0.1" controls-position="right"></el-input-number>
              <span class="上传路径">工作流默认 1</span>
            </el-form-item>
            <el-form-item label="步数">
              <el-input-number v-model="表单.步数" :min="1" :max="50" :step="1" controls-position="right"></el-input-number>
              <span v-if="表单.步数 === 8" class="上传路径">工作流带 8 步 turbo LoRA</span>
              <span v-else class="上传路径 警告">带的是 8 步 turbo LoRA，改离 8 步画质会明显下降</span>
            </el-form-item>
            <el-form-item label="采样器">
              <el-select v-model="表单.采样器" size="small">
                <el-option v-for="s in 采样器选项" :key="s" :label="s" :value="s"></el-option>
              </el-select>
            </el-form-item>
          </div>
        </div>

        <div class="提交行">
          <el-button type="primary" :loading="提交中" @click="提交任务()">提交任务</el-button>
          <el-button icon="el-icon-refresh" @click="拉任务列表()">刷新列表</el-button>
          <el-button type="text" @click="恢复工作流默认()">恢复工作流默认值</el-button>
        </div>
      </el-form>
    </div>

    <div class="表格区">
      <el-table :data="任务列表" border>
        <el-table-column prop="id" label="任务ID" width="80"></el-table-column>
        <el-table-column prop="状态" label="状态" width="100">
          <template slot-scope="s"><span :class="['状态标', '状态-' + s.row.状态]">{{ s.row.状态 }}</span></template>
        </el-table-column>
        <el-table-column label="提示词" min-width="220">
          <template slot-scope="s">
            <prompt-cell :文本="s.row.正向提示词" 标题="提示词全文"></prompt-cell>
          </template>
        </el-table-column>
        <el-table-column label="输入" width="130">
          <template slot-scope="s">
            <media-thumbs :媒体列表="输入媒体(s.row)" @点击="打开预览(s.row, $event)"></media-thumbs>
          </template>
        </el-table-column>
        <el-table-column label="参数" width="250">
          <template slot-scope="s">
            {{ 模式短名(s.row.模式) }} · {{ s.row.视频宽 }}×{{ s.row.视频高 }} · {{ s.row.视频时长 }}s
            · {{ s.row.步数 || '-' }}步 · cfg {{ s.row.cfg }} · {{ s.row.生成声音 ? '有声' : '静音' }}
            <span v-if="s.row.底膜精度 && s.row.底膜精度 !== 'auto'"> · 底膜{{ 底膜精度短名(s.row.底膜精度) }}</span>
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
