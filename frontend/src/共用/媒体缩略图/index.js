export default {
  name: '媒体缩略图',
  props: {
    媒体列表: { type: Array, default: () => [] },
    // 是否允许逐条删除。默认 false：任务列表里的产物缩略图只是看看，不给删；
    // 表单区（如导演台全能的素材上传）传 true，删的时候逐个删，不用整组清空。
    可删除: { type: Boolean, default: false },
    // 大号预览：表单区用（160×120），任务列表里还是 52×52 小图。
    大号: { type: Boolean, default: false },
    // 显示全：图片不裁剪，按自身比例缩放（复用 缩略块-自适应 的样式规则）。
    // 默认 false 保持 52×52 cover 裁剪；t2 图片解析等页面传 true 让人物/背景完整可见。
    显示全: { type: Boolean, default: false }
  }
}
