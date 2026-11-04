<template>
  <div>
    <!-- 页头 -->
    <div class="页头">
      <div class="左">
        <h1 class="标题">新建剧本</h1>
        <div class="副题">定义故事起始场景，再用推荐标签与集数规划项目</div>
      </div>
      <div class="右">
        <el-button @click="$router.push('/script')">返回列表</el-button>
      </div>
    </div>

    <!-- 步骤条 -->
    <div class="步骤条">
      <div class="步" :class="第1步类">
        <div class="圈">1</div>
        <div class="字">故事起点</div>
      </div>
      <div class="连"></div>
      <div class="步" :class="第2步类">
        <div class="圈">2</div>
        <div class="字">确认信息</div>
      </div>
    </div>

    <!-- 第 1 步：故事起点 -->
    <div v-if="当前步 === 1">
      <div class="卡片" style="margin-bottom:16px">
        <div class="行间">
          <div style="background:var(--主);color:#06210f;font-weight:600;padding:8px 14px;border-radius:8px;font-size:13px">
            宏观版：随机开头 - 10 部分
          </div>
          <div style="font-size:12px;color:var(--字弱)">
            今日免费剩余 9 / 10 次（每日刷新 10 次）；推荐标签与随机开头均消耗 1 次随机额度
          </div>
        </div>
      </div>

      <div class="网格 二">
        <div class="卡片">
          <div class="区标题">故事梗概</div>
          <div style="margin-bottom:12px">
            <div style="font-size:13px;color:var(--字次);margin-bottom:6px">剧名</div>
            <el-input v-model="表单.剧名" placeholder="可点选推荐剧名，或自行拟定" maxlength="30"></el-input>
            <div style="font-size:12px;color:var(--字弱);margin-top:4px">{{ 表单.剧名.length }} / 30</div>
          </div>
          <div>
            <div class="行间" style="margin-bottom:6px">
              <div style="font-size:13px;color:var(--字次)">一句话创意</div>
              <div style="flex:1"></div>
              <el-button type="text" size="mini" @click="丰富创意()">AI 丰富梗概</el-button>
            </div>
            <el-input
              type="textarea"
              :rows="9"
              maxlength="500"
              v-model="表单.创意"
              placeholder="例：某日清晨他发现身边人另有身份，两人在误会与信任里从敌对走向彼此并肩...">
            </el-input>
            <div style="font-size:12px;color:var(--字弱);margin-top:4px">{{ 表单.创意.length }} / 500</div>
          </div>
        </div>

        <div class="卡片">
          <div class="区标题">题材标签 · 最多 2 个（主 + 辅）</div>
          <div class="chip组">
            <div
              v-for="项 in 题材选项"
              :key="项"
              class="chip"
              :class="{ 选中: 表单.题材.indexOf(项) >= 0 }"
              @click="切换题材(项)">{{ 项 }}</div>
          </div>
          <div style="font-size:12px;color:var(--主);margin-top:8px">
            * 未选择标签将使用默认推荐，可继续编辑
          </div>

          <el-divider></el-divider>

          <div class="行间" style="margin-bottom:12px">
            <div style="font-size:13px;color:var(--字次);width:48px">集数</div>
            <el-input v-model="表单.集数" style="width:110px">
              <template slot="append">集</template>
            </el-input>
            <div style="font-size:12px;color:var(--字弱)">最多 200 集</div>
          </div>

          <div class="行间">
            <div style="font-size:13px;color:var(--字次);width:48px">时长</div>
            <el-select v-model="表单.单集时长" style="width:130px">
              <el-option label="每集 2 分钟" value="2 分钟"></el-option>
              <el-option label="每集 3 分钟" value="3 分钟"></el-option>
              <el-option label="每集 5 分钟" value="5 分钟"></el-option>
            </el-select>
            <div style="font-size:12px;color:var(--字弱)">
              本剧预计 {{ 预计时长 }} 分钟，分集时长仅作参考
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第 2 步：确认信息 -->
    <div v-else>
      <div class="卡片" style="margin-bottom:16px">
        <div class="区标题">确认信息</div>
        <div class="网格 二" style="gap:12px">
          <div class="回显行">
            <div class="回显名">剧名</div>
            <div class="回显值">{{ 表单.剧名 || '未命名剧本' }}</div>
          </div>
          <div class="回显行">
            <div class="回显名">集数</div>
            <div class="回显值">{{ 表单.集数 }} 集 · 每集 {{ 表单.单集时长 }}</div>
          </div>
          <div class="回显行">
            <div class="回显名">题材</div>
            <div class="回显值">
              <el-tag v-for="项 in 表单.题材" :key="项" size="mini" style="margin-right:6px">{{ 项 }}</el-tag>
              <span v-if="表单.题材.length === 0" style="color:var(--字弱)">未选择，将使用默认推荐</span>
            </div>
          </div>
          <div class="回显行">
            <div class="回显名">预计时长</div>
            <div class="回显值">{{ 预计时长 }} 分钟</div>
          </div>
        </div>
        <div style="margin-top:12px">
          <div class="回显名" style="margin-bottom:6px">一句话创意</div>
          <div style="font-size:13px;color:var(--字次);line-height:1.7">
            {{ 表单.创意 || '（尚未填写，将使用 AI 推荐开头）' }}
          </div>
        </div>
      </div>

      <div class="卡片">
        <div class="区标题">视觉风格</div>
        <div class="chip组">
          <div
            v-for="项 in 风格选项"
            :key="项"
            class="chip"
            :class="{ 选中: 表单.风格 === 项 }"
            @click="表单.风格 = 项">{{ 项 }}</div>
        </div>
        <div style="font-size:12px;color:var(--字弱);margin-top:10px">
          视觉风格将用于后续人物设定与美术资产生成，可在分集大纲页随时调整
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="行间 右" style="margin-top:20px">
      <el-button :disabled="当前步 === 1" @click="上一步()">上一步</el-button>
      <el-button v-if="当前步 === 1" type="primary" @click="下一步()">下一步</el-button>
      <el-button v-else type="primary" @click="开始创作()">开始创作</el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScriptNew',
  data() {
    return {
      当前步: 1,
      表单: {
        剧名: '重生之禁术教师',
        集数: '24',
        创意: '',
        题材: [],
        风格: '写实校园',
        单集时长: '2 分钟'
      },
      题材选项: [
        '都市', '校园', '玄幻', '职场', '年代', '科幻', '悬疑', '古装',
        '家庭伦理', '甜宠', '武侠', '喜剧', '军事', '医疗', '宫斗', '青春'
      ],
      风格选项: ['写实校园', '低饱和胶片', '高对比冷暖', '日系小清新', '赛博霓虹', '水墨国风']
    }
  },
  computed: {
    预计时长() {
      const 集数 = parseInt(this.表单.集数, 10)
      const 单集 = parseInt(this.表单.单集时长, 10)
      if (isNaN(集数) || isNaN(单集)) return 0
      return 集数 * 单集
    },
    第1步类() {
      if (this.当前步 === 1) return '当前'
      return '完成'
    },
    第2步类() {
      if (this.当前步 === 2) return '当前'
      return ''
    }
  },
  methods: {
    切换题材(项) {
      const 位置 = this.表单.题材.indexOf(项)
      if (位置 >= 0) {
        this.表单.题材.splice(位置, 1)
        return
      }
      if (this.表单.题材.length >= 2) {
        this.表单.题材.shift()
      }
      this.表单.题材.push(项)
    },
    丰富创意() {
      if (!this.表单.创意) {
        this.表单.创意 = '十年前的那间教室里，他再次睁开眼。这一次，他要把被列为禁术的东西，一门一门教回去。'
      } else {
        this.表单.创意 = this.表单.创意 + '而真正的问题是：他并不是唯一的重生者。'
      }
    },
    上一步() {
      if (this.当前步 > 1) this.当前步 = this.当前步 - 1
    },
    下一步() {
      if (!this.表单.剧名.trim()) {
        this.$message({ message: '请先填写剧名', type: 'warning' })
        return
      }
      this.当前步 = 2
    },
    开始创作() {
      this.$router.push({
        path: '/script/plan',
        query: {
          剧名: this.表单.剧名,
          集数: this.表单.集数,
          题材: this.表单.题材.join('、'),
          风格: this.表单.风格
        }
      })
    }
  }
}
</script>

<style scoped>
.chip组 { display: flex; flex-wrap: wrap; gap: 8px; }
.回显行 { display: flex; align-items: center; }
.回显名 { width: 72px; flex: 0 0 72px; font-size: 12px; color: var(--字弱); }
.回显值 { font-size: 14px; color: var(--字); }
</style>
