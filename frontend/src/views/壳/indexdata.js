// 壳的菜单数据：分组见 docs/07 G8；路由路径用英文（URL 不带中文），标题中文
// docs/12 第 2 节：四个新模块「直接作为侧边栏的四个项目」加进去，与现有三组并列。
// 不另套子组，不加中间层 —— 所以这四个用 扁平:true 渲染成一级 el-menu-item。
export const 菜单 = [
  {
    标题: '系统',
    分组: '系统',
    子项: [
      { 标题: '用户', 路径: '/user', 图标: 'el-icon-user' },
      { 标题: '模型配置', 路径: '/model-config', 图标: 'el-icon-setting' },
      { 标题: '技能管理', 路径: '/skill-manage', 图标: 'el-icon-folder-opened' }
    ]
  },
  {
    标题: '测试',
    分组: '测试',
    子项: [
      { 标题: 'T1 文本回复', 路径: '/test/t1-text', 图标: 'el-icon-chat-line-round' },
      { 标题: 'T2 图片解析', 路径: '/test/t2-image-parse', 图标: 'el-icon-picture-outline' },
      { 标题: 'T3 生成图片', 路径: '/test/t3-text2img', 图标: 'el-icon-magic-stick' },
      { 标题: 'T3B 生成图片8K', 路径: '/test/t3b-text2img8k', 图标: 'el-icon-magic-stick' },
      { 标题: '3图编辑一致版', 路径: '/test/t4-edit-3img', 图标: 'el-icon-edit' },
      { 标题: '多图编辑多人合并版', 路径: '/test/t5-edit-multi', 图标: 'el-icon-edit-outline' },
      { 标题: '动漫转真人编辑', 路径: '/test/t5b-anime2real', 图标: 'el-icon-picture' },
      { 标题: 'T6 人物替换', 路径: '/test/t6-face-swap', 图标: 'el-icon-user-solid' },
      { 标题: 'T7 首尾帧', 路径: '/test/t7-frame2frame', 图标: 'el-icon-video-play' },
      { 标题: 'T8 参考生视频', 路径: '/test/t8-ref2video', 图标: 'el-icon-film' },
      { 标题: 'T9 去水印', 路径: '/test/t9-dewatermark', 图标: 'el-icon-brush' },
      { 标题: 'T10 二采重绘', 路径: '/test/t10-repaint', 图标: 'el-icon-refresh' },
      { 标题: 'T11 音频剪辑', 路径: '/test/t11-audio-edit', 图标: 'el-icon-headset' }
    ]
  },
  {
    标题: '导演台',
    分组: '导演台',
    子项: [
      // 2026-10-21 起导演台只保留 D2 多参考生视频；其余项在此屏蔽（路由未动，需要时取消注释即恢复）
      // { 标题: 'D1 文生视频', 路径: '/test/d1-t2v', 图标: 'el-icon-video-camera' },
      { 标题: 'D2 多参考生视频', 路径: '/test/d2-r2v', 图标: 'el-icon-picture-outline' },
      { 标题: 'D全 导演台全能', 路径: '/test/d-all', 图标: 'el-icon-video-camera' },
      // { 标题: 'D3 首尾帧生视频', 路径: '/test/d3-fl2v', 图标: 'el-icon-copy-document' },
      // { 标题: 'D4 视频生视频', 路径: '/test/d4-v2v', 图标: 'el-icon-video-play' },
      // { 标题: 'D5 参考视频生视频', 路径: '/test/d5-rv2v', 图标: 'el-icon-film' },
      // { 标题: 'D6 加速版生视频', 路径: '/test/d6-acc', 图标: 'el-icon-film' },
      // { 标题: 'D7 二采加速生视频', 路径: '/test/d7-refine', 图标: 'el-icon-film' },
      // { 标题: 'D8 外部分组图生视频', 路径: '/test/d8-i2v-groups', 图标: 'el-icon-film' },
      // { 标题: 'D9 外部分组多参考生视频', 路径: '/test/d9-r2v-groups', 图标: 'el-icon-film' }
    ]
  },
  {
    标题: '工具',
    分组: '工具',
    子项: [{ 标题: '工作流下载', 路径: '/tool/workflow', 图标: 'el-icon-download' }]
  },
  // ---- docs/12 新增：四个独立一级项目，不套子组 ----
  {
    标题: '剧本创作', 分组: '剧本创作', 路径: '/script', 图标: 'el-icon-notebook-2', 扁平: true, 分隔: true
  },
  {
    标题: '视频生成', 分组: '视频生成', 路径: '/video', 图标: 'el-icon-video-camera', 扁平: true
  },
  {
    标题: '我的资产', 分组: '我的资产', 路径: '/assets', 图标: 'el-icon-picture', 扁平: true
  },
  {
    标题: '音色库', 分组: '音色库', 路径: '/voices', 图标: 'el-icon-microphone', 扁平: true
  }
]
