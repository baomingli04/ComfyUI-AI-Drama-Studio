// 复制文本到剪贴板：优先用 clipboard API，非安全上下文或被拒时回退 textarea + execCommand
// 返回 Promise<boolean>，调用方据此给提示
export async function 复制到剪贴板(文本) {
  const 文 = String(文本 == null ? '' : 文本)
  if (!文) return false

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(文)
      return true
    }
  } catch (e) {
    // 落到下面的回退方案
  }

  try {
    const 区 = document.createElement('textarea')
    区.value = 文
    区.setAttribute('readonly', 'readonly')
    区.style.position = 'fixed'
    区.style.top = '-9999px'
    区.style.left = '-9999px'
    区.style.opacity = '0'
    document.body.appendChild(区)
    区.select()
    区.setSelectionRange(0, 文.length)
    const 成功 = document.execCommand('copy')
    document.body.removeChild(区)
    return 成功
  } catch (e) {
    return false
  }
}
