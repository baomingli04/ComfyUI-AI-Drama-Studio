<template>
  <div class="创作模块">
    <div class="剧集布局">
      <ep-rail
        当前="美术资产"
        :剧名="剧名" :剧id="剧id" :集="集号" :标题="集标题" />

      <div class="剧集主体">
        <!-- 面包屑 -->
        <div class="面包屑条">
          <span class="可点" @click="$router.push('/video')">视频生成</span>
          <span> / </span>
          <span class="可点" @click="$router.push({ path: '/video/episode', query: $route.query })">{{ 剧名 }} 第 {{ 集号 }} 集</span>
          <span> / </span>
          <span style="color:var(--字次)">美术资产</span>
        </div>

        <!-- 载入/报错门控 -->
        <div v-if="载入中" class="卡片 状态卡"><i class="el-icon-loading"></i> 正在读取美术资产…</div>
        <div v-else-if="载入报错" class="卡片 状态卡 败">{{ 载入报错 }}
          <el-button size="mini" style="margin-left:10px" @click="载入()">重试</el-button>
        </div>

        <template v-else>
          <!-- 页头：四分区统计 + 风格/画幅 + 模型选择 -->
          <div class="卡片 头卡">
            <div class="头行">
              <div>
                <div class="头题">美术资产 · 全剧 {{ 组们.length }} 项</div>
                <div class="分区签行">
                  <span v-for="区 in 分区表" :key="区.键" class="分区签"
                        :class="{ 活: 激活分区 === 区.键 }" @click="激活分区 = 区.键">
                    {{ 区.名 }} ({{ 统计[区.键] || 0 }})
                  </span>
                  <span class="分区签 加签" @click="打开新增()">＋ 新增</span>
                </div>
              </div>
              <div style="flex:1"></div>
              <div class="设定块">
                <div class="设定行"><span class="设键">画幅</span><span>{{ 设定.画幅 }}</span>
                  <el-select v-model="设定.画幅" size="mini" class="设选" @change="存设定('画幅')">
                    <el-option v-for="v in ['9:16', '16:9', '1:1', '4:3']" :key="v" :label="v" :value="v" />
                  </el-select>
                </div>
                <div class="设定行"><span class="设键">分辨率</span>
                  <el-select v-model="设定.分辨率" size="mini" class="设选" @change="存设定('分辨率')">
                    <el-option v-for="v in ['480p', '720p', '1080p']" :key="v" :label="v" :value="v" />
                  </el-select>
                </div>
                <div class="设定行"><span class="设键">全局风格</span>
                  <el-input v-model="设定.全局风格" size="mini" class="设选 宽" placeholder="如 校园青春日系胶片风" @change="存设定('全局风格')" />
                </div>
              </div>
            </div>
            <div class="提示行">
              <b>一张当前参考图 = 一张卡片</b>；AI 编辑/重新生成会<b>新增一张卡片</b>（原图保留，不要可逐卡删除）；每张图有自己的提示词（上传后自动解析，点图片下方文字可改）；「管理」里可按形态分组、上传多图、查看/恢复历史。
            </div>
          </div>

          <!-- 分区卡流：一张当前参考图 = 一张卡片；没图的资产出一张占位卡 -->
          <div class="卡流">
            <div v-for="卡 in 卡片们" :key="卡.图 ? ('k' + 卡.图.id) : ('g' + 卡.组.键)"
                 class="卡片 资卡" :class="{ 人物卡: 卡.组.类型 === '人物' }">
              <!-- 卡头 -->
              <div class="资头">
                <div class="资名">{{ 卡.组.名称 }}</div>
                <span class="类签">{{ 卡.组.类型 }}</span>
                <span v-if="卡.组.性别" class="性签">{{ 卡.组.性别 }}</span>
                <span v-if="卡.图 && (卡.图.标注 || 卡.图.形态)" class="性签">{{ 卡.图.标注 || 卡.图.形态 }}</span>
                <span v-if="卡.图" class="集签">E{{ 卡.图.集号 }}</span>
                <span v-else-if="卡.组.集们.length" class="集签">E{{ 卡.组.集们.join('、E') }}</span>
                <div style="flex:1"></div>
                <button v-if="卡.组.历史图们.length" class="小钮" @click.stop="打开图窗(卡.组, true)">历史 {{ 卡.组.历史图们.length }}</button>
                <button v-if="卡.图" class="小钮 删钮" @click.stop="删卡图(卡)">删</button>
                <button v-else class="小钮 删钮" @click.stop="删资产(卡.组)">删资产</button>
              </div>

              <!-- 图片（点开预览）/ 占位（点开图窗上传） -->
              <div v-if="卡.图" class="大图行">
                <img class="大图" :src="媒体地址(卡.图.url)" :alt="卡.图.标注" @click="预览图 = 卡.图" />
              </div>
              <div v-else class="缩略行" @click="打开图窗(卡.组)">
                <div class="缩略块 占位">
                  <i class="el-icon-picture-outline"></i>
                  <span>点击上传或生成参考图</span>
                </div>
              </div>

              <!-- 图片提示词（该图自己的提示词/解析词，点击编辑） -->
              <div v-if="卡.图" class="约行 保 词行" @click="打开图提示词(卡.图, 卡.组)"
                   :title="卡.图.提示词 || '点击解析或填写'">
                <template v-if="卡.图.提示词">图片提示词：{{ 卡.图.提示词 }}</template>
                <template v-else>（暂无图片提示词，点此解析或填写）</template>
              </div>

              <!-- 人物：关联角色 + 把图片提示词同步进角色档案（多套外形按【形态】分段存） -->
              <div v-if="卡.组.类型 === '人物' && 卡.图" class="关行">
                <span class="关标">关联角色</span>
                <el-select :value="卡.图.关联人物 || 关联默认(卡.组)" size="mini" clearable filterable
                           placeholder="选角色（默认按资产匹配）" class="关选" @change="改关联(卡, $event)">
                  <el-option v-for="人 in 人物选项们" :key="人.人物id" :label="人.名" :value="人.人物id" />
                </el-select>
                <button class="小钮" :disabled="同步中id === 卡.图.id" @click.stop="同步外形(卡)">
                  {{ 同步中id === 卡.图.id ? '同步中…' : '同步外形到角色' }}
                </button>
              </div>
              <template v-else>
                <div v-if="卡.组.必须保持" class="约行 保">必须保持：{{ 卡.组.必须保持 }}</div>
                <div v-if="卡.组.禁止出现" class="约行 禁">禁止出现：{{ 卡.组.禁止出现 }}</div>
              </template>

              <!-- 人物：音色区（只在资产首卡显示，避免多图卡重复） -->
              <div v-if="卡.组.类型 === '人物' && 卡.首卡" class="音区">
                <div class="音头">
                  <span class="音标">音色</span>
                  <span class="态签" :class="{ 待: 卡.组.音色状态 !== '已生成' }">{{ 卡.组.音色状态 }}</span>
                  <span v-if="卡.组.音色名" class="音名签" :title="'点击试听'" @click.stop="试听(卡.组)"><i class="el-icon-mic"></i> {{ 卡.组.音色名 }}</span>
                  <div style="flex:1"></div>
                  <button v-if="卡.组.音色url" class="小钮 主" @click.stop="试听(卡.组)"><i class="el-icon-video-play"></i> 试听</button>
                </div>
                <div class="音提示">音色提示词</div>
                <div class="音文">{{ 卡.组.音色提示词 || '（未填写）' }}</div>
                <div class="音操作">
                  <button class="小钮 主" @click.stop="打开音库(卡.组)"><i class="el-icon-headset"></i> 选择音色</button>
                  <button class="小钮" @click.stop="编辑音色(卡.组)">编辑提示词</button>
                  <el-upload action="#" :show-file-list="false" accept="audio/*" :http-request="(o) => 上传音色文件(o, 卡.组)">
                    <button class="小钮" :disabled="上传中">上传音色</button>
                  </el-upload>
                </div>
              </div>

              <!-- 操作行 -->
              <div class="出图行">
                <template v-if="卡.图">
                  <el-upload action="#" :show-file-list="false" accept="image/*" :http-request="(o) => 上传参考图(o, 卡.组, 卡.图)">
                    <button class="小钮" :disabled="上传中">{{ 上传中 ? '上传中…' : '上传图片' }}</button>
                  </el-upload>
                  <button class="小钮" :disabled="解析中id === 卡.图.id" @click.stop="解析图提示词(卡.图, 卡.组)">
                    {{ 解析中id === 卡.图.id ? '解析中…' : '解析提示词' }}
                  </button>
                  <button class="小钮 主" @click.stop="打开AI编辑(卡.图, 卡.图.提示词, 卡.组)">AI编辑</button>
                  <button class="小钮" :disabled="卡.组.生图中" @click.stop="重新生成图(卡.组, 卡.图)">
                    {{ 卡.组.生图中 ? '生成中…' : '重新生成' }}
                  </button>
                  <button class="小钮" @click.stop="打开图窗(卡.组)">管理</button>
                </template>
                <template v-else>
                  <el-upload action="#" :show-file-list="false" accept="image/*" :http-request="(o) => 上传参考图(o, 卡.组)">
                    <button class="小钮 主">上传图片</button>
                  </el-upload>
                  <button class="小钮" @click.stop="编辑提示词(卡.组)">编辑提示词</button>
                  <button class="小钮" @click.stop="打开图窗(卡.组)">管理参考图</button>
                </template>
              </div>
            </div>
          </div>

          <div v-if="!卡片们.length" class="卡片 状态卡">
            该分区暂无资产。先到 <span class="可点 主色" @click="去资产()">资产清单</span> 提取本集资产。
          </div>

          <!-- 底部统计 + 导航 -->
          <div class="卡片 统计条">
            <span>已生成图 <b>{{ 当前图总数 }}</b> 张</span>
            <span class="分隔">·</span>
            <span>历史图 <b>{{ 历史图总数 }}</b> 张</span>
            <div style="flex:1"></div>
            <el-button size="small" @click="上一步()">上一步：资产清单</el-button>
            <el-button size="small" type="primary" @click="下一步()">下一步：拆分分镜<i class="el-icon-arrow-right"></i></el-button>
          </div>
        </template>
      </div>
    </div>

    <!-- 参考图弹窗（已拆分为独立组件 美术资产参考图弹窗.vue；图窗显/图窗组/上传形态与业务方法留在本组件，操作经事件回传） -->
    <art-ref-dialog :visible.sync="图窗显" :组="图窗组" :上传中="上传中" :解析中id="解析中id"
                    :上传形态.sync="上传形态"
                    @预览="预览图 = $event" @上传="上传参考图" @改字段="改图字段"
                    @打开提示词="打开图提示词" @解析="解析图提示词" @AI编辑="打开AI编辑" @图操作="图操作" />

    <!-- 图片预览（已拆分为独立组件 美术资产预览弹窗.vue；预览图/预览窗显留在本组件） -->
    <art-preview-dialog :visible.sync="预览窗显" :图="预览图" />

    <!-- 新增美术资产弹窗（全剧共用，不挂集；已拆分为独立组件 美术资产新增弹窗.vue；新增缓冲/保存新增留在本组件） -->
    <art-create-dialog :visible.sync="新增窗显" :缓冲="新增缓冲" :分区表="分区表" :新增中="新增中" @保存="保存新增" />

    <!-- 单图提示词编辑（已拆分为独立组件 美术资产单图提示词弹窗.vue；编辑图/编辑图组/存图提示词留在本组件） -->
    <art-image-prompt-dialog :visible.sync="图提示词窗显" :编辑图="编辑图" :图存中="图存中" @保存="存图提示词" />

    <!-- 单图 AI 编辑（表单与 /test 三图编辑一致版页同款：图1/图2/图3 图位 + 正向提示词；图1 默认当前图） -->
    <el-dialog :visible.sync="AI编辑窗显" :title="AI编辑 ? 'AI 编辑图片' : ''" width="680px" append-to-body>
      <template v-if="AI编辑">
        <div class="表单块"><div class="表单标">编辑任务类型</div>
          <el-radio-group v-model="AI编辑.任务类型" @change="切任务类型">
            <el-radio label="三图编辑一致版">三图编辑一致版（T4）</el-radio>
            <el-radio label="多图编辑多人合并版">多图编辑·多人合并版（T5）</el-radio>
            <el-radio label="动漫转真人">动漫转真人（T5b）</el-radio>
          </el-radio-group>
          <div class="类型注">{{ 任务类型注 }}</div>
        </div>

        <div class="图位行">
          <div class="图位" v-for="n in [1, 2, 3]" :key="'slot' + n">
            <div class="图位题">图{{ n }}<span class="图位说">{{ 图位说明(n) }}</span></div>
            <div class="图位框">
              <img v-if="AI编辑['图' + n]" class="图位图" :src="媒体地址(AI编辑['图' + n])"
                   @click="选择目标 = '图' + n" />
              <div v-else class="图位空" @click="选择目标 = '图' + n"><i class="el-icon-plus"></i></div>
            </div>
            <div class="图位操作">
              <button class="小钮" @click="选参考图('图' + n)">从参考图选</button>
              <el-upload action="#" :show-file-list="false" accept="image/*" :http-request="(o) => 上传编辑图('图' + n, o)">
                <button class="小钮">上传</button>
              </el-upload>
              <button v-if="AI编辑['图' + n] && n > 1" class="小钮 删钮" @click="AI编辑['图' + n] = ''">清</button>
            </div>
          </div>
        </div>

        <!-- 选图条：点某个图位的「从参考图选」后出现，点缩略图即赋给该图位 -->
        <div class="选图条" v-if="选择目标">
          <div class="选图题">点击一张已有图片设为 {{ 选择目标 }}（本资产当前图在前，其后历史图，最后是其他资产的图；也可用图位下的「上传」传新图）
            <span class="可点 取选" @click="选择目标 = ''">取消</span></div>
          <div class="选图行">
            <div v-for="图 in AI编辑图们" :key="'p' + 图.id" class="选图块" @click="挑图(图)">
              <img class="选图图" :src="媒体地址(图.url)" />
              <div class="选图标">{{ 图.来源组 }} · {{ 图.标注 || 图.形态 || '参考图' }}</div>
            </div>
            <div v-if="!AI编辑图们.length" class="窗空">全剧还没有参考图，请用图位下的「上传」传一张</div>
          </div>
        </div>

        <!-- AI 扩写：选技能把需求扩成完整提示词；引导词按「页面×技能」存库 -->
        <div class="表单块">
          <div class="表单标">AI 扩写（选一个技能，把简短需求扩写成完整正向提示词）</div>
          <div class="扩写排">
            <el-select v-model="AI编辑.技能id" size="small" class="扩技能" placeholder="提示词技能"
                       @change="切扩写技能($event)">
              <el-option v-for="s in 图扩技能们" :key="s.id" :label="s.名称 + (s.分类名称 ? '（' + s.分类名称 + '）' : '')" :value="s.id" />
            </el-select>
            <el-input v-model="AI编辑.需求" size="small" class="扩需求"
                      placeholder="写需求：想要什么画面/效果，简短描述" @keyup.enter.native="AI扩写()" />
            <el-button size="small" type="primary" plain :loading="扩写中" @click="AI扩写()">AI扩写</el-button>
            <el-button size="small" @click="引导词显 = !引导词显">{{ 引导词显 ? '收起引导词' : '引导词设置' }}</el-button>
          </div>
          <div v-if="引导词显" class="引导区">
            <div class="引导题">{{ AI编辑.任务类型 || '三图编辑一致版' }} · 生成:/video/art:{{ AI编辑.任务类型 || '三图编辑一致版' }}:{{ AI编辑.技能id || '未选技能' }} —— 这些规则会原样附加到本次扩写的系统提示词里，按「任务类型×技能」各存一份，三种编辑任务互不混用。</div>
            <el-input v-model="引导词文本" type="textarea" :rows="8" placeholder="每行一条规则" />
            <div class="引导钮行">
              <button class="小钮" @click="引导词显 = false">取消</button>
              <button class="小钮 主" :disabled="引导词存中" @click="存引导词()">{{ 引导词存中 ? '保存中…' : '保存' }}</button>
            </div>
          </div>
        </div>

        <div class="表单块"><div class="表单标">正向提示词（编辑指令，默认带出该图自己的提示词）</div>
          <el-input type="textarea" :rows="4" v-model="AI编辑.正向"
                    placeholder="例如：保持人物长相一致，换上雨天校服，光线偏冷" /></div>
        <div class="表单块 新增注">任务完成后产物新增一张参考图卡片，原图保留（不要可删卡）。</div>
      </template>
      <div slot="footer">
        <el-button size="small" @click="AI编辑窗显 = false">取消</el-button>
        <el-button size="small" type="primary" :loading="编辑任务中" @click="提交AI编辑()">
          {{ 编辑任务中 ? '任务执行中…' : '提交任务' }}</el-button>
      </div>
    </el-dialog>

    <!-- 编辑出图提示词（已拆分为独立组件 美术资产出图提示词弹窗.vue；编辑组/存提示词留在本组件） -->
    <art-set-prompt-dialog :visible.sync="提示词窗显" :编辑组="编辑组" :存中="存中" @保存="存提示词" />

    <!-- 编辑音色 -->
    <el-dialog :visible.sync="音色窗显" :title="编辑组 ? '音色 · ' + 编辑组.名称 : ''" width="560px" append-to-body>
      <template v-if="编辑组">
        <div class="表单块"><div class="表单标">音色提示词</div>
          <el-input type="textarea" :rows="3" v-model="编辑组.音色提示词"
                    placeholder="格式：男，青年，自然 · 22 岁，木叶忍者学校三班新任班主任" /></div>
        <div class="表单块" v-if="编辑组.音色url"><div class="表单标">当前音色文件</div>
          <audio :src="音色播放地址(编辑组.音色url)" controls style="width:100%" /></div>
        <div class="表单块">
          <div class="表单标">AI 合成音色（Edge-TTS · 联网调用微软免费接口）</div>
          <div class="行间" style="gap:8px;flex-wrap:wrap">
            <el-select v-model="合成音色名" size="small" style="width:210px" :disabled="音色合成中">
              <el-option v-for="音 in 音色合成选项" :key="音.值" :label="音.标" :value="音.值" />
            </el-select>
          </div>
          <el-input type="textarea" :rows="2" v-model="合成文本" placeholder="要合成的台词文本（默认取音色提示词）"
                    style="margin-top:8px" :disabled="音色合成中" />
          <div class="行间" style="margin-top:8px;gap:8px">
            <el-button size="small" type="primary" :loading="音色合成中" @click="AI合成音色()">
              {{ 音色合成中 ? '合成中…' : '合成并填入' }}
            </el-button>
            <span v-if="音色合成中" style="font-size:12px;color:var(--字弱)">合成任务后台执行中，完成后自动填入下方音色文件</span>
          </div>
        </div>
        <el-upload action="#" :show-file-list="false" accept="audio/*" :http-request="上传音色文件">
          <el-button size="small" icon="el-icon-upload2" :loading="上传中">上传音色文件</el-button>
        </el-upload>
      </template>
      <div slot="footer">
        <el-button size="small" @click="音色窗显 = false">取消</el-button>
        <el-button size="small" type="primary" :loading="存中" @click="存音色()">保存</el-button>
      </div>
    </el-dialog>

    <!-- 音色库选择（数据与 /voices 音色库页同源） -->
    <el-dialog :visible.sync="音库窗显" :title="音库组 ? '选择音色 · ' + 音库组.名称 : '选择音色'" width="620px" append-to-body @closed="停库音色()">
      <div class="音库过滤">
        <span v-for="类 in ['全部', '男声', '女声']" :key="类" class="音库签"
              :class="{ 活: 音库分类 === 类 }" @click="音库分类 = 类">{{ 类 }}</span>
        <el-input v-model="音库词" placeholder="搜索音色..." prefix-icon="el-icon-search" size="small" style="width:180px" clearable />
      </div>
      <div class="音库列表">
        <div v-for="音 in 音库过滤后" :key="音.id" class="音库行"
             :class="{ 选中: 音库组 && 音库组.音色名 === 音.名 }" @click="播库音色(音)">
          <i :class="库正在播id === 音.id ? 'el-icon-video-pause' : 'el-icon-video-play'" class="音库播"></i>
          <div class="音库信">
            <div class="音库名">{{ 音.名 }}
              <span class="音库别">{{ 音.性别 }} · {{ 音.年龄段 }} · {{ 音.风格 }}</span>
            </div>
            <div class="音库说">{{ 音.说明 }}</div>
          </div>
          <button class="小钮 主" @click.stop="选用库音色(音)">使用</button>
        </div>
        <div v-if="!音库过滤后.length" class="音库空">没有匹配的音色</div>
      </div>
      <audio ref="库音频" :src="库播文件" preload="metadata" @ended="库正在播id = null" style="display:none"></audio>
    </el-dialog>
  </div>
</template>

<script>
import 剧集侧栏 from '@/共用/剧集侧栏/index.vue'
import { 取, 发, 基础地址, 取令牌 } from '@/接口/请求'
import { 媒体地址 } from '@/接口/媒体'
import { 提交图片任务 } from '@/共用/图片任务'
import { 读引导, 存配置, 读技能id, 记技能id, 适配技能id } from '@/共用/技能生成配置'
import { 默认扩写规则 } from '@/共用/扩写行'
import { 音色列表 } from '@/views/共用/假数据'
import 美术资产预览弹窗 from './美术资产预览弹窗.vue'
import 美术资产参考图弹窗 from './美术资产参考图弹窗.vue'
import 美术资产新增弹窗 from './美术资产新增弹窗.vue'
import 美术资产单图提示词弹窗 from './美术资产单图提示词弹窗.vue'
import 美术资产出图提示词弹窗 from './美术资产出图提示词弹窗.vue'

/* 类型分区（固定顺序，未出现的类型也显示 0） */
const 分区表 = [
  { 键: '人物', 名: '人物' },
  { 键: '场景', 名: '场景' },
  { 键: '道具', 名: '道具' },
  { 键: '服装', 名: '服装' }
]

/* 解析引导词按 分类 各一套：图上选了分类用图的，没选用资产类型（选哪个用哪个） */
const 分类解析要求 = {
  人物: '解析这张人物参考图，严格按三行输出，每行格式「字段：内容」：外貌：发型发色/五官/肤色/面部特征；身材：体型体格；穿搭：服装/发饰/配饰。不要解释，不要输出其他内容',
  场景: '解析这张场景参考图，输出一段可直接用于重新生成同类场景图的中文出图提示词：写清场景类型与空间布局（前景/中景/背景）、建筑与陈设细节、时间与光线、天气与氛围、画面风格，不要解释，只输出提示词本身',
  道具: '解析这张道具参考图，输出一段可直接用于重新生成同类道具图的中文出图提示词：写清物件名称与外观形状、材质与颜色、表面细节与新旧状态、摆放角度与背景、画面风格，不要解释，只输出提示词本身',
  服装: '解析这张服装参考图，输出一段可直接用于重新生成同类服装图的中文出图提示词：写清服装款式与结构、颜色与材质、纹样与配饰、穿着方式与整体造型，不要解释，只输出提示词本身'
}

export default {
  name: 'ArtAssets',
  components: {
    'ep-rail': 剧集侧栏,
    /* 弹窗子组件统一用 ASCII 别名注册（本项目约定：自定义标签用 ASCII 名） */
    'art-preview-dialog': 美术资产预览弹窗,
    'art-ref-dialog': 美术资产参考图弹窗,
    'art-create-dialog': 美术资产新增弹窗,
    'art-image-prompt-dialog': 美术资产单图提示词弹窗,
    'art-set-prompt-dialog': 美术资产出图提示词弹窗
  },
  data() {
    return {
      载入中: true,
      载入报错: '',
      行们: [],          // 美术列表接口原始行（每集每资产一行）
      人物选项们: [],    // 人物档案列表（人物卡「关联角色」下拉）
      激活分区: '人物',
      分区表: 分区表,
      设定: { 画幅: '9:16', 分辨率: '480p', 全局风格: '' },
      /* 弹窗态 */
      图窗显: false,
      图窗组: null,
      只看历史: false,
      预览图: null,
      提示词窗显: false,
      音色窗显: false,
      编辑组: null,
      /* 音色库选择弹窗（/voices 同源数据） */
      音库窗显: false,
      音库组: null,
      音库分类: '全部',
      音库词: '',
      库正在播id: null,
      库播文件: '',
      存中: false,
      上传中: false,
      /* AI 合成音色（Edge-TTS，2026-11-04 新增） */
      音色合成中: false,
      音色轮询器: null,
      合成音色名: 'zh-CN-XiaoxiaoNeural',
      合成文本: '',
      音色合成选项: [
        { 值: 'zh-CN-XiaoxiaoNeural', 标: '晓晓 · 女声' },
        { 值: 'zh-CN-XiaoyiNeural', 标: '晓伊 · 女声' },
        { 值: 'zh-CN-YunjianNeural', 标: '云健 · 男声' },
        { 值: 'zh-CN-YunxiNeural', 标: '云希 · 男声' },
        { 值: 'zh-CN-YunxiaNeural', 标: '云夏 · 少年' },
        { 值: 'zh-CN-YunyangNeural', 标: '云扬 · 男声·播音' },
        { 值: 'zh-CN-liaoning-XiaobeiNeural', 标: '晓北 · 女声·东北' },
        { 值: 'zh-CN-shaanxi-XiaoniNeural', 标: '晓妮 · 女声·陕西' }
      ],
      /* ＋新增（全剧共用，集号=0） */
      新增窗显: false,
      新增缓冲: null,
      新增中: false,
      /* 图窗：形态/解析/单图提示词 */
      上传形态: '',
      解析中id: null,
      编辑图: null,
      编辑图组: null,
      图提示词窗显: false,
      图存中: false,
      /* 人物卡关联角色/同步外形 */
      同步中id: null,
      /* 单图 AI 编辑（T4 三图一致版 / T5 多人合并版 / T5b 动漫转真人） */
      AI编辑窗显: false,
      AI编辑: null,
      编辑任务中: false,
      选择目标: '',
      /* AI 编辑里的扩写：技能（图片提示词扩写分类）+ 引导词（按 页面×技能 存库） */
      图扩技能们: [],
      图扩技能id: '',
      扩写中: false,
      引导词显: false,
      引导词文本: '',
      引导词存中: false
    }
  },
  computed: {
    剧名() { return this.$route.query.name || '' },
    剧id() { return parseInt(this.$route.query.ep) || 0 },
    集号() { return parseInt(this.$route.query.集) || 1 },
    集标题() { return this.$route.query.标题 || '' },
    /* 按 资产id 聚合跨集行：同一资产各集合并为一张卡，图共同显示 */
    组们() {
      const 映射 = {}
      const 顺序 = []
      for (let i = 0; i < this.行们.length; i++) {
        const 行 = this.行们[i]
        const 键 = 行.资产id || ('行' + 行.资产行id)
        if (!映射[键]) {
          映射[键] = {
            键: 键,
            资产id: 行.资产id,
            类型: 行.类型,
            名称: 行.名称,
            性别: '',
            集们: [],
            主行: 行,          // 定装字段来源（集号最大那行）
            图们: []           // 各集全部图合并，带 集号
          }
          顺序.push(键)
        }
        const 组 = 映射[键]
        if (组.集们.indexOf(行.集号) < 0) 组.集们.push(行.集号)
        if (行.集号 > 组.主行.集号) 组.主行 = 行
        for (let j = 0; j < (行.图们 || []).length; j++) {
          const 图 = Object.assign({}, 行.图们[j], { 集号: 行.集号 })
          组.图们.push(图)
        }
      }
      const 组们 = 顺序.map(键 => {
        const 组 = 映射[键]
        const 定 = 组.主行.定装 || {}
        组.定装id = 定.id || null
        组.生图状态 = 定.生图状态 || '待生成'
        组.音色状态 = 定.音色状态 || '待生成'
        组.生图提示词 = 定.生图提示词 || ''
        组.必须保持 = 定.必须保持 || ''
        组.禁止出现 = 定.禁止出现 || ''
        组.音色提示词 = 定.音色提示词 || ''
        组.音色名 = 定.音色名 || ''
        组.音色url = 定.音色url || ''
        组.当前图们 = 组.图们.filter(图 => 图.状态 === '当前')
        组.历史图们 = 组.图们.filter(图 => 图.状态 === '历史')
        组.生图中 = false
        return 组
      })
      return 组们
    },
    统计() {
      const 计 = { 人物: 0, 场景: 0, 道具: 0, 服装: 0 }
      for (const 组 of this.组们) if (计[组.类型] !== undefined) 计[组.类型]++
      return 计
    },
    /* 一图一卡：每个当前参考图一张卡；没有当前图的资产出一张占位卡；首卡承载音色区 */
    卡片们() {
      const 区 = this.激活分区
      const 卡们 = []
      for (const 组 of this.组们) {
        if (组.类型 !== 区) continue
        if (组.当前图们.length) {
          for (let i = 0; i < 组.当前图们.length; i++) {
            卡们.push({ 组: 组, 图: 组.当前图们[i], 首卡: i === 0 })
          }
        } else {
          卡们.push({ 组: 组, 图: null, 首卡: true })
        }
      }
      return 卡们
    },
    当前图总数() {
      return this.组们.reduce((和, 组) => 和 + 组.当前图们.length, 0)
    },
    历史图总数() {
      return this.组们.reduce((和, 组) => 和 + 组.历史图们.length, 0)
    },
    预览窗显: {
      get() { return !!this.预览图 },
      set(值) { if (!值) this.预览图 = null }
    },
    /* 图窗的 形态选项们/图窗形态组们 两个计算属性已随参考图弹窗拆入 美术资产参考图弹窗.vue */
    /* AI 编辑弹窗：所属资产组（按组键从最新 组们 解析，重拉后仍指向新对象） */
    AI编辑组() {
      if (!this.AI编辑) return null
      return this.组们.find(组 => 组.键 === this.AI编辑.组键) || this.图窗组 || null
    },
    /* 音色库弹窗：按性别分类 + 关键词过滤（与 /voices 页同规则） */
    音库过滤后() {
      const 词 = this.音库词.trim()
      return 音色列表.filter(音 => {
        const 性别匹配 = this.音库分类 === '全部'
          || (this.音库分类 === '男声' && 音.性别 === '男')
          || (this.音库分类 === '女声' && 音.性别 === '女')
        const 词匹配 = !词 || 音.名.indexOf(词) >= 0 || (音.说明 || '').indexOf(词) >= 0
        return 性别匹配 && 词匹配
      })
    },
    /* AI 编辑弹窗：可选图 = 本资产当前图 + 本资产历史图 + 全剧其他资产的当前图（多人合并要能选别人的图） */
    AI编辑图们() {
      const 主组 = this.AI编辑组
      if (!主组) return []
      const 们 = []
      for (const 图 of 主组.当前图们) 们.push(Object.assign({}, 图, { 来源组: 主组.名称 }))
      for (const 图 of 主组.历史图们) 们.push(Object.assign({}, 图, { 来源组: 主组.名称 + '·历史' }))
      for (const 组 of this.组们) {
        if (组.键 === 主组.键) continue
        for (const 图 of 组.当前图们) 们.push(Object.assign({}, 图, { 来源组: 组.名称 }))
      }
      return 们
    },
    /* AI 编辑：当前任务类型的说明（区分三图一致版 / 多人合并版 / 动漫转真人） */
    任务类型注() {
      const t = this.AI编辑 && this.AI编辑.任务类型
      if (t === '多图编辑多人合并版') {
        return '多人合并：把图2/图3里的角色或元素合并进图1的画面。图1（主体）必填，图2/图3 至少再选/传一张。'
      }
      if (t === '动漫转真人') {
        return '风格转换：只使用图1，把动漫/插画风格的图转成真人质感。图2/图3 不参与本任务。'
      }
      return '一致性编辑：以图1为主图进行编辑改图，图2/图3 作为长相/风格一致性参考（都可选，只有图1也能跑）。'
    }
  },
  watch: {
    '$route.query.ep'() { this.载入() }
  },
  created() {
    this.载入()
    this.拉图扩技能()
  },
  beforeDestroy() {
    this.停音色轮询()
  },
  methods: {
    媒体地址,
    async 载入() {
      const 页 = this
      if (!页.剧id) {
        页.载入报错 = '缺少剧 id'
        页.载入中 = false
        return
      }
      页.载入中 = true
      页.载入报错 = ''
      try {
        let 数据 = await 取('/api/美术/列表?剧id=' + 页.剧id)
        页.行们 = (数据 && 数据.行们) || []
        页.回显设定()
        /* 人物档案列表：人物卡「关联角色」下拉用（拉失败不阻塞页面） */
        if (!页.人物选项们.length) {
          取('/api/人物/列表?剧id=' + 页.剧id)
            .then(function (人数据) { 页.人物选项们 = (人数据 && 人数据.人物们) || [] })
            .catch(function () { /* 忽略 */ })
        }
        /* 有资产但全没定装行 → 首次进入自动初始化（幂等） */
        const 缺定装 = 页.行们.length && 页.行们.every(行 => !行.定装)
        if (缺定装) {
          await 发('/api/美术/初始化', { 剧id: 页.剧id })
          数据 = await 取('/api/美术/列表?剧id=' + 页.剧id)
          页.行们 = (数据 && 数据.行们) || []
          页.回显设定()
        }
      } catch (e) {
        页.载入报错 = '美术资产读取失败：' + ((e && e.message) || e)
      }
      页.载入中 = false
    },
    /* 头部设定从任一定装行回显（各行一致） */
    回显设定() {
      for (const 行 of this.行们) {
        if (行.定装) {
          this.设定.画幅 = 行.定装.画幅 || '9:16'
          this.设定.分辨率 = 行.定装.分辨率 || '480p'
          this.设定.全局风格 = 行.定装.全局风格 || ''
          return
        }
      }
    },
    /* 头部设定（画幅/分辨率/全局风格）：存到该组全部定装行 */
    async 存设定(键) {
      const 值 = this.设定[键]
      const 行们 = this.行们.filter(行 => 行.定装)
      if (!行们.length) return
      try {
        for (const 行 of 行们) {
          await 发('/api/美术/保存', { id: 行.定装.id, [键]: 值 })
        }
        this.$message.success('已应用到全部 ' + 行们.length + ' 项')
      } catch (e) {
        this.$message.error('保存失败：' + ((e && e.message) || e))
      }
    },
    打开图窗(组, 只历史) {
      this.图窗组 = 组
      this.只看历史 = !!只历史
      this.上传形态 = ''
      this.图窗显 = true
    },
    /* 重拉后把图窗组指回聚合后的新对象 */
    同步图窗组() {
      if (!this.图窗组) return
      this.图窗组 = this.组们.find(组 => 组.键 === this.图窗组.键) || null
    },
    /* ---------------- ＋新增（全剧共用，集号=0） ---------------- */
    打开新增() {
      this.新增缓冲 = { 类型: this.激活分区, 名称: '', 别名: '', 级别: '', 摘要: '' }
      this.新增窗显 = true
    },
    async 保存新增() {
      const 页 = this
      const 缓冲 = 页.新增缓冲
      if (!缓冲 || !String(缓冲.名称 || '').trim()) {
        页.$message.error('名称不能为空')
        return
      }
      页.新增中 = true
      try {
        const 数据 = await 发('/api/美术/新增', {
          剧id: 页.剧id, 类型: 缓冲.类型, 名称: 缓冲.名称,
          别名: 缓冲.别名, 级别: 缓冲.级别, 摘要: 缓冲.摘要
        })
        页.新增窗显 = false
        页.激活分区 = 数据.类型 || 页.激活分区
        await 页.载入()
        页.$message.success('已新增 ' + (数据.资产id || '') + ' ' + (数据.名称 || ''))
      } catch (e) {
        页.$message.error('新增失败：' + ((e && e.message) || e))
      }
      页.新增中 = false
    },
    /* ---------------- 上传（带分类/形态，上传后自动 T2 解析提示词） ----------------
       组 可选：占位卡直接上传时传卡片组；图窗上传时用 this.图窗组 */
    /* ---------------- 上传参考图：占位卡=新增第一张；有图卡(传 替换图)=替换该卡图片不新建 ---------------- */
    async 上传参考图(选项, 组, 替换图) {
      const 页 = this
      const 组值 = 组 || 页.图窗组
      if (!组值 || !组值.定装id) {
        页.$message.warning('该项还没有美术定装行')
        return
      }
      页.上传中 = true
      let 新url = ''
      let 图id = 0
      try {
        新url = await 页.传文件(选项.file)
        if (替换图 && 替换图.id) {
          /* 替换：编辑当前卡那张图行的地址，提示词清空待重新解析 */
          await 发('/api/美术/参考图保存', {
            定装id: 组值.定装id, 动作: '编辑',
            id: 替换图.id, url: 新url, 提示词: ''
          })
          图id = 替换图.id
        } else {
          const 形态 = (页.上传形态 || '').trim()
          const 数据 = await 发('/api/美术/参考图保存', {
            定装id: 组值.定装id, 动作: '添加',
            url: 新url, 标注: '', 来源: '上传',
            分类: 组值.类型, 形态: 形态 || null
          })
          图id = 数据.id || 0
        }
        await 页.重拉()
        页.同步图窗组()
        页.$message.success(替换图 ? '图片已替换' : '已上传并落库')
      } catch (e) {
        页.$message.error('上传失败：' + ((e && e.message) || e))
      }
      页.上传中 = false
      /* 上传成功后自动解析提示词（不阻塞，后台跑完写回）；url 直接用上传返回路径，不依赖重拉反查 */
      if (图id && 新url) 页.解析图提示词({ id: 图id, url: 新url }, 组值)
    },
    /* 重拉后按 id 找到新图的 url（解析要用图地址） */
    最新图url(图id) {
      for (const 组 of this.组们) {
        for (const 图 of 组.图们) if (图.id === 图id) return 图.url
      }
      return ''
    },
    /* ---------------- 单图：解析提示词（T2 图片解析任务；组 可选，卡片/图窗两用） ---------------- */
    async 解析图提示词(图, 组) {
      const 页 = this
      const 组值 = 组 || 页.图窗组
      if (!图 || !图.url) return
      页.解析中id = 图.id
      /* 分类：图上选了分类用图的，没选用资产类型；四类各用各的解析引导词（人物可同步档案） */
      const 分类 = 图.分类 || (组值 && 组值.类型) || '人物'
      const 是人物 = 分类 === '人物'
      const 解析要求 = 分类解析要求[分类] || 分类解析要求.场景
      try {
        const 行 = await 提交图片任务({
          类型: '图片解析',
          参数: {
            输入图1: 图.url,
            正向提示词: 解析要求
          }
        })
        const 文 = (行.回复 || '').trim()
        if (!文) throw new Error('解析结果为空')
        await 发('/api/美术/参考图保存', { 定装id: 组值.定装id, 动作: '编辑', id: 图.id, 提示词: 文 })
        await 页.重拉()
        页.同步图窗组()
        页.$message.success('提示词已解析并落库')
        /* 人物图解析完自动同步进关联角色档案（多套外形按【形态】分段）；仅在明确挂在人物资产下时触发 */
        if (是人物 && 组值 && 组值.定装id) {
          try {
            const 同 = await 发('/api/美术/参考图保存', { 定装id: 组值.定装id, 动作: '同步外形', id: 图.id })
            页.$message.success('已同步外形到角色「' + 同.人物 + '」（' + 同.套名 + '：' + (同.更新 || []).join('/') + '）')
          } catch (e2) {
            页.$message.warning('外形同步失败：' + ((e2 && e2.message) || e2) + '，可关联角色后手动同步')
          }
        }
      } catch (e) {
        页.$message.error('解析提示词失败：' + ((e && e.message) || e))
      }
      页.解析中id = null
    },
    /* ---------------- 人物卡：关联角色 + 同步外形 ---------------- */
    /* 关联下拉的默认值：该图没显式关联时按资产 id 匹配人物档案 */
    关联默认(组) {
      if (!组.资产id) return ''
      for (const 人 of this.人物选项们) {
        if (人.人物id === 组.资产id) return 组.资产id
      }
      return ''
    },
    /* 选/换关联角色：落库后立刻把图片提示词同步进该角色档案 */
    async 改关联(卡, 人物id) {
      const 页 = this
      try {
        await 发('/api/美术/参考图保存', {
          定装id: 卡.组.定装id, 动作: '编辑', id: 卡.图.id, 关联人物: 人物id || ''
        })
        页.$set(卡.图, '关联人物', 人物id || '')
        页.$message.success(人物id ? '已关联角色' : '已清除关联')
        if (人物id) await 页.同步外形(卡)
      } catch (e) {
        页.$message.error('关联失败：' + ((e && e.message) || e))
      }
    },
    /* 同步外形：后端把该图提示词按 外貌/身材/穿搭 拆字段写回人物档案（首套覆盖，之后按【形态】追加） */
    async 同步外形(卡) {
      const 页 = this
      if (!卡.图 || !卡.组.定装id) return
      页.同步中id = 卡.图.id
      try {
        const 同 = await 发('/api/美术/参考图保存', { 定装id: 卡.组.定装id, 动作: '同步外形', id: 卡.图.id })
        页.$message.success('已同步外形到角色「' + 同.人物 + '」（' + 同.套名 + '：' + (同.更新 || []).join('/') + '）')
      } catch (e) {
        页.$message.error('同步失败：' + ((e && e.message) || e))
      }
      页.同步中id = null
    },
    /* ---------------- 单图字段编辑（标注/分类/形态/提示词） ---------------- */
    async 改图字段(图, 字段, 值) {
      const 页 = this
      try {
        await 发('/api/美术/参考图保存', { 定装id: 页.图窗组.定装id, 动作: '编辑', id: 图.id, [字段]: 值 })
        页.$set(图, 字段, 值)
        页.$message.success('已保存')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
    },
    打开图提示词(图, 组) {
      this.编辑图 = 图
      this.编辑图组 = 组 || this.图窗组
      this.图提示词窗显 = true
    },
    async 存图提示词() {
      const 页 = this
      if (!页.编辑图) return
      页.图存中 = true
      try {
        await 发('/api/美术/参考图保存', { 定装id: 页.编辑图组.定装id, 动作: '编辑', id: 页.编辑图.id, 提示词: 页.编辑图.提示词 || '' })
        await 页.重拉()
        页.同步图窗组()
        页.图提示词窗显 = false
        页.$message.success('提示词已落库')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.图存中 = false
    },
    /* ---------------- 单图 AI 编辑（T4 三图一致版 / T5 多人合并版 / T5b 动漫转真人） ----------------
       组 可选：从图窗里点某张图进来时用 this.图窗组；从卡片「重新生成」进来时直接传卡片组 */
    打开AI编辑(图, 预填, 组) {
      const 组值 = 组 || this.图窗组
      if (!组值 || !组值.当前图们.length) {
        this.$message.warning('先上传或生成一张当前参考图')
        return
      }
      this.AI编辑 = {
        任务类型: '三图编辑一致版',
        组键: 组值.键,
        图1: 图 ? 图.url : 组值.当前图们[0].url,
        图2: '',
        图3: '',
        正向: 预填 || (图 && 图.提示词) || '',
        源图id: 图 ? 图.id : 组值.当前图们[0].id,
        技能id: '',
        需求: ''
      }
      this.选择目标 = ''
      this.引导词显 = false
      this.应用任务技能()
      this.AI编辑窗显 = true
    },
    /* ---------------- AI 编辑里的扩写：技能 + 引导词（按 页面×任务类型×技能 存库） ---------------- */
    /* 三种编辑任务（T4/T5/T5b）各自的配置类型：引导词与技能记忆互不混用 */
    任务配置类型() {
      return '生成:/video/art:' + ((this.AI编辑 && this.AI编辑.任务类型) || '三图编辑一致版')
    },
    async 拉图扩技能() {
      const 页 = this
      try {
        const 数据 = await 取('/api/提示词/技能列表?分类=' + encodeURIComponent('图片提示词扩写'))
        页.图扩技能们 = 数据.列表 || []
        页.应用任务技能()
      } catch (e) { /* 技能列表拉不到不阻塞页面 */ }
    },
    /* 按当前任务类型解析默认技能（该类型上次选的 → 该类型关键词适配最适），并载对应引导词 */
    应用任务技能() {
      const 页 = this
      if (!页.图扩技能们.length) return
      const 类型 = 页.任务配置类型()
      页.图扩技能id = 读技能id(类型) || 适配技能id(页.图扩技能们, 类型)
      if (页.AI编辑) 页.AI编辑.技能id = 页.图扩技能id
      页.载引导词(页.图扩技能id)
    },
    /* 引导词：库里「任务类型×技能」那份，没存过回退默认扩写规则 */
    async 载引导词(技能id) {
      let 文 = await 读引导(this.任务配置类型(), 技能id)
      if (!文) 文 = 默认扩写规则
      this.引导词文本 = 文
    },
    切扩写技能(技能id) {
      this.图扩技能id = 技能id
      if (this.AI编辑) this.AI编辑.技能id = 技能id
      记技能id(this.任务配置类型(), 技能id)
      this.载引导词(技能id)
    },
    /* 切任务类型：换用该类型记忆/适配的技能与其引导词 */
    切任务类型() {
      this.应用任务技能()
    },
    async 存引导词() {
      const 页 = this
      if (!页.AI编辑 || !页.AI编辑.技能id) {
        页.$message.warning('先选择技能再保存引导词（引导词按「任务类型×技能」各存一份）')
        return
      }
      页.引导词存中 = true
      try {
        await 存配置(页.任务配置类型(), 页.AI编辑.技能id, 页.引导词文本)
        页.$message.success('已保存「' + 页.AI编辑.任务类型 + '」该技能的引导词')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.引导词存中 = false
    },
    /* AI扩写：需求 → 完整正向提示词（引用已选的 图1/图2/图3 作锚点） */
    async AI扩写() {
      const 页 = this
      const 任 = 页.AI编辑
      if (!任 || !任.技能id) { 页.$message.warning('请先选择提示词技能'); return }
      if (!任.需求 || !任.需求.trim()) { 页.$message.warning('请先填写扩写需求'); return }
      页.扩写中 = true
      try {
        const 引用 = []
        for (let i = 1; i <= 3; i++) {
          if (任['图' + i]) 引用.push({ 名称: '图' + i, 类型: 'image' })
        }
        const 数据 = await 发('/api/提示词/扩写', {
          技能id: 任.技能id, 模式: 'image',
          需求: 任.需求.trim(), 引用: 引用,
          附加规则: 页.引导词文本 || ''
        })
        页.$set(任, '正向', 数据.提示词 || 任.正向)
        页.$message.success('已扩写并填入正向提示词')
      } catch (e) {
        页.$message.error('扩写失败：' + ((e && e.message) || e))
      }
      页.扩写中 = false
    },
    /* 图位角标说明：按任务类型区分图2/图3 的用途 */
    图位说明(n) {
      const t = this.AI编辑 && this.AI编辑.任务类型
      if (n === 1) return '主图 · 默认当前图'
      if (t === '多图编辑多人合并版') return '并入画面 · 至少一张'
      if (t === '动漫转真人') return '本任务不使用'
      return '可选 · 一致性参考'
    },
    /* 图位「从参考图选」：展开/收起选图条 */
    选参考图(目标) {
      this.选择目标 = this.选择目标 === 目标 ? '' : 目标
    },
    /* 选图条里点一张图 → 赋给目标图位 */
    挑图(图) {
      if (!this.选择目标 || !this.AI编辑) return
      this.AI编辑[this.选择目标] = 图.url
      if (this.选择目标 === '图1') this.AI编辑.源图id = 图.id
      this.选择目标 = ''
    },
    /* 图位「上传」：直接传文件并把相对路径填进该图位 */
    async 上传编辑图(目标, 选项) {
      try {
        const 路径 = await this.传文件(选项.file)
        if (!this.AI编辑) return
        this.AI编辑[目标] = 路径
        if (目标 === '图1') this.AI编辑.源图id = 0   // 外部上传的图不在参考图库，不参与转历史
      } catch (e) {
        this.$message.error('上传失败：' + ((e && e.message) || e))
      }
    },
    async 提交AI编辑() {
      const 页 = this
      const 任 = 页.AI编辑
      if (!任 || !任.图1) { 页.$message.warning('请先设置图1（默认当前图，可从参考图选或上传）'); return }
      if (任.任务类型 === '多图编辑多人合并版' && !任.图2 && !任.图3) {
        页.$message.warning('多图编辑·多人合并版最少要两张图：请再从参考图选或上传图2/图3')
        return
      }
      if (!String(任.正向 || '').trim()) { 页.$message.warning('正向提示词不能为空'); return }
      if (!页.AI编辑组 || !页.AI编辑组.定装id) { 页.$message.warning('该项还没有美术定装行，无法转存产物'); return }
      /* 与测试页参数对齐：动漫转真人只收 图1+提示词，多余的图位不传 */
      const 参数 = { 输入图1: 任.图1, 正向提示词: 任.正向 }
      if (任.任务类型 !== '动漫转真人') {
        if (任.图2) 参数.输入图2 = 任.图2
        if (任.图3) 参数.输入图3 = 任.图3
      }
      const 源图 = ((页.AI编辑组 && 页.AI编辑组.图们) || []).filter(图 => 图.id === 任.源图id)[0] || null
      页.编辑任务中 = true
      try {
        const 行 = await 提交图片任务({ 类型: 任.任务类型, 参数: 参数 })
        const 产物 = 行.产物图片2 || 行.产物图片
        if (!产物) throw new Error('任务成功但没有产物图片')
        /* 一图一卡：产物新增一张卡片，源图保留不转历史（不要可手动删卡） */
        const 加 = await 发('/api/美术/参考图保存', {
          定装id: 页.AI编辑组.定装id, 动作: '添加',
          url: 产物, 标注: (源图 && 源图.标注) || 'AI编辑', 来源: '生成',
          分类: (源图 && 源图.分类) || 页.AI编辑组.类型, 形态: (源图 && 源图.形态) || null
        })
        await 页.重拉()
        页.同步图窗组()
        页.AI编辑窗显 = false
        页.$message.success('AI 编辑完成，已新增一张参考图卡片')
        /* 产物自动解析提示词（不阻塞）；人物图解析完自动同步外形进角色档案（几张图几套外形） */
        if (加 && 加.id) 页.解析图提示词({ id: 加.id, url: 产物 }, 页.AI编辑组)
      } catch (e) {
        页.$message.error('AI 编辑失败：' + ((e && e.message) || e))
      }
      页.编辑任务中 = false
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
    async 图操作(图, 动作) {
      const 页 = this
      if (动作 === '删除') {
        try { await 页.$confirm('删除这张参考图？', '确认', { type: 'warning' }) } catch (e) { return }
      }
      try {
        await 发('/api/美术/参考图保存', { 定装id: 页.图窗组.定装id, 动作: 动作, id: 图.id })
        await 页.重拉()
        页.同步图窗组()
        页.$message.success(动作 === '删除' ? '已删除' : 动作 === '转历史' ? '已转历史' : '已恢复为当前')
      } catch (e) {
        页.$message.error('操作失败：' + ((e && e.message) || e))
      }
    },
    async 重拉() {
      const 数据 = await 取('/api/美术/列表?剧id=' + this.剧id)
      this.行们 = (数据 && 数据.行们) || []
    },
    编辑提示词(组) {
      this.编辑组 = 组
      this.提示词窗显 = true
    },
    async 存提示词() {
      const 页 = this
      const 组 = 页.编辑组
      if (!组 || !组.定装id) { 页.$message.warning('该项还没有定装行'); return }
      页.存中 = true
      try {
        await 发('/api/美术/保存', {
          id: 组.定装id,
          生图提示词: 组.生图提示词, 必须保持: 组.必须保持, 禁止出现: 组.禁止出现
        })
        页.提示词窗显 = false
        页.$message.success('提示词已落库')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.存中 = false
    },
    编辑音色(组) {
      this.停音色轮询()
      this.音色合成中 = false
      this.编辑组 = 组
      this.合成文本 = 组.音色提示词 || '大家好，这是一段音色试听示例。'
      this.合成音色名 = 'zh-CN-XiaoxiaoNeural'
      this.音色窗显 = true
    },
    /* AI 合成音色：发起「音色合成」任务并轮询，成功后把产物填进当前表单，
       用户点「保存」走既有 存音色 流程落库（2026-11-04 新增） */
    async AI合成音色() {
      const 页 = this
      const 组 = 页.编辑组
      if (!组 || !组.定装id) return
      const 文本 = (页.合成文本 || '').trim()
      if (!文本) { 页.$message.warning('请先填写要合成的台词文本'); return }
      if (页.音色合成中) return
      页.音色合成中 = true
      try {
        const 数据 = await 发('/api/任务/提交', { 类型: '音色合成', 正向提示词: 文本, 模式: 页.合成音色名 })
        const 任务id = 数据 && 数据.id
        if (!任务id) throw new Error('后端未返回任务 id')
        页.启动音色轮询(任务id)
      } catch (e) {
        页.$message.error('发起合成失败：' + ((e && e.message) || e))
        页.音色合成中 = false
      }
    },
    启动音色轮询(任务id) {
      const 页 = this
      页.停音色轮询()
      页.音色轮询器 = setInterval(async function () {
        try {
          const 数据 = await 取('/api/任务/状态?id=' + 任务id)
          const 态 = 数据 && 数据.状态
          if (态 === '成功') {
            页.停音色轮询()
            页.音色合成中 = false
            if (数据.产物视频1 && 页.编辑组) 页.编辑组.音色url = 数据.产物视频1
            if (页.编辑组) 页.编辑组.音色状态 = '已生成'
            页.$message.success('音色已合成，点「保存」落库')
          } else if (态 === '失败' || 态 === '中断') {
            页.停音色轮询()
            页.音色合成中 = false
            页.$message.error('合成失败：' + ((数据 && 数据.错误信息) || '未知原因'))
          } else if (态 === '已取消') {
            页.停音色轮询()
            页.音色合成中 = false
            页.$message.warning('合成任务已取消')
          }
        } catch (e) { /* 单次轮询失败继续等 */ }
      }, 2000)
    },
    停音色轮询() {
      if (this.音色轮询器) {
        clearInterval(this.音色轮询器)
        this.音色轮询器 = null
      }
    },
    async 存音色() {
      const 页 = this
      const 组 = 页.编辑组
      if (!组 || !组.定装id) return
      页.存中 = true
      try {
        await 发('/api/美术/保存', { id: 组.定装id, 音色提示词: 组.音色提示词 })
        页.音色窗显 = false
        页.$message.success('音色提示词已落库')
      } catch (e) {
        页.$message.error('保存失败：' + ((e && e.message) || e))
      }
      页.存中 = false
    },
    /* 上传音色文件：音色编辑弹窗（用 编辑组）与卡片音色区（传 组）两用 */
    async 上传音色文件(选项, 组) {
      const 页 = this
      const 组值 = 组 || 页.编辑组
      if (!组值 || !组值.定装id) return
      页.上传中 = true
      try {
        const 路径 = await 页.传文件(选项.file)
        await 发('/api/美术/保存', { id: 组值.定装id, 音色url: 路径, 音色状态: '已生成' })
        await 页.重拉()
        页.$message.success('音色文件已上传并落库')
      } catch (e) {
        页.$message.error('上传失败：' + ((e && e.message) || e))
      }
      页.上传中 = false
    },
    试听(组) {
      if (!组.音色url) { this.$message.info('还没有音色文件'); return }
      window.open(this.音色播放地址(组.音色url), '_blank')
    },
    /* 音色文件播放地址：/voices/ 开头是前端静态目录直出，其余走后端媒体接口 */
    音色播放地址(url) {
      if (!url) return ''
      if (url.indexOf('/voices/') === 0) return url
      return 媒体地址(url)
    },
    /* ---------------- 音色库选择（/voices 同源） ---------------- */
    打开音库(组) {
      this.音库组 = 组
      this.音库分类 = '全部'
      this.音库词 = ''
      this.音库窗显 = true
    },
    播库音色(音) {
      const 页 = this
      const a = 页.$refs.库音频
      if (!a) return
      if (页.库正在播id === 音.id) { a.pause(); 页.库正在播id = null; return }
      a.src = 音.文件
      const p = a.play()
      if (p && p.catch) p.catch(() => 页.$message.warning('浏览器拦截了自动播放，请再点一次'))
      页.库正在播id = 音.id
    },
    停库音色() {
      const a = this.$refs.库音频
      if (a) a.pause()
      this.库正在播id = null
    },
    async 选用库音色(音) {
      const 页 = this
      const 组 = 页.音库组
      if (!组 || !组.定装id) {
        页.$message.warning('该项还没有美术定装行')
        return
      }
      try {
        await 发('/api/美术/保存', { id: 组.定装id, 音色名: 音.名, 音色url: 音.文件, 音色状态: '已生成' })
        await 页.重拉()
        页.停库音色()
        页.音库窗显 = false
        页.$message.success('已把「' + 音.名 + '」设为「' + 组.名称 + '」的音色')
      } catch (e) {
        页.$message.error('选择失败：' + ((e && e.message) || e))
      }
    },
    /* 卡片删除：删掉这张参考图（组不删；最后一张删完资产回到占位卡） */
    async 删卡图(卡) {
      const 页 = this
      if (!卡.图 || !卡.组.定装id) return
      try { await 页.$confirm('删除「' + 卡.组.名称 + '」这张参考图卡片？', '确认', { type: 'warning' }) } catch (e) { return }
      try {
        await 发('/api/美术/参考图保存', { 定装id: 卡.组.定装id, 动作: '删除', id: 卡.图.id })
        await 页.重拉()
        页.同步图窗组()
        页.$message.success('已删除')
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    },
    /* 删资产：整个美术资产删除（参考图+定装+资产行），占位卡没有图也能删掉建错的资产 */
    async 删资产(组) {
      const 页 = this
      if (!组 || !组.定装id) return
      try { await 页.$confirm('删除整个「' + 组.名称 + '」（' + 组.类型 + '）？该资产的全部参考图、音色等会一起清除，不可恢复。', '确认删除', { type: 'warning' }) } catch (e) { return }
      try {
        await 发('/api/美术/参考图保存', { 定装id: 组.定装id, 动作: '删资产' })
        await 页.重拉()
        页.同步图窗组()
        页.$message.success('已删除资产「' + 组.名称 + '」')
      } catch (e) {
        页.$message.error('删除失败：' + ((e && e.message) || e))
      }
    },
    /* 重新生成：以指定图（默认第一张当前图）为底开 AI 编辑弹窗，产物会新增一张卡片 */
    重新生成图(组, 图) {
      const 底图 = 图 || 组.当前图们[0]
      if (!底图) {
        this.$message.warning('「' + 组.名称 + '」还没有当前参考图，请先上传一张，再以此图为基础重新生成')
        return
      }
      /* 提示词 = 定装生图提示词 + 全局风格 + 保持/禁止约束 */
      const 段们 = []
      if (组.生图提示词) 段们.push(组.生图提示词)
      if (this.设定.全局风格) 段们.push('全局风格：' + this.设定.全局风格)
      if (组.必须保持) 段们.push('必须保持：' + 组.必须保持.replace(/\n/g, '；'))
      if (组.禁止出现) 段们.push('禁止出现：' + 组.禁止出现.replace(/\n/g, '；'))
      this.打开AI编辑(底图, 段们.join('\n'), 组)
    },
    去资产() {
      this.$router.push({ path: '/video/assets', query: this.$route.query })
    },
    上一步() { this.$router.push({ path: '/video/assets', query: this.$route.query }) },
    下一步() { this.$router.push({ path: '/video/shot', query: this.$route.query }) }
  }
}
</script>

<style scoped>
/* ---- 页头 ---- */
.头卡 { padding: 16px 18px; margin-bottom: 14px; }
.头行 { display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.头题 { font-size: 15px; font-weight: 700; color: var(--字); }
.分区签行 { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.分区签 {
  font-size: 12px; color: var(--字次); cursor: pointer;
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 14px; padding: 3px 12px; transition: all .15s ease;
}
.分区签:hover { color: var(--字); border-color: var(--描边亮, var(--描边)); }
.分区签.活 { color: var(--主); border-color: var(--主); background: var(--主浅); font-weight: 600; }
.分区签.加签 { color: var(--主); border-style: dashed; }
.设定块 { display: flex; flex-direction: column; gap: 6px; min-width: 260px; }
.设定行 { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--字次); }
.设键 { width: 56px; flex: 0 0 auto; }
.设选 { width: 130px; }
.设选.宽 { width: 170px; }
.提示行 { margin-top: 12px; font-size: 12px; color: var(--字弱); line-height: 1.7; }
.提示行 b { color: var(--主); }

.状态卡 { padding: 22px; text-align: center; color: var(--字次); font-size: 13px; margin-bottom: 14px; }
.状态卡.败 { color: var(--败, #f56c6c); }
.主色 { color: var(--主); }

/* ---- 卡流 ---- */
.卡流 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 14px;
}
.资卡 { padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; }

.资头 { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.资名 { font-size: 14px; font-weight: 700; color: var(--字); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.类签 {
  font-size: 11px; color: var(--字次);
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 4px; padding: 1px 7px; flex: 0 0 auto;
}
.性签 {
  font-size: 11px; color: var(--主);
  background: var(--主浅); border-radius: 4px; padding: 1px 7px; flex: 0 0 auto;
}
.集签 {
  font-size: 11px; color: var(--字弱);
  border: 1px dashed var(--描边); border-radius: 4px; padding: 1px 6px; flex: 0 0 auto;
}
.态签 { font-size: 11px; color: var(--成, #67c23a); flex: 0 0 auto; }
.态签.待 { color: var(--警, #e6a23c); }

.小钮 {
  font-size: 12px; color: var(--字次); cursor: pointer;
  background: var(--卡片二); border: 1px solid var(--描边);
  border-radius: 6px; padding: 3px 10px;
  transition: all .15s ease; white-space: nowrap;
}
.小钮:hover { border-color: var(--描边亮, var(--描边)); color: var(--字); }
.小钮.主 { color: var(--主); border-color: var(--主); background: transparent; }
.小钮.主:hover { background: var(--主浅); }
.小钮:disabled { opacity: .5; cursor: not-allowed; }
.删钮:hover { color: var(--败, #f56c6c); border-color: var(--败, #f56c6c); }

/* ---- 缩略行 ---- */
.缩略行 { display: flex; gap: 8px; cursor: pointer; }
.缩略块 {
  width: 92px; height: 120px; border-radius: 8px; overflow: hidden;
  background: var(--卡片二); border: 1px solid var(--描边);
  display: flex; flex-direction: column; flex: 0 0 auto;
}
.缩略图 { width: 100%; height: 96px; object-fit: cover; display: block; }
.缩略标 {
  font-size: 10px; color: var(--字次); text-align: center;
  line-height: 22px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 0 4px;
}
.缩略块.更多 {
  align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700; color: var(--字次);
}
.缩略块.占位 {
  width: auto; min-width: 200px; height: 74px; flex: 1;
  align-items: center; justify-content: center; gap: 6px;
  font-size: 12px; color: var(--字弱);
}
.缩略块.占位 i { font-size: 22px; }

.约行 { font-size: 12px; line-height: 1.8; padding-left: 14px; position: relative; }
.约行::before {
  content: ''; position: absolute; left: 0; top: 9px;
  width: 6px; height: 6px; border-radius: 50%;
}
.约行.保 { color: var(--字次); }
.约行.保::before { background: var(--成, #67c23a); }
.约行.禁 { color: var(--字弱); }
.约行.禁::before { background: var(--败, #f56c6c); }

/* ---- 音色区 ---- */
.音区 {
  border-top: 1px dashed var(--描边);
  padding-top: 10px;
  display: flex; flex-direction: column; gap: 8px;
}
.音头 { display: flex; align-items: center; gap: 8px; }
.音标 { font-size: 12px; font-weight: 600; color: var(--字); }
.音提示 { font-size: 11px; color: var(--字弱); }
.音文 {
  font-size: 12px; line-height: 1.7; color: var(--字次);
  background: var(--卡片二); border-radius: 6px; padding: 7px 10px;
}
.音操作 { display: flex; gap: 8px; flex-wrap: wrap; }
.音名签 {
  font-size: 11px; color: var(--主); background: var(--主浅);
  border-radius: 4px; padding: 2px 8px; cursor: pointer; white-space: nowrap;
}

/* ---- 音色库选择弹窗 ---- */
.音库过滤 { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.音库签 {
  font-size: 12px; color: var(--字次); border: 1px solid var(--描边);
  border-radius: 999px; padding: 3px 12px; cursor: pointer; user-select: none;
}
.音库签:hover { color: var(--字); border-color: var(--描边亮, var(--描边)); }
.音库签.活 { color: var(--主); border-color: var(--主); background: var(--主浅); font-weight: 600; }
.音库列表 { max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.音库行 {
  display: flex; align-items: center; gap: 10px;
  border: 1px solid var(--描边); border-radius: 8px;
  padding: 8px 12px; cursor: pointer; background: var(--卡片二);
}
.音库行:hover { border-color: var(--主); }
.音库行.选中 { border-color: var(--主); background: var(--主浅); }
.音库播 { font-size: 18px; color: var(--主); flex: none; }
.音库信 { flex: 1; min-width: 0; }
.音库名 { font-size: 13px; font-weight: 600; color: var(--字); }
.音库别 { font-size: 11px; font-weight: 400; color: var(--字弱); margin-left: 6px; }
.音库说 {
  font-size: 11px; color: var(--字弱); margin-top: 2px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.音库空 { font-size: 12px; color: var(--字弱); text-align: center; padding: 32px 0; }

.出图行 { display: flex; gap: 8px; margin-top: auto; flex-wrap: wrap; }

/* ---- 一图一卡：大图与图片提示词 ---- */
.大图行 { margin-bottom: 10px; }
/* 卡片大图（用户 2026-11-02：人物显示全，框大小保持不变）：cover裁剪 → contain 完整缩放进框，
   高度仍 230px，竖图左右留边（底色跟卡片），点图仍有放大预览 */
.大图 { width: 100%; height: 230px; object-fit: contain; background: var(--卡片二, rgba(127,127,127,.08)); display: block; cursor: zoom-in; border-radius: 8px; border: 1px solid var(--描边); }
.词行 { cursor: pointer; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.词行:hover { border-color: var(--主); }
.关行 { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.关标 { font-size: 12px; color: var(--字次); flex: none; }
.关选 { width: 180px; }

/* 参考图弹窗的样式已随组件拆入 美术资产参考图弹窗.vue；此处仅保留 AI 编辑弹窗仍用到的 .窗空 */
.窗空 { font-size: 12px; color: var(--字弱); padding: 20px 0; text-align: center; }

/* ---- 编辑弹窗 ---- */
.表单块 { margin-bottom: 14px; }
.表单标 { font-size: 12px; color: var(--字次); margin-bottom: 6px; }
.表单格 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

/* ---- AI 编辑弹窗：扩写技能行 + 引导词配置 ---- */
.扩写排 { display: flex; gap: 8px; align-items: center; }
.扩技能 { width: 210px; flex: none; }
.扩需求 { flex: 1; }
.引导区 { margin-top: 10px; border: 1px solid var(--描边); border-radius: 8px; padding: 10px; background: var(--卡片二); }
.引导题 { font-size: 12px; color: var(--字弱); margin-bottom: 8px; line-height: 1.6; }
.引导钮行 { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }

/* ---- AI 编辑弹窗：图位（与 /test 三图编辑一致版同款布局） ---- */
.类型注 { font-size: 12px; color: var(--字弱); margin-top: 8px; line-height: 1.6; }
.图位行 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 6px; }
.图位 { display: flex; flex-direction: column; gap: 6px; }
.图位题 { font-size: 12px; font-weight: 600; color: var(--字次); }
.图位说 { font-weight: 400; color: var(--字弱); margin-left: 6px; font-size: 11px; }
.图位框 {
  height: 110px; border: 1px dashed var(--描边); border-radius: 8px;
  background: var(--卡片二); overflow: hidden; display: flex; align-items: center; justify-content: center;
}
.图位图 { width: 100%; height: 100%; object-fit: contain; cursor: pointer; display: block; }
.图位空 { font-size: 22px; color: var(--字弱); cursor: pointer; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.图位空:hover { color: var(--主); }
.图位操作 { display: flex; gap: 6px; flex-wrap: wrap; }
.选图条 { border: 1px solid var(--描边); border-radius: 8px; padding: 10px; margin-bottom: 12px; background: var(--卡片二); }
.选图题 { font-size: 12px; color: var(--字次); margin-bottom: 8px; }
.取选 { color: var(--主); margin-left: 8px; }
.选图行 { display: flex; gap: 8px; flex-wrap: wrap; max-height: 200px; overflow-y: auto; }
.选图块 { width: 84px; cursor: pointer; border: 2px solid transparent; border-radius: 6px; overflow: hidden; }
.选图块:hover { border-color: var(--主); }
.选图图 { width: 100%; height: 64px; object-fit: contain; display: block; background: var(--卡片, transparent); }
.选图标 { font-size: 10px; color: var(--字弱); padding: 2px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.新增注 { font-size: 11px; color: var(--字弱); }

/* ---- 底部统计 ---- */
.统计条 {
  margin-top: 14px; padding: 12px 16px;
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--字次);
}
.统计条 b { color: var(--主); }
.分隔 { color: var(--字弱); }
</style>
