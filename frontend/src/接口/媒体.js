// 媒体地址：把后端相对路径（上传/xxx.png、产物/task_1_1.png）拼成带 token 的可显示地址
import { 基础地址, 取令牌 } from '@/接口/请求'

export function 媒体地址(相对路径) {
  if (!相对路径) return ''
  const 子路径 = String(相对路径).split('/').map(encodeURIComponent).join('/')
  return 基础地址 + '/api/媒体/' + 子路径 + '?token=' + encodeURIComponent(取令牌())
}

export function 是图片(路径) {
  return /\.(png|jpe?g|gif|webp|bmp)$/i.test(路径 || '')
}

export function 是视频(路径) {
  return /\.(mp4|webm|mov|avi|mkv)$/i.test(路径 || '')
}

export function 是音频(路径) {
  return /\.(mp3|wav|ogg|m4a|aac|flac)$/i.test(路径 || '')
}
