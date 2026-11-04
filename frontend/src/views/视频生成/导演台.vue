<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        当前="单镜生成"
        :剧名="剧名" :剧id="剧id" :集="集号" :标题="集标题" />

      <div class="剧集主体">
        <!-- 面包屑 -->
        <div class="面包屑条">
          <span class="可点" @click="$router.push('/video')">视频生成</span>
          <span> / </span>
          <span class="可点" @click="$router.push({ path:'/video/episode', query:$route.query })">{{ 剧名 }} 第 {{ 集号 }} 集</span>
          <span> / </span>
          <span class="可点" @click="$router.push({ path:'/video/shot', query:$route.query })">拆分分镜</span>
          <span> / </span>
          <span style="color:var(--字次)">单镜生成</span>
        </div>

        <!-- 载入 / 报错门控 -->
        <div v-if="载入中" class="卡片 空卡"><i class="el-icon-loading 空图标"></i><div class="空题">正在读取本集分镜…</div></div>
        <div v-else-if="载入报错" class="卡片 空卡">
          <i class="el-icon-warning-outline 空图标"></i><div class="空题">{{ 载入报错 }}</div>
          <el-button size="small" @click="载入()">重试</el-button>
        </div>

        <template v-else>
          <div v-if="!镜列表.length" class="卡片 空卡">
            <i class="el-icon-film 空图标"></i>
            <div class="空题">本集还没有分镜</div>
            <el-button size="small" type="primary" @click="$router.push({ path:'/video/shot', query:$route.query })">去拆分分镜</el-button>
          </div>

          <template v-else>
          <!-- 头卡：镜信息 + 切镜 -->
          <div class="卡片 头卡">
            <div class="头行">
              <span class="镜徽">{{ 当前镜.镜号 }}</span>
              <span class="镜题">{{ 当前镜.场次 }}</span>
              <span class="灰签">{{ 当前镜.景别 || '—' }} · {{ 当前镜.运镜 || '—' }} · {{ 当前镜.时长 || '—' }}</span>
              <span class="态签" :class="{ 生成中: 当前镜.视频状态 === '生成中', 已成: 当前镜.视频状态 === '已生成' }">{{ 当前镜.视频状态 }}</span>
              <div style="flex:1"></div>
              <el-button size="small" icon="el-icon-arrow-left" :disabled="!上一镜" @click="切镜(上一镜)">上一镜</el-button>
              <el-button size="small" :disabled="!下一镜" @click="切镜(下一镜)">下一镜<i class="el-icon-arrow-right el-icon--right"></i></el-button>
            </div>
            <div class="画面行">
              <span class="画标">画面</span><span>{{ 当前镜.画面 }}</span>
            </div>
            <div v-if="当前镜.台词 && 当前镜.台词 !== '（无）'" class="画面行">
              <span class="画标">台词</span><span>「{{ 当前镜.台词 }}」</span>
            </div>
          </div>

          <div class="两列">
            <!-- 左列：方式 + 资源 + 提示词 + 参数 -->
            <div class="左列">
              <!-- 生成方式：一级=任务类型分组，二级=组内模式（导演台全能六模式） -->
              <div class="卡片">
                <div class="卡题">生成方式
                  <span v-if="推荐键" class="推签">推荐：{{ 方式表[推荐键] ? 方式表[推荐键].名 : 推荐键 }}</span>
                </div>
                <div class="方式行">
                  <div v-for="组 in 方式分组们" :key="组.键" class="方式卡"
                       :class="{ 选中: 当前组键 === 组.键 }" @click="选组(组)">
                    <div class="式名">{{ 组.名 }}<span v-if="组.方式们.length > 1" class="组数">{{ 组.方式们.length }} 模式</span></div>
                    <div class="式说">{{ 组.说 }}</div>
                  </div>
                </div>
                <div v-if="当前组 && 当前组.方式们.length > 1" class="子方式行">
                  <span class="子题">选模式：</span>
                  <button v-for="键 in 当前组.方式们" :key="键" class="子方式"
                          :class="{ 活: 方式键 === 键 }" @click="选方式(键)">
                    {{ 方式表[键].名 }}<span v-if="方式表[键].模式" class="子码">{{ 方式表[键].模式 }}</span>
                  </button>
                </div>
                <div class="更多行">
                  <span class="灰签">当前走 {{ 方式表[方式键] ? 方式表[方式键].名 : '' }}{{ 是全能 ? '（导演台全能 · ' + 当前模式 + '）' : (方式表[方式键] ? '（' + 方式表[方式键].类型 + '）' : '') }}</span>
                </div>
              </div>

              <!-- 本镜资源区 -->
              <div class="卡片">
                <div class="卡题行">
                  <div class="卡题">本镜资源区 <span class="灰签">标注「首帧」「参考」决定它进哪个槽</span></div>
                  <div class="资操作">
                    <el-upload :show-file-list="false" accept="image/*" :http-request="上传本镜图">
                      <el-button size="mini" icon="el-icon-upload2" :loading="上传图中">上传图片</el-button>
                    </el-upload>
                    <el-button size="mini" icon="el-icon-picture" @click="开资产窗('图')">从资产引入</el-button>
                  </div>
                </div>
                <div class="资提示">
                  参考图按顺序占 <b>输入图 1..{{ 参考图上限 }}</b>（{{ 方式键 === '二采重绘' ? '本方式上限 8 张' : '上限 9 张' }}），
                  提示词里用 <b>&lt;Picture N&gt; / &lt;Subject N&gt;</b> 按顺序引用；「参考」图上的 ◀ ▶ 可调顺序
                </div>
                <div v-if="!本镜图们.length" class="资空">还没有资源图：上传一张、从资产引入，或在下方 AI 生成</div>
                <div class="图网格">
                  <div v-for="图 in 本镜图们" :key="'r' + 图.id" class="资图"
                       :class="{ 首帧: 图.标注 === '首帧', 参考: 图.标注 === '参考' }">
                    <img class="资图图" :src="媒体地址(图.url)" @click="预览图 = 图.url; 预览显 = true" />
                    <div class="资图注">
                      <input class="标输入" :value="图.标注" placeholder="标注"
                             @change="改图标注(图, $event.target.value)" />
                      <span class="源签">{{ 图.来源 }}</span>
                    </div>
                    <div class="资图钮">
                      <button v-if="图.标注 === '参考'" class="微钮" title="前移（Picture 顺序）" @click="参考图换位(图, -1)">◀</button>
                      <button v-if="图.标注 === '参考'" class="微钮" title="后移" @click="参考图换位(图, 1)">▶</button>
                      <button class="微钮" :class="{ 活: 图.标注 === '首帧' }" @click="设角色(图, '首帧')">首帧</button>
                      <button v-if="方式键 === '首尾帧'" class="微钮" :class="{ 活: 图.标注 === '尾帧' }" @click="设角色(图, '尾帧')">尾帧</button>
                      <button class="微钮" :class="{ 活: 图.标注 === '参考' }" @click="设角色(图, '参考')">参考</button>
                      <button class="微钮 删" @click="删图(图)">×</button>
                    </div>
                  </div>
                </div>
                <!-- 参考视频槽（参考主体 / 多参考 / 参考生视频 用，≤3） -->
                <div v-if="方式用参考视频" class="媒行">
                  <div class="媒题">参考视频 ≤3 <span class="灰签">提示词里用 &lt;Video 1&gt;… 按顺序引用</span></div>
                  <div class="媒操作">
                    <el-upload :show-file-list="false" accept="video/*" :http-request="上传参考视频">
                      <el-button size="mini" icon="el-icon-upload2">上传视频</el-button>
                    </el-upload>
                    <el-select v-if="已生成版本们.length" :value="''" size="mini" style="width:190px"
                               placeholder="从本镜已生成版本添加" @change="加参考视频($event)">
                      <el-option v-for="版 in 已生成版本们" :key="'rvv' + 版.id" :label="'版#' + 版.id" :value="版.url" />
                    </el-select>
                  </div>
                  <div v-if="参考视频们.length" class="媒列">
                    <div v-for="(u, i) in 参考视频们" :key="'rv' + i" class="媒项">
                      <video class="媒预" :src="媒体地址(u)" muted></video>
                      <div class="媒名">视频{{ i + 1 }}<button class="微钮 删" @click="删参考视频(i)">×</button></div>
                    </div>
                  </div>
                </div>
                <!-- 参考音频槽（≤3） -->
                <div v-if="方式用参考音频" class="媒行">
                  <div class="媒题">参考音频 ≤3 <span class="灰签">音频不进文本编码，只留 &lt;Audio N&gt; 标签</span></div>
                  <div class="媒操作">
                    <el-upload :show-file-list="false" accept="audio/*" :http-request="上传参考音频">
                      <el-button size="mini" icon="el-icon-upload2">上传音频</el-button>
                    </el-upload>
                    <el-button size="mini" icon="el-icon-microphone" @click="开资产窗('音色')">从资产引入</el-button>
                  </div>
                  <div v-if="参考音频们.length" class="媒列">
                    <div v-for="(u, i) in 参考音频们" :key="'ra' + i" class="媒项 媒音">
                      <audio class="媒音预" :src="媒体地址(u)" controls preload="none"></audio>
                      <div class="媒名">音频{{ i + 1 }}<button class="微钮 删" @click="删参考音频(i)">×</button></div>
                    </div>
                  </div>
                </div>
                <!-- AI 生成图 -->
                <div class="AI图行">
                  <el-input v-model="AI图提示词" size="mini" class="AI图入"
                            placeholder="AI 生图：写想要的本镜首帧画面（用首帧/参考图为底改）" @keyup.enter.native="AI生成图()" />
                  <el-button size="mini" type="primary" plain :loading="AI图中" @click="AI生成图()">AI 生成图</el-button>
                </div>
                <!-- 源视频槽（二采重绘 / v2v / rv2v 用） -->
                <div v-if="需要源视频" class="源视频行">
                  <span class="源标">源视频（改哪一版）：</span>
                  <el-select v-model="源视频url" size="mini" style="width:320px" placeholder="选该镜一版已生成的视频">
                    <el-option v-for="版 in 已生成版本们" :key="'sv' + 版.id"
                               :label="'版#' + 版.id + (版.方式 ? ' · ' + (方式表[版.方式] ? 方式表[版.方式].名 : 版.方式) : '') + (版.选中 ? ' · 当前选用' : '')"
                               :value="版.url" />
                  </el-select>
                  <span v-if="!已生成版本们.length" class="灰签">该镜还没有已生成视频，先换别的方式生成一版</span>
                </div>
              </div>

              <!-- 提示词 -->
              <div class="卡片">
                <div class="卡题行">
                  <div class="卡题">正向提示词</div>
                  <el-button size="mini" @click="用草稿()">用画面草稿</el-button>
                </div>
                <!-- AI 扩写：直接复用共用扩写行，配置 key 指向对应原测试页（扩写:/test/d-all:<模式> 等），
                     规则与原页同一份，改了两边同步生效。扩写行根节点是 el-form-item，必须包 el-form -->
                <el-form size="small" @submit.native.prevent>
                  <ai-expand
                    :技能列表="技能列表"
                    :技能id.sync="扩写技能id"
                    :需求.sync="扩写需求"
                    :载入中="扩写中"
                    :默认规则="扩写默认规则"
                    :文案="扩写文案"
                    :配置类型="扩写配置类型"
                    @生成="AI扩写($event)"
                  />
                </el-form>
                <el-input type="textarea" :rows="4" v-model="提示词" class="正入"
                          placeholder="本镜出视频的正向提示词（保存后落库，下次进来自动带出）" />
                <el-input v-if="显示反向 && 本方式有反向" type="textarea" :rows="2" v-model="反向提示词" class="正入"
                          placeholder="反向提示词（不想出现的内容，可选）" />
                <div class="行间">
                  <el-button v-if="本方式有反向" size="mini" type="text" @click="显示反向 = !显示反向">{{ 显示反向 ? '收起反向提示词' : '加反向提示词' }}</el-button>
                  <div style="flex:1"></div>
                  <el-button size="mini" :loading="存镜中" @click="保存镜()">保存提示词到分镜</el-button>
                </div>
              </div>

              <!-- 参数 + 提交 -->
              <div class="卡片">
                <div class="卡题行">
                  <div class="卡题">参数 <span class="灰签">{{ 方式表[方式键] ? 方式表[方式键].名 : '' }}{{ 是全能 ? '（导演台全能 · ' + 模式中文 + '）' : '' }}</span></div>
                  <el-button v-if="是全能" size="mini" type="text" @click="恢复工作流默认()">恢复工作流默认</el-button>
                </div>

                <!-- 底膜（导演台全能六模式） -->
                <div v-if="是全能" class="底膜行">
                  <label class="参项"><span>底膜精度</span>
                    <el-select v-model="底膜精度" size="mini" style="width:150px">
                      <el-option v-for="k in 底膜精度键们" :key="k" :label="底膜精度档表[k].简称" :value="k" />
                    </el-select>
                  </label>
                  <div class="底膜说">
                    当前底膜 <b>{{ 当前底膜提示 }}</b><br />
                    {{ 底膜精度档表[底膜精度].说明 }}。官方配对：t2v / i2v / fl2v → fl2va，r2v / v2v / rv2v → ref2va，
                    换模式会自动换底膜文件。bf16↔int8 是<b>不同的文件</b>，切换后要重新加载底膜（int8 约 40 秒，bf16 约 5 分钟）。
                  </div>
                </div>

                <!-- 本方式素材构成 -->
                <div class="素材行"><span class="素标">素材</span>{{ 素材说明 }}</div>

                <!-- 画面参数 -->
                <div class="参行">
                  <label class="参项"><span>比例</span>
                    <el-select v-model="参数.比例" size="mini" style="width:90px">
                      <el-option v-for="v in 比例选项" :key="v" :label="v" :value="v" />
                    </el-select>
                  </label>
                  <label class="参项"><span>一采MP{{ 是全能 ? '（工作流默认 0.4）' : (参数.一采MP == null ? '（留空 = 工作流默认 0.4）' : '') }}</span>
                    <el-input-number v-model="参数.一采MP" :min="0.1" :max="16" :step="0.1" size="mini" controls-position="right" style="width:100px" />
                  </label>
                  <label v-if="方式键 === '二采重绘'" class="参项"><span>二采MP（留空 = 工作流默认）</span>
                    <el-input-number v-model="参数.二采MP" :min="0.1" :max="16" :step="0.1" size="mini" controls-position="right" style="width:100px" />
                  </label>
                  <label class="参项"><span>时长(秒){{ 是全能 ? '（工作流默认 15）' : (方式键 === '二采重绘' ? '（默认 7）' : '') }}</span>
                    <el-input-number v-model="参数.时长" :min="1" :max="15" :step="1" size="mini" controls-position="right" style="width:100px" />
                  </label>
                  <span class="灰签" v-if="画布">画布 {{ 画布.宽 }} × {{ 画布.高 }}（比例 + 一采MP 算出，32 倍数{{ 是全能 || 方式键 === '参考生视频' ? '，只读' : '，随参数提交' }}）</span>
                </div>
                <div v-if="是全能" class="帧行">帧率 24 fps · {{ 帧数说明 }}</div>

                <!-- 生成参数：d-all 全套平铺直显（与原页一致，不折叠）/ d2 只有 seed+cfg -->
                <div v-if="显示高级参数" class="高级区">
                  <div class="高级题">生成参数{{ 是全能 ? '（工作流默认：cfg 1 · 8 步 turbo LoRA · res_multistep · 有声）' : '' }}</div>
                  <div class="参行">
                    <label class="参项"><span>seed{{ 是全能 ? '' : '（留空随机）' }}</span>
                      <span class="种排">
                        <el-input v-model="参数.seed" size="mini" style="width:150px" placeholder="留空随机" />
                        <button class="微钮" style="flex:0 0 auto;padding:2px 8px" @click="换新种子()">随机</button>
                      </span>
                    </label>
                    <label class="参项"><span>cfg</span>
                      <el-input-number v-model="参数.cfg" :min="0" :max="20" :step="0.1" size="mini" controls-position="right" style="width:90px" />
                    </label>
                    <template v-if="是全能">
                      <label class="参项"><span>步数（工作流带 8 步 turbo LoRA）</span>
                        <el-input-number v-model="参数.步数" :min="1" :max="50" size="mini" controls-position="right" style="width:90px" />
                      </label>
                      <label class="参项"><span>采样器</span>
                        <el-select v-model="参数.采样器" size="mini" style="width:140px">
                          <el-option v-for="s in 采样器选项" :key="s" :label="s" :value="s" />
                        </el-select>
                      </label>
                      <label class="参项"><span>生成声音</span>
                        <el-switch v-model="参数.生成声音" active-text="带 32kHz 立体声" />
                      </label>
                    </template>
                  </div>
                </div>

                <div class="提交行">
                  <el-button type="primary" :loading="提交中" @click="提交任务()">
                    {{ 提交中 ? '任务执行中…' : '提交任务' }}</el-button>
                  <span class="灰签">提交即入队（现有任务系统排队执行），出片自动写回本镜</span>
                </div>
              </div>
            </div>

            <!-- 右列：预览 + 版本 + 镜条 -->
            <div class="右列">
              <div class="卡片 预览卡">
                <video v-if="选中版" class="预览视频" :src="媒体地址(选中版.url)" controls playsinline></video>
                <div v-else class="预览空">
                  <i class="el-icon-video-camera"></i>
                  <div>还没有视频</div>
                  <div class="灰签">选好方式和素材，点「提交任务」</div>
                </div>
              </div>
              <div class="卡片">
                <div class="卡题行">
                  <div class="卡题">本集镜头 <span class="灰签">共 {{ 镜列表.length }} 镜 · 已生成 {{ 已完成数 }}</span></div>
                </div>
                <div class="镜条">
                  <div v-for="镜 in 镜列表" :key="'s' + 镜.镜号" class="镜块" :class="{ 活: 镜.镜号 === 当前镜.镜号 }" @click="切镜(镜)">
                    <div class="镜块号">{{ 镜.镜号 }}</div>
                    <div class="镜块态" :class="{ 已成: 镜.视频状态 === '已生成', 生成中: 镜.视频状态 === '生成中' }">{{ 镜.视频状态 === '已生成' ? '✓' : (镜.视频状态 === '生成中' ? '…' : '') }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 本镜生成视频：全部版本铺在下面，直接播放，可删、可指定正式使用 -->
          <div class="卡片 版卡">
            <div class="卡题行">
              <div class="卡题">本镜生成视频 <span class="灰签">{{ 本镜版本们.length }} 版 · 标「正式使用中」的那版进成片</span></div>
            </div>
            <div v-if="!本镜版本们.length" class="资空">还没有生成视频：选好方式和素材，点「提交任务」，出片后都摆在这里</div>
            <div class="版网格">
              <div v-for="版 in 本镜版本们" :key="'v' + 版.id" class="版块" :class="{ 正式: 版.选中 }">
                <video v-if="版.url" class="版视频" :src="媒体地址(版.url)" controls playsinline preload="metadata"></video>
                <div v-else class="版生成中"><i class="el-icon-loading"></i> 生成中…</div>
                <div class="版脚">
                  <span class="版式">{{ 版.方式 ? (方式表[版.方式] ? 方式表[版.方式].名 : 版.方式) : '—' }}</span>
                  <span v-if="版.选中" class="选签">正式使用中</span>
                  <span v-if="版.状态 === '失败'" class="败签">失败</span>
                  <span class="版时">{{ 版.创建时间 ? 版.创建时间.slice(5, 16).replace('T', ' ') : '' }}</span>
                  <span style="flex:1"></span>
                  <button v-if="版.状态 === '已生成' && !版.选中" class="微钮 主" title="成片合成取这一版" @click="设选中(版)">正式使用</button>
                  <button class="微钮 删" title="删除这一版" @click="删版本(版)">删</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部条 -->
          <div class="卡片 底条">
            <div class="行间">
              <span class="底题">{{ 已完成数 }} / {{ 镜列表.length }} 镜已生成</span>
              <span class="灰签">「连续生成」把未生成的镜按各自推荐方式排队提交（出片自动写回）</span>
            </div>
            <div class="行间">
              <el-button size="small" :loading="批量中" @click="连续生成()">{{ 批量中 ? '排队中…' : '连续生成未完成镜' }}</el-button>
              <el-button size="small" @click="$router.push({ path:'/video/shot', query:$route.query })">上一步：拆分分镜</el-button>
              <el-button size="small" type="primary" @click="$router.push({ path:'/video/film', query:$route.query })">下一步：成片</el-button>
            </div>
          </div>
          </template>
        </template>
      </div>
    </div>

    <!-- 从资产引入弹窗：已拆到 导演台资产窗弹窗.vue（注册别名 dt-asset-win）。
         显隐 资产窗显 留在本页（:visible.sync）；打开页签经 资产窗开签 传入；
         共享数据 资产行们/音色行们 用 props 下发；
         @引入图/@引入音色 回传本页 引入资产图/引入音色 落库 -->
    <dt-asset-win
      :visible.sync="资产窗显"
      :开签="资产窗开签"
      :资产行们="资产行们"
      :音色行们="音色行们"
      @引入图="引入资产图"
      @引入音色="引入音色" />

    <!-- 媒体预览弹窗：已拆到 导演台预览弹窗.vue（注册别名 dt-preview-win），预览图/预览显 留在本页 -->
    <dt-preview-win :visible.sync="预览显" :图="预览图" />
  </div>
</template>

<script>
import 剧集侧栏 from '@/共用/剧集侧栏/index.vue'
import { 取, 发, 基础地址, 取令牌 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'
import { 提交图片任务 } from '@/共用/图片任务'
import {
  方式表, 方式分组们, 方式来源页表, 方式默认参数, 算画布, 取镜秒, 新种子,
  拼任务参数, 校验方式, 推荐方式, 匹配资产, 提示词草稿,
  对账生成中版本, 落对账结果
} from '@/共用/分镜视频'
import 扩写行 from '@/共用/扩写行/index.vue'
import { 默认规则集, 扩写模式集 } from '@/views/测试/导演台全能/扩写规则'
import 导演台资产窗弹窗 from '@/views/视频生成/导演台资产窗弹窗.vue'
import 导演台预览弹窗 from '@/views/视频生成/导演台预览弹窗.vue'

/* ---- 底膜（与 /test/d-all 完全同一套：模式→族→文件，切换精度=换文件重载） ---- */
const 底膜族表 = {
  t2v: 'fl2va', i2v: 'fl2va', fl2v: 'fl2va',
  r2v: 'ref2va', v2v: 'ref2va', rv2v: 'ref2va'
}
const 底膜文件 = {
  ref2va: {
    auto: 'minimax_h3_ref2va_pruned_bf16.safetensors',
    bf16: 'minimax_h3_ref2va_pruned_bf16.safetensors',
    int8: 'minimax_h3_ref2va_pruned_int8_convrot.safetensors'
  },
  fl2va: {
    auto: 'minimax_h3_fl2va_pruned_int8_convrot.safetensors',
    bf16: 'minimax_h3_fl2va_pruned_bf16.safetensors',
    int8: 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'
  }
}
const 底膜精度档 = {
  auto: { 简称: '工作流默认', 说明: 'ref2va 用 bf16（工作流原值）、fl2va 用 int8，与现在完全一致', 体积: '' },
  bf16: { 简称: 'bf16', 说明: '两个族都用 bf16：画质上限最高，但显存最紧、首次加载约 5 分钟', 体积: '约 38 GB' },
  int8: { 简称: 'int8 convrot', 说明: '两个族都用 int8：官方推荐，显存约省一半、加载快很多，画质略降', 体积: '约 20 GB' }
}
/* i2v/v2v/rv2v 在 d-all 插件里是「单段」跑；t2v/r2v/fl2v 是 10s+5s 两段结构 */
const 单段模式 = ['i2v', 'v2v', 'rv2v']
const 模式中文表 = { t2v: '文生视频', i2v: '图生视频', fl2v: '首尾帧', r2v: '参考主体', v2v: '视频转视频', rv2v: '参考改视频' }

export default {
  name: 'Director',
  /* 弹窗子组件用 ASCII 别名注册（in-DOM 模板只认 ASCII 标签名，本项目既有约定） */
  components: {
    'ep-rail': 剧集侧栏,
    'ai-expand': 扩写行,
    'dt-asset-win': 导演台资产窗弹窗,
    'dt-preview-win': 导演台预览弹窗
  },
  data() {
    return {
      载入中: true,
      载入报错: '',
      /* 方式表/方式分组们 是 import 常量，模板里用必须挂到实例上（Vue2 模板只认 this） */
      方式表: 方式表,
      方式分组们: 方式分组们,
      镜列表: [],
      版本们: [],
      资产行们: [],
      音色行们: [],
      当前镜号: '',
      本镜图们: [],
      /* 从资产引入弹窗：显隐留在本页，筛选/页签状态在子组件内（打开页签经 资产窗开签 传入） */
      资产窗显: false,
      资产窗开签: '图',
      /* 生成表单。参数默认值=当前初始方式（参考生视频）的原页默认；切方式时按 方式默认参数 整套换 */
      方式键: '参考生视频',
      提示词: '',
      反向提示词: '',
      显示反向: true,
      源视频url: '',
      参考视频们: [],
      参考音频们: [],
      参数: { 比例: '16:9', 一采MP: null, 二采MP: 0.4, 时长: 5, seed: '', cfg: 1, 步数: 8, 采样器: 'res_multistep', 生成声音: true },
      方式参数已初始化: false,
      底膜精度: 'int8',
      底膜精度档表: 底膜精度档,
      比例选项: ['16:9', '9:16', '3:4', '4:3', '1:1', '2:3', '3:2', '21:9'],
      采样器选项: ['res_multistep', 'euler', 'euler_ancestral', 'dpmpp_2m', 'dpmpp_2m_sde', 'dpmpp_3m_sde', 'uni_pc', 'ddim'],
      AI图提示词: '',
      AI图中: false,
      /* 扩写（与对应原测试页同一套规则，见 扩写配置类型 computed） */
      技能列表: [],
      扩写技能id: '',
      扩写需求: '',
      扩写中: false,
      /* 状态 */
      提交中: false,
      存镜中: false,
      批量中: false,
      上传图中: false,
      预览图: '',
      预览显: false,
      监控定时器: null
    }
  },
  computed: {
    剧名() { return this.$route.query.name || '' },
    剧id() { return parseInt(this.$route.query.ep) || 0 },
    集号() { return parseInt(this.$route.query.集) || 1 },
    集标题() { return this.$route.query.标题 || '' },
    当前镜() {
      const 号 = this.当前镜号
      const 找 = this.镜列表.filter(function (x) { return x.镜号 === 号 })[0]
      return 找 || this.镜列表[0] || {}
    },
    序号() {
      const 页 = this
      return this.镜列表.findIndex(function (x) { return x.镜号 === 页.当前镜.镜号 })
    },
    上一镜() { return this.序号 > 0 ? this.镜列表[this.序号 - 1] : null },
    下一镜() { return this.序号 >= 0 && this.序号 < this.镜列表.length - 1 ? this.镜列表[this.序号 + 1] : null },
    本镜版本们() {
      const 号 = this.当前镜.镜号
      return this.版本们.filter(function (v) { return v.镜号 === 号 })
    },
    已生成版本们() {
      return this.本镜版本们.filter(function (v) { return v.状态 === '已生成' && v.url })
    },
    选中版() {
      const 选 = this.本镜版本们.filter(function (v) { return v.选中 && v.状态 === '已生成' && v.url })[0]
      return 选 || this.已生成版本们[0] || null
    },
    首帧url() {
      const 图 = this.本镜图们.filter(function (g) { return g.标注 === '首帧' })[0]
      return 图 ? 图.url : ''
    },
    尾帧url() {
      const 图 = this.本镜图们.filter(function (g) { return g.标注 === '尾帧' })[0]
      return 图 ? 图.url : ''
    },
    参考图们() {
      return this.本镜图们.filter(function (g) { return g.标注 === '参考' }).map(function (g) { return g.url })
    },
    需要源视频() {
      return this.方式键 === '二采重绘' || this.方式键 === '视频转视频' || this.方式键 === '参考改视频'
    },
    /* ---- 方式派生（对齐四个原页面） ---- */
    是全能() {
      return !!(方式表[this.方式键] && 方式表[this.方式键].模式)
    },
    当前组键() {
      const 元 = 方式表[this.方式键]
      return 元 ? 元.类型 : ''
    },
    当前组() {
      const 页 = this
      return 方式分组们.filter(function (g) { return g.键 === 页.当前组键 })[0] || null
    },
    /* ---- 扩写：与对应原测试页同一套规则（改了两边同步生效） ----
       d-all 六模式 → 扩写:/test/d-all:<模式>（该页本就按模式分六份）；
       其余三个方式 → 扩写:<原页路由>（原页用组件默认 key） */
    扩写配置类型() {
      const 元 = 方式表[this.方式键]
      if (!元) return '扩写:/video/director'
      if (元.模式) return '扩写:/test/d-all:' + 元.模式
      return '扩写:' + (方式来源页表[this.方式键] || '/video/director')
    },
    扩写模式值() {
      const 元 = 方式表[this.方式键]
      if (!元) return 'multi_reference'
      return 元.模式 ? (扩写模式集[元.模式] || 'single_frame') : 'multi_reference'
    },
    扩写默认规则() {
      const 元 = 方式表[this.方式键]
      return (元 && 元.模式) ? (默认规则集[元.模式] || '') : ''
    },
    扩写文案() {
      const 元 = 方式表[this.方式键] || {}
      const 名 = 元.名 || this.方式键
      const 源页 = 元.模式 ? ('/test/d-all（' + 名 + ' 模式）') : (方式来源页表[this.方式键] || '本页')
      return {
        配置文字: '扩写提示词配置（' + 名 + '）',
        配置说明: '这里是「' + 名 + '」用的扩写规则，与 ' + 源页 + ' 页同一份（在这边改，原页也生效），会原样附加到本次扩写的系统提示词里。'
      }
    },
    当前模式() {
      const 元 = 方式表[this.方式键]
      return 元 && 元.模式 ? 元.模式 : ''
    },
    模式中文() {
      return 模式中文表[this.当前模式] || ''
    },
    当前底膜族() {
      return 底膜族表[this.当前模式] || 'ref2va'
    },
    当前底膜文件() {
      const 族表 = 底膜文件[this.当前底膜族] || {}
      return 族表[this.底膜精度] || 族表.auto || ''
    },
    当前底膜提示() {
      const 档 = 底膜精度档[this.底膜精度] || 底膜精度档.auto
      const 体积 = 档.体积 ? '（' + 档.体积 + '）' : ''
      return this.当前底膜族 + ' · ' + this.当前底膜文件 + 体积
    },
    底膜精度键们() {
      return Object.keys(底膜精度档)
    },
    帧数说明() {
      const 秒 = Number(this.参数.时长) || 0
      if (单段模式.indexOf(this.当前模式) >= 0) {
        const 帧 = Math.max(5, Math.round(秒 * 24))
        return '单段 → ' + (帧 + (5 - (帧 % 17)) % 17) + ' 帧'
      }
      if (秒 === 15) return '工作流分段 10s+5s → 243+124 = 367 帧（与工作流默认一致）'
      return '后端按工作流分段比例分配时长，每段补到 17k+5（改时长会等比缩放分段）'
    },
    方式用参考视频() {
      return this.方式键 === '参考主体' || this.方式键 === '多参考生视频' || this.方式键 === '参考生视频'
    },
    方式用参考音频() {
      return this.方式用参考视频 || this.方式键 === '参考改视频' || this.方式键 === '二采重绘'
    },
    /* 引入弹窗的筛选/分页 computed（资产窗图行们/资产窗图分页/资产窗音行们/资产窗音分页）
       已随弹窗拆到 导演台资产窗弹窗.vue */
    参考图上限() {
      return this.方式键 === '二采重绘' ? 8 : 9
    },
    素材说明() {
      const 段 = []
      if (this.方式键 === '文生视频') return '纯文字，不需要任何素材'
      if (this.当前模式 === 'i2v') return '首帧图 1 张（资源区标「首帧」，提示词里它是 <Picture 1>）'
      if (this.当前模式 === 'fl2v') return '首帧 1 张 + 尾帧 1 张（资源区标「首帧」「尾帧」）'
      if (this.当前模式 === 'v2v') return '源视频 1 条（下方选该镜已生成的一版）'
      if (this.方式键 === '二采重绘') return '源视频 1 条 · 参考图 ≤8（<Picture N>/<Subject N>）· 参考音频 ≤3（<Audio N>）'
      if (this.当前模式 === 'rv2v') return '源视频 1 条 · 参考图 ≤9（<Picture N>/<Subject N>）· 参考音频 ≤3（<Audio N>）'
      if (this.当前模式 === 'r2v') return '参考图 ≤9（<Picture N>/<Subject N>）· 参考视频 ≤3（<Video N>）· 参考音频 ≤3（<Audio N>）'
      if (this.方式键 === '多参考生视频') return '参考图 ≤9（<Picture N>/<Subject N>）· 参考视频 ≤3（<Video N>）· 参考音频 ≤3（<Audio N>）'
      if (this.方式键 === '参考生视频') return '参考图 ≤9 · 参考视频 ≤3 · 参考音频 ≤3'
      return ''
    },
    显示高级参数() {
      return this.是全能 || this.方式键 === '多参考生视频'
    },
    /* 反向提示词只有 d-all 六模式和 d2 原页有这个字段；t8/t10 原页没有就不显示 */
    本方式有反向() {
      return this.是全能 || this.方式键 === '多参考生视频'
    },
    推荐键() {
      const 命中 = 匹配资产(this.当前镜.画面, this.资产行们)
      return 推荐方式(this.当前镜, this.本镜图们, 命中.length, this.已生成版本们.length > 0)
    },
    画布() { return 算画布(this.参数.比例, this.参数.一采MP) },
    已完成数() {
      return this.镜列表.filter(function (x) { return x.视频状态 === '已生成' }).length
    }
  },
  watch: {
    /* 切镜后刷新资源区与源视频槽；切走前把没提交的提示词暂存，回来还在 */
    当前镜号(新号, 旧号) {
      const 页 = this
      if (旧号 && 页.剧id) {
        try {
          localStorage.setItem('导演台提示词:' + 页.剧id + ':' + 页.集号 + ':' + 旧号,
            JSON.stringify({ 提示词: 页.提示词 }))
        } catch (e) { /* 忽略 */ }
      }
      页.载本镜图()
    },
    /* 切方式：参数/底膜精度/反向词按方式各存一份（用对应模式的对应参数）；
       扩写技能与引导词也切到该方式自己那份（生成:/video/director:<方式键>:<技能id>） */
    方式键(新键, 旧键) {
      if (!新键 || !旧键 || 新键 === 旧键) return
      const 页 = this
      try {
        localStorage.setItem('导演台参数:' + 旧键, JSON.stringify({
          参数: 页.参数, 底膜精度: 页.底膜精度, 反向提示词: 页.反向提示词
        }))
      } catch (e) { /* 忽略 */ }
      let 存 = null
      try { 存 = JSON.parse(localStorage.getItem('导演台参数:' + 新键) || 'null') } catch (e) { 存 = null }
      if (存 && 存.参数) {
        页.参数 = Object.assign(页.默认参数(新键), 存.参数)
        页.底膜精度 = 存.底膜精度 || 'int8'
        页.反向提示词 = String(存.反向提示词 == null ? '' : 存.反向提示词)
        页.方式参数已初始化 = true
      } else {
        /* 没有存档：整套套用该方式对应原页的默认值（d-all 六模式=16:9/15s/新种子/cfg1/8步/res_multistep/有声） */
        页.应用方式默认(新键)
      }
      /* 扩写规则不用手动切：扩写行组件 watch 配置类型，方式一变自动重载对应原页那份 */
    }
  },
  created() {
    const q镜 = String(this.$route.query.镜 || '')
    if (q镜) this.当前镜号 = q镜
    this.载入()
    this.拉技能列表()
  },
  beforeDestroy() {
    if (this.监控定时器) { clearInterval(this.监控定时器); this.监控定时器 = null }
  },
  methods: {
    媒体地址,
    async 载入() {
      const 页 = this
      页.载入中 = true
      页.载入报错 = ''
      try {
        const 分镜据 = await 取('/api/分镜/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.镜列表 = (分镜据 && 分镜据.分镜们) || []
        if (!页.当前镜号 || !页.镜列表.some(function (x) { return x.镜号 === 页.当前镜号 })) {
          页.当前镜号 = 页.镜列表.length ? 页.镜列表[0].镜号 : ''
        }
        const 版据 = await 取('/api/分镜/视频?剧id=' + 页.剧id + '&集号=' + 页.集号)
        页.版本们 = (版据 && 版据.版本们) || []
        try {
          const 美据 = await 取('/api/美术/列表?剧id=' + 页.剧id)
          const 全行们 = (美据 && 美据.行们) || []
          页.资产行们 = 全行们.filter(function (行) { return 行.图们 && 行.图们.length })
          /* 有音色的角色卡（音色url 已合成），供参考音频「从资产引入」 */
          页.音色行们 = 全行们.filter(function (行) { return 行.定装 && 行.定装.音色url })
        } catch (e2) { 页.资产行们 = []; 页.音色行们 = [] }
        await 页.载本镜图()
      } catch (e) {
        页.载入报错 = (e && e.message) || '载入失败'
      }
      页.载入中 = false
    },
    async 载本镜图() {
      const 页 = this
      if (!页.当前镜.镜号) { 页.本镜图们 = []; 页.预填(); return }
      try {
        const 据 = await 取('/api/分镜/图?剧id=' + 页.剧id + '&集号=' + 页.集号 + '&镜号=' + encodeURIComponent(页.当前镜.镜号))
        页.本镜图们 = (据 && 据.图们) || []
      } catch (e) {
        页.本镜图们 = []
      }
      页.预填()
    },
    /* 进镜预填：方式（镜上存的 → 推荐）、提示词（切镜暂存 → 镜上存的 → 草稿）、参数时长对齐分镜、源视频默认选中版 */
    预填() {
      const 页 = this
      const 镜 = 页.当前镜
      if (!镜.镜号) return
      let 暂存 = null
      try { 暂存 = JSON.parse(localStorage.getItem('导演台提示词:' + 页.剧id + ':' + 页.集号 + ':' + 镜.镜号) || 'null') } catch (e) { 暂存 = null }
      页.提示词 = (暂存 && 暂存.提示词) || 镜.生成提示词 || 提示词草稿(镜)
      const 新键 = 镜.生成方式 && 方式表[镜.生成方式] ? 镜.生成方式 : (this.推荐键 || '参考生视频')
      if (新键 !== this.方式键) {
        this.方式键 = 新键 /* watch 里套用该方式存档或原页默认 */
      } else if (!this.方式参数已初始化) {
        this.应用方式默认(新键) /* 首次进页方式没变过：也要套用对应原页默认 */
      }
      if (镜.时长) this.参数.时长 = 取镜秒(镜.时长, 5)
      this.源视频url = (this.选中版 && this.选中版.url) || ''
      this.自动带参考()
    },
    /* 智能带参考：画面里认出的资产名 → 该资产当前图还没有进本镜资源区就引入一排 */
    async 自动带参考() {
      const 页 = this
      const 镜 = 页.当前镜
      if (!镜.镜号 || !页.资产行们.length) return
      const 命中 = 匹配资产(镜.画面, 页.资产行们)
      if (!命中.length) return
      const 已有 = {}
      页.本镜图们.forEach(function (g) { 已有[g.url] = 1 })
      for (let i = 0; i < 命中.length; i++) {
        const 行 = 命中[i]
        const 当前图 = (行.图们 || []).filter(function (g) { return g.状态 === '当前' })[0]
        if (!当前图 || 已有[当前图.url]) continue
        try {
          await 发('/api/分镜/图保存', {
            剧id: 页.剧id, 集号: 页.集号, 镜号: 镜.镜号, 动作: '添加',
            url: 当前图.url, 标注: '参考', 来源: '资产'
          })
          已有[当前图.url] = 1
        } catch (e) { /* 引入失败不阻塞 */ }
      }
      /* 有新增就重拉资源区 */
      try {
        const 据 = await 取('/api/分镜/图?剧id=' + 页.剧id + '&集号=' + 页.集号 + '&镜号=' + encodeURIComponent(镜.镜号))
        页.本镜图们 = (据 && 据.图们) || []
      } catch (e) { /* 忽略 */ }
    },
    选组(组) {
      if (!组 || !组.方式们 || !组.方式们.length) return
      /* 单方式组直接切；多模式组（导演台全能）只展开二级目录，当前不在组里就默认选第一个 */
      if (组.方式们.length === 1) { this.选方式(组.方式们[0]); return }
      if (组.方式们.indexOf(this.方式键) < 0) this.选方式(组.方式们[0])
    },
    选方式(键) {
      if (!方式表[键]) return
      this.方式键 = 键
      if (this.是全能 && !String(this.反向提示词 || '').trim()) this.反向提示词 = 'bad video'
      if (this.需要源视频 && !this.源视频url) this.源视频url = (this.选中版 && this.选中版.url) || ''
    },
    /* 某方式的默认参数：逐字对齐对应原测试页 data() 的表单默认值（见 分镜视频.js 方式默认参数）。
       seed:'新' → 进页填新随机种子（d-all 规则）；一采MP '' → null（el-input-number 显示为空=工作流默认 0.4） */
    默认参数(键) {
      const 基 = { 比例: '9:16', 一采MP: 0.4, 二采MP: 0.4, 时长: 5, seed: '', cfg: 1, 步数: 8, 采样器: 'res_multistep', 生成声音: true }
      const 出 = Object.assign(基, 方式默认参数[键] || {})
      if (出.seed === '新') 出.seed = 新种子()
      if (出.一采MP === '') 出.一采MP = null
      if (出.二采MP === '') 出.二采MP = null
      return 出
    },
    /* 整套套用某方式的默认（参数 + 底膜精度 + 反向词）；只在进页/切方式且无存档时调，不覆盖用户手调 */
    应用方式默认(键) {
      const 默 = this.默认参数(键)
      this.参数 = 默
      this.底膜精度 = 'int8'
      if (默.反向提示词 != null) this.反向提示词 = 默.反向提示词
      this.方式参数已初始化 = true
    },
    /* ---------- 参考视频 / 参考音频槽（≤3，对齐原页面上传行） ---------- */
    async 上传参考视频(选项) {
      const 页 = this
      try {
        const 路径 = await 页.传文件(选项.file)
        if (页.参考视频们.length >= 3) { 页.$message.warning('参考视频最多 3 个'); return }
        页.参考视频们.push(路径)
        页.$message.success('已加参考视频 ' + 页.参考视频们.length)
      } catch (e) { 页.$message.error('上传失败：' + ((e && e.message) || e)) }
    },
    加参考视频(url) {
      if (!url) return
      if (this.参考视频们.length >= 3) { this.$message.warning('参考视频最多 3 个'); return }
      if (this.参考视频们.indexOf(url) < 0) this.参考视频们.push(url)
    },
    删参考视频(下标) { this.参考视频们.splice(下标, 1) },
    async 上传参考音频(选项) {
      const 页 = this
      try {
        const 路径 = await 页.传文件(选项.file)
        if (页.参考音频们.length >= 3) { 页.$message.warning('参考音频最多 3 个'); return }
        页.参考音频们.push(路径)
        页.$message.success('已加参考音频 ' + 页.参考音频们.length)
      } catch (e) { 页.$message.error('上传失败：' + ((e && e.message) || e)) }
    },
    删参考音频(下标) { this.参考音频们.splice(下标, 1) },
    /* 参考图槽位顺序：◀▶ 与相邻「参考」图换排序（提示词 <Picture N> 按这个顺序引用） */
    async 参考图换位(图, 方向) {
      const 页 = this
      const 参考们 = 页.本镜图们.filter(function (g) { return g.标注 === '参考' })
      const k = 参考们.findIndex(function (g) { return g.id === 图.id })
      const j = k + 方向
      if (k < 0 || j < 0 || j >= 参考们.length) return
      const a = 参考们[k], b = 参考们[j]
      try {
        await 页.落本镜图({ 动作: '编辑', id: a.id, 排序: (b.排序 || 0) })
        await 页.落本镜图({ 动作: '编辑', id: b.id, 排序: (a.排序 || 0) })
      } catch (e) {
        页.$message.error('调序失败：' + ((e && e.message) || e))
      }
    },
    换新种子() { this.参数.seed = 新种子() },
    恢复工作流默认() {
      Object.assign(this.参数, {
        seed: 新种子(), cfg: 1, 比例: '16:9', 一采MP: 0.4,
        时长: 15, 生成声音: true, 步数: 8, 采样器: 'res_multistep'
      })
      this.底膜精度 = 'int8'
      this.反向提示词 = 'bad video'
      this.$message.success('已恢复工作流默认参数（比例/时长按需再调）')
    },
    切镜(镜) {
      if (!镜) return
      this.当前镜号 = 镜.镜号
      const 查 = Object.assign({}, this.$route.query, { 镜: 镜.镜号 })
      this.$router.replace({ query: 查 })
    },
    /* ---------- 资源区 ---------- */
    async 落本镜图(载荷) {
      const 页 = this
      const 据 = await 发('/api/分镜/图保存', Object.assign({
        剧id: 页.剧id, 集号: 页.集号, 镜号: 页.当前镜.镜号
      }, 载荷))
      const 刷 = await 取('/api/分镜/图?剧id=' + 页.剧id + '&集号=' + 页.集号 + '&镜号=' + encodeURIComponent(页.当前镜.镜号))
      页.本镜图们 = (刷 && 刷.图们) || []
      return 据
    },
    async 传文件(文件) {
      const 表 = new FormData()
      表.append('文件', 文件)
      const 响 = await fetch(基础地址 + '/api/上传', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + 取令牌() },
        body: 表
      })
      const 数据 = await 响.json()
      if (!数据.ok) throw new Error(数据.error || '上传失败')
      return 数据.路径
    },
    async 上传本镜图(选项) {
      const 页 = this
      if (!页.当前镜.镜号) return
      页.上传图中 = true
      try {
        const 路径 = await 页.传文件(选项.file)
        const 已有首帧 = 页.本镜图们.some(function (g) { return g.标注 === '首帧' })
        await 页.落本镜图({ 动作: '添加', url: 路径, 标注: 已有首帧 ? '参考' : '首帧', 来源: '上传' })
        页.$message.success('已上传并进资源区')
      } catch (e) {
        页.$message.error('上传失败：' + ((e && e.message) || e))
      }
      页.上传图中 = false
    },
    /* 引入资产图到本镜资源区——由子组件 导演台资产窗弹窗 @引入图 触发（落库走共享的 落本镜图） */
    async 引入资产图(行, 图) {
      const 页 = this
      try {
        await 页.落本镜图({ 动作: '添加', url: 图.url, 标注: '参考', 来源: '资产' })
        页.$message.success('已引入「' + 行.名称 + '」')
      } catch (e) {
        页.$message.error('引入失败：' + ((e && e.message) || e))
      }
    },
    /* 打开引入弹窗：'图'=参考图页签，'音色'=音色页签。
       筛选/页签状态已随弹窗拆到 导演台资产窗弹窗.vue（子组件 watch visible 时按 开签 重置） */
    开资产窗(标签) {
      this.资产窗开签 = 标签 === '音色' ? '音色' : '图'
      this.资产窗显 = true
    },
    /* 引入角色音色为参考音频（≤3，与上传同一上限）——由子组件 导演台资产窗弹窗 @引入音色 触发 */
    引入音色(行) {
      const 页 = this
      if (页.参考音频们.length >= 3) { 页.$message.warning('参考音频最多 3 个'); return }
      页.参考音频们.push(行.定装.音色url)
      页.$message.success('已引入「' + 行.名称 + '」的音色为参考音频')
    },
    async 改图标注(图, 值) {
      const 页 = this
      try {
        await 页.落本镜图({ 动作: '编辑', id: 图.id, 标注: 值 })
      } catch (e) {
        页.$message.error('保存标注失败：' + ((e && e.message) || e))
      }
    },
    async 设角色(图, 角色) {
      const 页 = this
      const 新标注 = 图.标注 === 角色 ? '' : 角色
      try {
        await 页.落本镜图({ 动作: '编辑', id: 图.id, 标注: 新标注 })
      } catch (e) {
        页.$message.error('设置失败：' + ((e && e.message) || e))
      }
    },
    async 删图(图) {
      const 页 = this
      try {
        await 页.落本镜图({ 动作: '删除', id: 图.id })
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    },
    /* AI 生成图：三图编辑一致版，图1=首帧或第一张参考图，产物落资源区（来源=生成） */
    async AI生成图() {
      const 页 = this
      const 提示 = String(页.AI图提示词 || '').trim()
      if (!提示) { 页.$message.warning('先写一句想要的首帧画面'); return }
      const 底图 = 页.首帧url || (页.参考图们[0] || '')
      if (!底图) { 页.$message.warning('先上传或引入一张图作底，再 AI 生成'); return }
      页.AI图中 = true
      try {
        const 行 = await 提交图片任务({ 类型: '三图编辑一致版', 参数: { 输入图1: 底图, 正向提示词: 提示 } })
        const 产物 = 行.产物图片2 || 行.产物图片
        if (!产物) throw new Error('任务成功但没有产物图片')
        const 已有首帧 = 页.本镜图们.some(function (g) { return g.标注 === '首帧' })
        await 页.落本镜图({ 动作: '添加', url: 产物, 标注: 已有首帧 ? '参考' : '首帧', 来源: '生成', 提示词: 提示 })
        页.$message.success('AI 图已生成并进资源区')
      } catch (e) {
        页.$message.error('AI 生成图失败：' + ((e && e.message) || e))
      }
      页.AI图中 = false
    },
    /* ---------- 扩写（共用扩写行，规则与对应原测试页同一份） ---------- */
    async 拉技能列表() {
      const 页 = this
      try {
        const 据 = await 取('/api/提示词/技能列表?分类=minimax')
        页.技能列表 = (据 && 据.列表) || []
        if (!页.扩写技能id && 页.技能列表.length) 页.扩写技能id = 页.技能列表[0].id
      } catch (e) { /* 不阻塞 */ }
    },
    /* 扩写引用 = 当前槽位里已填的输入媒体，按 图N/视频N/音频N 命名（与任务提交的槽位口径一致） */
    扩写引用() {
      const 页 = this
      const 元 = 方式表[页.方式键] || {}
      const 表 = {}
      const 挂图 = function (们, 上限) {
        (们 || []).slice(0, 上限 || 9).forEach(function (u, i) { if (u) 表['输入图' + (i + 1)] = u })
      }
      const 挂视频 = function (们) { (们 || []).forEach(function (u, i) { if (u) 表['输入视频' + (i + 1)] = u }) }
      const 挂音频 = function (们) { (们 || []).forEach(function (u, i) { if (u) 表['输入音频' + (i + 1)] = u }) }
      if (元.模式 === 'i2v') { if (页.首帧url) 表['输入图1'] = 页.首帧url }
      else if (元.模式 === 'fl2v') {
        if (页.首帧url) 表['输入图1'] = 页.首帧url
        if (页.尾帧url) 表['输入图2'] = 页.尾帧url
      } else if (元.模式 === 'v2v') { if (页.源视频url) 表['输入视频1'] = 页.源视频url }
      else if (元.模式 === 'rv2v') {
        if (页.源视频url) 表['输入视频1'] = 页.源视频url
        挂图(页.参考图们); 挂音频(页.参考音频们)
      } else if (元.模式 === 'r2v') {
        挂图(页.参考图们); 挂视频(页.参考视频们); 挂音频(页.参考音频们)
      } else if (页.方式键 === '参考生视频' || 页.方式键 === '多参考生视频') {
        挂图(页.参考图们); 挂视频(页.参考视频们); 挂音频(页.参考音频们)
      } else if (页.方式键 === '二采重绘') {
        if (页.源视频url) 表['输入视频1'] = 页.源视频url
        挂图(页.参考图们, 8); 挂音频(页.参考音频们)
      }
      const 引用 = []
      for (let i = 1; i <= 9; i++) if (表['输入图' + i]) 引用.push({ 名称: '图' + i, 类型: 'image' })
      for (let i = 1; i <= 3; i++) if (表['输入视频' + i]) 引用.push({ 名称: '视频' + i, 类型: 'video' })
      for (let i = 1; i <= 3; i++) if (表['输入音频' + i]) 引用.push({ 名称: '音频' + i, 类型: 'audio' })
      return 引用
    },
    async AI扩写(附加规则) {
      const 页 = this
      if (!页.扩写技能id) { 页.$message.warning('先选提示词技能'); return }
      if (!String(页.扩写需求 || '').trim()) { 页.$message.warning('先填扩写需求'); return }
      页.扩写中 = true
      try {
        const 据 = await 发('/api/提示词/扩写', {
          技能id: 页.扩写技能id,
          模式: 页.扩写模式值,
          需求: String(页.扩写需求).trim(),
          引用: 页.扩写引用(),
          附加规则: 附加规则 || ''
        })
        页.提示词 = 据.提示词 || 页.提示词
        页.$message.success('已扩写并填入正向提示词')
      } catch (e) {
        页.$message.error('扩写失败：' + ((e && e.message) || e))
      }
      页.扩写中 = false
    },
    用草稿() {
      this.提示词 = 提示词草稿(this.当前镜)
      this.$message.success('已按画面/台词填入草稿')
    },
    /* ---------- 分镜落库 ---------- */
    async 保存镜(静默) {
      const 页 = this
      const 镜 = 页.当前镜
      if (!镜.镜号) return
      镜.生成方式 = 页.方式键
      镜.生成提示词 = 页.提示词
      页.存镜中 = true
      try {
        await 页.存全部分镜()
        if (!静默) 页.$message.success('已保存：' + 镜.镜号 + ' 的生成方式与提示词')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.存镜中 = false
    },
    async 存全部分镜() {
      const 页 = this
      const 镜们 = 页.镜列表.map(function (镜) {
        return {
          镜号: 镜.镜号, 场次: 镜.场次, 景别: 镜.景别, 运镜: 镜.运镜,
          画面: 镜.画面, 台词: 镜.台词, 时长: 镜.时长,
          视频状态: 镜.视频状态 || '待生成',
          生成方式: 镜.生成方式 || '', 生成提示词: 镜.生成提示词 || ''
        }
      })
      await 发('/api/分镜/保存', { 剧id: 页.剧id, 集号: 页.集号, 镜们: 镜们 })
      const 据 = await 取('/api/分镜/列表?剧id=' + 页.剧id + '&集号=' + 页.集号)
      页.镜列表 = (据 && 据.分镜们) || []
    },
    /* ---------- 提交 ---------- */
    当前槽位() {
      return {
        首帧: this.首帧url,
        尾帧: this.尾帧url,
        源视频: this.源视频url,
        参考图们: this.参考图们.slice(0, this.参考图上限),
        参考视频们: this.参考视频们.slice(0, 3),
        参考音频们: this.参考音频们.slice(0, 3),
        提示词: this.提示词,
        反向提示词: this.反向提示词
      }
    },
    async 提交任务() {
      const 页 = this
      const 镜 = 页.当前镜
      if (!镜.镜号) return
      const 槽 = 页.当前槽位()
      const 错 = 校验方式(页.方式键, 槽)
      if (错) { 页.$message.warning(错); return }
      页.提交中 = true
      try {
        const 参数 = 拼任务参数(页.方式键, 槽, {
          比例: 页.参数.比例, 一采MP: 页.参数.一采MP, 二采MP: 页.参数.二采MP,
          时长: 页.参数.时长, seed: 页.参数.seed, cfg: 页.参数.cfg,
          步数: 页.参数.步数, 采样器: 页.参数.采样器,
          生成声音: 页.参数.生成声音, 底膜精度: 页.底膜精度
        })
        const 据 = await 发('/api/任务/提交', 参数)
        const 任务id = (据 && 据.id) || 0
        /* 先落一版「生成中」（任务id 挂上，出片后回写），分镜状态同步 */
        await 发('/api/分镜/视频保存', {
          剧id: 页.剧id, 集号: 页.集号, 镜号: 镜.镜号, 动作: '添加',
          方式: 页.方式键, 提示词: 页.提示词, 任务id: 任务id
        })
        镜.视频状态 = '生成中'
        await 页.保存镜(true)
        await 页.刷版本们()
        页.$message.success('任务已提交（id=' + 任务id + '），出片后自动写回本镜')
        页.开监控()
      } catch (e) {
        页.$message.error('提交失败：' + ((e && e.message) || e))
      }
      页.提交中 = false
    },
    /* 连续生成：未完成的镜按各自推荐方式排队提交（每镜独立拼参数），不等结果 */
    async 连续生成() {
      const 页 = this
      const 待生成 = 页.镜列表.filter(function (x) { return x.视频状态 !== '已生成' && x.视频状态 !== '生成中' })
      if (!待生成.length) { 页.$message.success('没有待生成的镜'); return }
      页.批量中 = true
      let 排上 = 0
      for (let i = 0; i < 待生成.length; i++) {
        const 镜 = 待生成[i]
        try {
          const 命中 = 匹配资产(镜.画面, 页.资产行们)
          const 参考们 = 命中.map(function (行) {
            const 当前图 = (行.图们 || []).filter(function (g) { return g.状态 === '当前' })[0]
            return 当前图 ? 当前图.url : ''
          }).filter(function (u) { return u })
          /* 每镜各自推荐：镜上存过方式就沿用；否则按统一推荐规则
             （多资产=多参考生视频 / 单资产=参考生视频 / 兜底=文生视频），与列表页推荐标签同口径 */
          const 方式 = (镜.生成方式 && 方式表[镜.生成方式]) ? 镜.生成方式 : 推荐方式(镜, [], 命中.length, false)
          const 槽 = {
            首帧: '', 尾帧: '', 源视频: '',
            参考图们: 参考们,
            提示词: 镜.生成提示词 || 提示词草稿(镜),
            反向提示词: ''
          }
          const 错 = 校验方式(方式, 槽)
          if (错) continue
          const 参数 = 拼任务参数(方式, 槽, { 比例: 页.参数.比例, 一采MP: 页.参数.一采MP, 时长: 取镜秒(镜.时长, 5) })
          const 据 = await 发('/api/任务/提交', 参数)
          await 发('/api/分镜/视频保存', {
            剧id: 页.剧id, 集号: 页.集号, 镜号: 镜.镜号, 动作: '添加',
            方式: 方式, 提示词: 槽.提示词, 任务id: (据 && 据.id) || 0
          })
          镜.视频状态 = '生成中'
          镜.生成方式 = 方式
          镜.生成提示词 = 槽.提示词
          排上 += 1
        } catch (e) { /* 单镜失败不影响后面 */ }
      }
      try { await 页.存全部分镜() } catch (e) { /* 忽略 */ }
      await 页.刷版本们()
      页.批量中 = false
      页.$message.success('已排队 ' + 排上 + ' 镜，出片自动写回')
      页.开监控()
    },
    async 刷版本们() {
      const 页 = this
      const 据 = await 取('/api/分镜/视频?剧id=' + 页.剧id + '&集号=' + 页.集号)
      页.版本们 = (据 && 据.版本们) || []
    },
    /* ---------- 生成中监控：定时对账任务表并回写 ---------- */
    开监控() {
      const 页 = this
      if (页.监控定时器) return
      页.监控定时器 = setInterval(function () {
        if (document.hidden) return
        页.对账一轮()
      }, 8000)
      页.对账一轮()
    },
    async 对账一轮() {
      const 页 = this
      const 生成中数 = 页.版本们.filter(function (v) { return v.状态 === '生成中' }).length
      if (!生成中数) {
        if (页.监控定时器) { clearInterval(页.监控定时器); 页.监控定时器 = null }
        return
      }
      try {
        const 结果们 = await 对账生成中版本(页.版本们)
        if (!结果们.length) return
        let 变了 = false
        for (let i = 0; i < 结果们.length; i++) {
          const 项 = 结果们[i]
          await 落对账结果(页.剧id, 页.集号, 项.镜号, 项)
          const 镜 = 页.镜列表.filter(function (x) { return x.镜号 === 项.镜号 })[0]
          if (镜 && 项.状态 === '已生成') { 镜.视频状态 = '已生成'; 变了 = true }
          if (镜 && 项.状态 === '失败') { 镜.视频状态 = '待生成'; 变了 = true }
        }
        await 页.刷版本们()
        if (变了) {
          try { await 页.存全部分镜() } catch (e) { /* 忽略 */ }
          页.$message.success('有镜出片了，已写回')
        }
      } catch (e) { /* 下一轮再试 */ }
    },
    /* ---------- 版本 ---------- */
    async 设选中(版) {
      const 页 = this
      try {
        await 发('/api/分镜/视频保存', { 剧id: 页.剧id, 集号: 页.集号, 镜号: 版.镜号, 动作: '设选中', id: 版.id })
        await 页.刷版本们()
        页.$message.success('已设为正式使用 版#' + 版.id + '（成片取这版）')
      } catch (e) {
        页.$message.error('操作失败：' + ((e && e.message) || e))
      }
    },
    async 删版本(版) {
      const 页 = this
      try { await 页.$confirm('删除 版#' + 版.id + '？不可恢复。', '确认', { type: 'warning' }) } catch (e) { return }
      try {
        await 发('/api/分镜/视频保存', { 剧id: 页.剧id, 集号: 页.集号, 镜号: 版.镜号, 动作: '删除', id: 版.id })
        await 页.刷版本们()
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    }
  }
}
</script>

<style scoped>
.头卡 { padding: 14px 18px; margin-bottom: 12px; }
.头行 { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.镜徽 {
  padding: 2px 8px; border-radius: 6px; background: var(--主弱, rgba(64,158,255,.12));
  color: var(--主); font-family: Menlo, Consolas, monospace; font-size: 12px; font-weight: 700;
}
.镜题 { font-size: 13px; font-weight: 600; color: var(--字); }
.灰签 { font-size: 12px; color: var(--字弱); }
.态签 { font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--描边); color: var(--字次); }
.态签.生成中 { background: rgba(230,162,60,.15); color: #e6a23c; }
.态签.已成 { background: rgba(63,191,127,.14); color: var(--成功, #3fbf7f); }
.画面行 { margin-top: 8px; font-size: 12px; color: var(--字次); display: flex; gap: 8px; }
.画标 { flex: 0 0 auto; color: var(--字弱); }
.推签 { margin-left: 8px; font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--主弱, rgba(64,158,255,.12)); color: var(--主); }

.两列 { display: flex; gap: 14px; align-items: flex-start; }
.左列 { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.右列 { flex: 0 0 340px; display: flex; flex-direction: column; gap: 12px; }
.卡片 { padding: 14px 16px; }
.卡题 { font-size: 13px; font-weight: 600; color: var(--字); }
.卡题行 { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; gap: 8px; }

/* 方式卡 */
.方式行 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 10px; }
.方式卡 {
  border: 1px solid var(--描边); border-radius: 10px; padding: 10px 12px; cursor: pointer;
  background: var(--面板, transparent); transition: border-color .15s;
}
.方式卡:hover { border-color: var(--主); }
.方式卡.选中 { border-color: var(--主); background: var(--主弱, rgba(64,158,255,.08)); }
.式名 { font-size: 13px; font-weight: 600; color: var(--字); }
.式说 { margin-top: 4px; font-size: 11px; color: var(--字弱); line-height: 1.5; }
.更多行 { margin-top: 10px; display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--字弱); }
.组数 { font-size: 10px; color: var(--字弱); margin-left: 6px; font-weight: 400; }
/* 二级目录：导演台全能的六模式 */
.子方式行 { margin-top: 10px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.子题 { font-size: 12px; color: var(--字弱); }
.子方式 {
  border: 1px solid var(--描边); background: transparent; border-radius: 999px;
  font-size: 12px; color: var(--字次); padding: 3px 12px; cursor: pointer;
}
.子方式:hover { border-color: var(--主); }
.子方式.活 { border-color: var(--主); color: var(--主); background: var(--主弱, rgba(64,158,255,.1)); }
.子码 { font-size: 10px; color: var(--字弱); margin-left: 4px; font-family: Menlo, Consolas, monospace; }

/* 资源区 */
.资操作 { display: flex; gap: 8px; }
.资空 { font-size: 12px; color: var(--字弱); padding: 12px 0; text-align: center; }
.图网格 { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; }
.资图 { border: 1px solid var(--描边); border-radius: 8px; overflow: hidden; }
.资图.首帧 { border-color: var(--主); border-width: 2px; }
.资图.参考 { border-color: var(--成功, #3fbf7f); }
.资图图 { width: 100%; height: 84px; object-fit: contain; display: block; background: var(--面板弱, rgba(0,0,0,.03)); cursor: pointer; }
.资图注 { display: flex; align-items: center; gap: 4px; padding: 3px 6px; }
.标输入 { flex: 1 1 auto; min-width: 0; border: none; border-bottom: 1px dashed var(--描边); background: transparent; font-size: 11px; color: var(--字); padding: 2px 0; outline: none; }
.源签 { flex: 0 0 auto; font-size: 10px; color: var(--字弱); }
.资图钮 { display: flex; gap: 4px; padding: 4px 6px 6px; }
.微钮 {
  flex: 1 1 auto; border: 1px solid var(--描边); background: transparent; border-radius: 5px;
  font-size: 11px; color: var(--字次); cursor: pointer; padding: 2px 0;
}
.微钮.活 { border-color: var(--主); color: var(--主); background: var(--主弱, rgba(64,158,255,.1)); }
.微钮.删 { flex: 0 0 22px; color: #e24b4a; }
.AI图行 { margin-top: 10px; display: flex; gap: 8px; }
.AI图入 { flex: 1 1 auto; }
.源视频行 { margin-top: 10px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.源标 { font-size: 12px; color: var(--字次); }

/* 提示词 */
.扩写排 { display: flex; gap: 6px; margin-bottom: 8px; }
.扩技能 { flex: 0 0 170px; }
.扩需求 { flex: 1 1 auto; }
.引导区 { border: 1px dashed var(--描边); border-radius: 8px; padding: 10px; margin-bottom: 8px; }
.引导题 { font-size: 11px; color: var(--字弱); margin-bottom: 6px; }
.正入 { margin-top: 8px; }
.行间 { display: flex; align-items: center; gap: 8px; }
.行间.右 { justify-content: flex-end; }

/* 参数 */
.参行 { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-top: 8px; }
.参项 { display: flex; flex-direction: column; gap: 3px; font-size: 11px; color: var(--字弱); }
.高级区 { margin-top: 12px; border-top: 1px dashed var(--描边); padding-top: 8px; }
.高级题 { font-size: 12px; font-weight: 600; color: var(--字次); margin-bottom: 2px; }
.高级折 { margin-top: 8px; border: none; }
.高级折 >>> .el-collapse-item__header { font-size: 12px; color: var(--字弱); height: 34px; line-height: 34px; }
.提交行 { margin-top: 12px; display: flex; align-items: center; gap: 10px; }
.底膜行 { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 4px; }
.底膜说 { flex: 1 1 auto; font-size: 11px; color: var(--字弱); line-height: 1.7; }
.素材行 { margin-top: 8px; font-size: 12px; color: var(--字次); line-height: 1.6; }
.素标 { display: inline-block; margin-right: 8px; padding: 0 6px; border-radius: 4px; background: var(--描边); font-size: 11px; color: var(--字次); }
.帧行 { margin-top: 6px; font-size: 11px; color: var(--字弱); }
.种排 { display: flex; gap: 4px; align-items: center; }

/* 参考图提示 + 参考视频/音频槽 */
.资提示 { font-size: 11px; color: var(--字弱); line-height: 1.7; margin-bottom: 8px; }
.资提示 b { color: var(--字次); }
.媒行 { margin-top: 12px; border-top: 1px dashed var(--描边); padding-top: 10px; }
.媒题 { font-size: 12px; font-weight: 600; color: var(--字); margin-bottom: 6px; }
.媒操作 { display: flex; gap: 8px; align-items: center; }
.媒列 { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
.媒项 { width: 140px; border: 1px solid var(--描边); border-radius: 8px; overflow: hidden; }
.媒项.媒音 { width: 240px; }
.媒预 { width: 100%; height: 78px; object-fit: contain; display: block; background: #000; }
.媒音预 { width: 100%; height: 36px; display: block; }
.媒名 { display: flex; align-items: center; justify-content: space-between; padding: 2px 6px; font-size: 11px; color: var(--字次); }

/* 右列 */
.预览卡 { min-height: 240px; display: flex; align-items: center; justify-content: center; }
.预览视频 { width: 100%; max-height: 420px; border-radius: 8px; background: #000; }
.预览空 { text-align: center; color: var(--字弱); font-size: 13px; padding: 40px 0; }
.预览空 i { font-size: 40px; display: block; margin-bottom: 8px; }
/* 本镜生成视频（全宽铺在下方） */
.版卡 { margin-top: 14px; }
.版网格 { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.版块 { border: 1px solid var(--描边); border-radius: 10px; overflow: hidden; }
.版块.正式 { border-color: var(--成功, #3fbf7f); border-width: 2px; }
.版视频 { width: 100%; height: 150px; object-fit: contain; display: block; background: #000; }
.版生成中 { height: 150px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #e6a23c; background: rgba(230,162,60,.08); }
.版脚 { display: flex; align-items: center; gap: 6px; padding: 6px 8px; flex-wrap: wrap; }
.版式 { font-size: 12px; color: var(--字); font-weight: 600; }
.版时 { font-size: 11px; color: var(--字弱); }
.微钮.主 { border-color: var(--成功, #3fbf7f); color: var(--成功, #3fbf7f); }
.选签 { margin-left: 6px; font-size: 10px; padding: 0 6px; border-radius: 999px; background: rgba(63,191,127,.14); color: var(--成功, #3fbf7f); }
.败签 { margin-left: 6px; font-size: 10px; padding: 0 6px; border-radius: 999px; background: rgba(226,75,74,.12); color: #e24b4a; }

/* 镜条 */
.镜条 { display: flex; gap: 6px; flex-wrap: wrap; }
.镜块 {
  flex: 0 0 56px; border: 1px solid var(--描边); border-radius: 8px; padding: 6px 0;
  text-align: center; cursor: pointer;
}
.镜块.活 { border-color: var(--主); background: var(--主弱, rgba(64,158,255,.08)); }
.镜块号 { font-size: 11px; font-family: Menlo, Consolas, monospace; color: var(--字); }
.镜块态 { font-size: 11px; color: var(--字弱); margin-top: 2px; min-height: 14px; }
.镜块态.已成 { color: var(--成功, #3fbf7f); }
.镜块态.生成中 { color: #e6a23c; }

/* 底条 */
.底条 { margin-top: 14px; display: flex; align-items: center; justify-content: space-between; }
.底题 { font-size: 14px; font-weight: 600; color: var(--主); }

/* 资产引入弹窗的 .资窗* 样式与 .资窗弹窗 色板块已随弹窗拆到 导演台资产窗弹窗.vue */

@media (max-width: 1100px) {
  .两列 { flex-direction: column; }
  .右列 { flex: 1 1 auto; width: 100%; }
  .方式行 { grid-template-columns: repeat(2, 1fr); }
}
</style>
