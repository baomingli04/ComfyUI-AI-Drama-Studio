<template>
  <!-- 参考图弹窗（从 美术资产.vue 拆出）：当前图按形态分节 + 历史图。
       显隐（图窗显）、图窗组、上传形态与全部业务方法仍在父组件，
       本组件承载模板/展示计算属性，操作经 $emit 回传父组件。 -->
  <el-dialog :visible="visible" :title="组 ? 组.名称 + ' · 参考图' : '参考图'"
             width="860px" top="6vh" append-to-body
             @update:visible="$emit('update:visible', $event)">
    <template v-if="组">
      <div class="窗操作行">
        <el-upload action="#" :show-file-list="false" multiple accept="image/*"
                   :http-request="o => $emit('上传', o)" :disabled="上传中">
          <el-button size="small" type="primary" icon="el-icon-upload2" :loading="上传中">上传图片</el-button>
        </el-upload>
        <span class="窗形选">形态
          <el-select :value="上传形态" size="small" filterable allow-create clearable placeholder="通用" class="形选框"
                     @input="$emit('update:上传形态', $event)">
            <el-option v-for="形 in 形态选项们" :key="形" :label="形" :value="形" />
          </el-select>
        </span>
        <span class="窗提示">可一次选多张；上传后自动解析提示词；每张图可改分类/形态/标注</span>
      </div>

      <div class="窗分组" v-for="形态组 in 图窗形态组们" :key="'f' + 形态组.名">
        <div class="窗组题">{{ 形态组.名 }}（{{ 形态组.图们.length }}）</div>
        <div class="图网格">
          <div v-for="图 in 形态组.图们" :key="'c' + 图.id" class="图块">
            <img class="图" :src="媒体地址(图.url)" @click="$emit('预览', 图)" />
            <div class="图注">
              <input class="标注输入" :value="图.标注" placeholder="填写标注，如 正面定装"
                     @change="$emit('改字段', 图, '标注', $event.target.value)" />
              <div class="图选择行">
                <el-select :value="图.分类 || 组.类型" size="mini" class="类选框"
                           @change="$emit('改字段', 图, '分类', $event)">
                  <el-option v-for="t in ['人物', '场景', '道具', '服装']" :key="t" :label="t" :value="t" />
                </el-select>
                <el-select :value="图.形态 || ''" size="mini" filterable allow-create clearable
                           placeholder="形态" class="形选框2" @change="$emit('改字段', 图, '形态', $event)">
                  <el-option v-for="形 in 形态选项们" :key="形" :label="形" :value="形" />
                </el-select>
              </div>
              <div class="提示词行" @click="$emit('打开提示词', 图)">
                <span :class="{ 无: !图.提示词 }">{{ 图.提示词 ? (图.提示词.length > 46 ? 图.提示词.slice(0, 46) + '…' : 图.提示词) : '（无提示词，点此解析/填写）' }}</span>
              </div>
              <span class="图签">{{ 图.来源 }} · E{{ 图.集号 }}</span>
            </div>
            <div class="图操作">
              <button class="小钮" :disabled="解析中id === 图.id" @click="$emit('解析', 图)">
                {{ 解析中id === 图.id ? '解析中…' : '解析提示词' }}
              </button>
              <button class="小钮 主" @click="$emit('AI编辑', 图)">AI编辑</button>
              <button class="小钮" @click="$emit('图操作', 图, '转历史')">转历史</button>
              <button class="小钮 删钮" @click="$emit('图操作', 图, '删除')">删</button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!组.当前图们.length" class="窗空">还没有当前参考图，上传或重新生成</div>

      <div class="窗分组" v-if="组.历史图们.length">
        <div class="窗组题">历史（{{ 组.历史图们.length }}）</div>
        <div class="图网格">
          <div v-for="图 in 组.历史图们" :key="'h' + 图.id" class="图块 历史块">
            <img class="图" :src="媒体地址(图.url)" @click="$emit('预览', 图)" />
            <div class="图注">
              <input class="标注输入" :value="图.标注" placeholder="标注"
                     @change="$emit('改字段', 图, '标注', $event.target.value)" />
              <div class="提示词行" v-if="图.提示词" @click="$emit('打开提示词', 图)">
                <span>{{ 图.提示词.length > 46 ? 图.提示词.slice(0, 46) + '…' : 图.提示词 }}</span>
              </div>
              <span class="图签">{{ 图.来源 }} · E{{ 图.集号 }}<template v-if="图.形态"> · {{ 图.形态 }}</template></span>
            </div>
            <div class="图操作">
              <button class="小钮" @click="$emit('图操作', 图, '恢复')">恢复为当前</button>
              <button class="小钮 删钮" @click="$emit('图操作', 图, '删除')">删</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { 媒体地址 } from '@/接口/媒体'

/* 参考图弹窗（从 美术资产.vue 拆出）。
   上传参考图/改图字段/打开图提示词/解析图提示词/打开AI编辑/图操作 与页面主表单
   （卡片流）共用，保留在父组件；本组件只承载模板与两个展示计算属性，操作经 $emit 回传。 */
export default {
  name: 'ArtRefImagesDialog',
  props: {
    visible: { type: Boolean, default: false },
    组: { type: Object, default: null },       // 即父组件的 图窗组
    上传中: { type: Boolean, default: false },
    解析中id: { type: [Number, String], default: null },
    上传形态: { type: String, default: '' }
  },
  computed: {
    /* 该资产已有过的全部形态（供下拉复用） */
    形态选项们() {
      const 组 = this.组
      if (!组) return []
      const 列 = []
      for (const 图 of 组.图们) {
        const 形 = (图.形态 || '').trim()
        if (形 && 列.indexOf(形) < 0) 列.push(形)
      }
      return 列
    },
    /* 当前参考图按形态分节（空形态归入「通用」） */
    图窗形态组们() {
      const 组 = this.组
      if (!组) return []
      const 映射 = {}
      const 顺序 = []
      for (const 图 of 组.当前图们) {
        const 名 = (图.形态 || '').trim() || '通用'
        if (!映射[名]) { 映射[名] = { 名: 名, 图们: [] }; 顺序.push(名) }
        映射[名].图们.push(图)
      }
      return 顺序.map(名 => 映射[名])
    }
  },
  methods: { 媒体地址 }
}
</script>

<style scoped>
/* 小钮在本组件 scoped 内单独声明（与父组件同名同款） */
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

/* ---- 参考图弹窗 ---- */
.窗操作行 { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.窗提示 { font-size: 12px; color: var(--字弱); }
.窗形选 { font-size: 12px; color: var(--字次); display: inline-flex; align-items: center; gap: 6px; }
.形选框 { width: 130px; }
.形选框2 { width: 110px; }
.类选框 { width: 92px; }
.窗分组 { margin-bottom: 16px; }
.窗组题 { font-size: 13px; font-weight: 700; color: var(--字); margin-bottom: 10px; }
.窗空 { font-size: 12px; color: var(--字弱); padding: 20px 0; text-align: center; }
.图网格 { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.图块 {
  border: 1px solid var(--描边); border-radius: 8px; overflow: hidden;
  background: var(--卡片二); display: flex; flex-direction: column;
}
.图块.历史块 { opacity: .75; }
.图 { width: 100%; height: 170px; object-fit: cover; display: block; cursor: zoom-in; }
.图注 { padding: 6px 8px 2px; display: flex; flex-direction: column; gap: 4px; }
.标注输入 {
  font-size: 12px; color: var(--字);
  background: transparent; border: 1px dashed transparent;
  border-radius: 4px; padding: 2px 6px; width: 100%;
}
.标注输入:hover, .标注输入:focus { border-color: var(--描边); outline: none; background: var(--卡片); }
.图选择行 { display: flex; gap: 6px; }
.提示词行 {
  font-size: 11px; line-height: 1.6; color: var(--字次);
  background: var(--卡片); border-radius: 4px; padding: 4px 6px;
  cursor: pointer; word-break: break-all;
}
.提示词行:hover { color: var(--主); }
.提示词行 .无 { color: var(--字弱); font-style: italic; }
.图签 { font-size: 10px; color: var(--字弱); }
.图操作 { display: flex; gap: 6px; padding: 6px 8px 8px; flex-wrap: wrap; }
</style>
