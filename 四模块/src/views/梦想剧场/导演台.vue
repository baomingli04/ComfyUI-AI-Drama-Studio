<template>
  <div>
    <!-- 面包屑 -->
    <div class="面包屑条">
      <span class="可点" @click="$router.push('/theater')">梦想剧场</span>
      <span> / </span>
      <span class="可点" @click="$router.push({ path:'/theater/assets', query:$route.query })">{{ 剧名 }}</span>
      <span> / </span>
      <span style="color:var(--字次)">导演台</span>
    </div>

    <!-- 进度步骤 -->
    <div class="卡片" style="margin-bottom:16px">
      <div class="步骤条" style="margin:0">
        <div class="步 完成"><span class="圈"><i class="el-icon-check"></i></span><span class="字">剧本编辑</span></div>
        <span class="连"></span>
        <div class="步 完成"><span class="圈"><i class="el-icon-check"></i></span><span class="字">分镜与美术资产</span></div>
        <span class="连"></span>
        <div class="步 当前"><span class="圈">3</span><span class="字">导演台</span></div>
        <span class="连"></span>
        <div class="步"><span class="圈">4</span><span class="字">短片</span></div>
      </div>
    </div>

    <div style="display:flex;gap:16px;align-items:flex-start">
      <!-- 左列 -->
      <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:16px">
        <!-- Tabs -->
        <div class="行间">
          <el-button size="small" :type="页签 === '单镜生成' ? 'primary' : ''" plain @click="页签 = '单镜生成'">单镜生成</el-button>
          <el-button size="small" :type="页签 === '成片' ? 'primary' : ''" plain @click="$router.push({ path:'/theater/film', query:$route.query })">成片</el-button>
        </div>

        <div class="卡片 无内距" style="display:flex;flex-direction:column">
          <!-- 头信息 -->
          <div style="padding:16px;border-bottom:1px solid var(--描边);display:flex;justify-content:space-between">
            <div>
              <div style="font-size:12px;color:var(--字弱);margin-bottom:4px">分镜信息</div>
              <div style="font-size:13px;color:var(--字)">镜头 {{ 当前镜.镜号 }} · 12.0s 计划</div>
            </div>
            <div style="text-align:right">
              <div style="font-size:12px;color:var(--字弱);margin-bottom:4px">成片信息</div>
              <div style="font-size:13px;color:var(--字)">镜头 {{ 当前镜.镜号 }} · 四宫格</div>
            </div>
          </div>

          <!-- 脚本内容 -->
          <div style="padding:16px;max-height:300px;overflow-y:auto;font-size:12px;line-height:1.9;color:var(--字次)">
            <p style="margin:0 0 4px"><span style="color:var(--主)">[场景描述: SCN 001 教室·日]</span></p>
            <p style="margin:0 0 4px"><span style="color:var(--主)">[情绪标签: 冷感建立]</span></p>
            <p style="margin:0 0 4px">分镜 {{ 当前镜.镜号 }} | 时间 00:00-00:12 | 时长 12秒 | 场景 {{ 当前镜.场次 }} | 人物 C1 | 高三教室前排</p>
            <p style="margin:0 0 4px">镜头设定 (Camera)：</p>
            <p style="margin:0 0 4px">教室前侧，林夜向窗外看，定上几颗刚结好的青果，低平小构图，窗边挂着两幅红联，黑板漆面不全。</p>
            <p style="margin:0 0 4px">Blocking（动-动-静）：</p>
            <p style="margin:0 0 4px">起，林夜站在讲台，手背抵住桌沿；动，右手握粉笔缓缓抬起；静，目光落于窗外树梢，不再移动。</p>
            <p style="margin:0 0 4px">镜头内部时间线（0.0s 起，总长 12.0s）：</p>
            <p style="margin:0 0 4px">0-5s：特写 | 50mm | 斜日微光透过窗棂落在肩线，慢光不动 | S1 | C1</p>
            <p style="margin:0 0 4px">5-12s：极缓推近 | 50mm | 指尖与窗棂边缘占据画面右下，手影微动</p>
            <p style="margin:0 0 4px">光线：午后教室斜日打在黑板白底边缘</p>
            <p style="margin:0 0 4px">道具提示：粉笔一根，教案本摊开在第一页</p>
            <p style="margin:0 0 4px">入点描述：教室前侧，林夜背影与窗棂，静帧建立</p>
            <p style="margin:0 0 4px">出点描述：极缓推近 50mm，指尖轻触窗棂边缘不动</p>
            <p style="margin:0">负面提示：禁止出现第二块暖光源，禁止切林夜正脸入画，禁止头部移动超过极缓推</p>
          </div>

          <!-- 生成参考图 -->
          <div style="border-top:1px solid var(--描边);padding:16px">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;color:var(--字弱)">生成参考图</span>
              <span style="font-size:12px;color:var(--字弱)">四宫格</span>
            </div>
            <div class="行间" style="margin-bottom:12px">
              <el-button size="mini" type="primary" plain>已生成</el-button>
              <el-button size="mini" plain @click="生成()">重绘</el-button>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;border-radius:8px;overflow:hidden">
              <div v-for="i in 4" :key="i" class="占位图" style="height:120px">
                <span>原图：参考图 {{ i }}</span>
              </div>
            </div>

            <div style="display:flex;align-items:center;gap:12px;margin-top:16px">
              <div style="display:flex;align-items:center;gap:8px;background:var(--描边);padding:6px 10px;border-radius:6px;font-size:12px;color:var(--字次)">
                <span>16:9</span><span style="color:var(--字弱)">|</span>
                <span>720p</span><span style="color:var(--字弱)">|</span>
                <span>四宫格</span>
              </div>
              <el-button type="primary" style="flex:1" @click="生成()">生成镜头</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右列 -->
      <div style="width:400px;flex:0 0 400px;display:flex;flex-direction:column;gap:16px">
        <div class="卡片" style="height:280px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--字弱)">
          <i class="el-icon-video-camera" style="font-size:44px;margin-bottom:8px"></i>
          <div style="font-size:13px">暂无预览</div>
          <div style="font-size:12px;margin-top:8px;text-align:center;line-height:1.6">
            点「生成镜头」后，此处将实时显示比例预览
          </div>
        </div>

        <div class="卡片">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:12px;color:var(--字弱)">镜头列表 · 当前镜头 {{ 当前镜.镜号 }} 为参考图</span>
            <span style="font-size:12px;color:var(--字弱)">共 {{ 分镜列表.length }} 帧</span>
          </div>
          <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px">
            <div
              v-for="镜 in 分镜列表"
              :key="镜.id"
              style="flex:0 0 72px;cursor:pointer"
              @click="当前镜 = 镜"
            >
              <div
                class="占位图"
                :style="{ height:'52px', border: 当前镜.id === 镜.id ? '2px solid var(--主)' : '1px solid var(--描边)', background:'linear-gradient(135deg,' + 镜.色 + ',#0f172a)' }"
              >
                <span style="font-size:11px">{{ 镜.镜号 }}</span>
              </div>
              <div style="font-size:11px;color:var(--字弱);margin-top:4px;text-align:center">{{ 镜.时长 }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部条 -->
    <div class="卡片" style="margin-top:16px;display:flex;align-items:center;justify-content:space-between">
      <div class="行间">
        <span style="font-size:14px;font-weight:700;color:var(--主)">{{ 已完成 }}</span>
        <span style="font-size:12px;color:var(--字弱)">/ {{ 分镜列表.length }} 帧镜头完成</span>
      </div>
      <div class="行间">
        <el-button size="small" @click="连续生成()">连续生成</el-button>
        <el-button size="small" type="primary" @click="$router.push({ path:'/theater/film', query:$route.query })">成片</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { 分镜列表 } from '../../假数据'

export default {
  name: 'Director',
  data() {
    return {
      页签: '单镜生成',
      分镜列表: 分镜列表.map(x => Object.assign({}, x)),
      当前镜: null
    }
  },
  created() {
    this.当前镜 = this.分镜列表[0]
  },
  computed: {
    剧名() {
      return this.$route.query.name || '火影之禁术教师'
    },
    已完成() {
      return this.分镜列表.filter(x => x.状态 === '已生成').length
    }
  },
  methods: {
    生成() {
      this.当前镜.状态 = '已生成'
      this.$message.success('已提交生成：' + this.当前镜.镜号)
    },
    连续生成() {
      this.分镜列表.forEach(x => { x.状态 = '已生成' })
      this.$message.success('已提交连续生成，共 ' + this.分镜列表.length + ' 帧')
    }
  }
}
</script>
