<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps<{
  imageSrc: string
  aspectRatio?: number | null
  lockRatio: boolean
}>()

const emit = defineEmits<{
  cropChange: [x: number, y: number, w: number, h: number]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

let img: HTMLImageElement | null = null
let ctx: CanvasRenderingContext2D | null = null
let displayW = 0
let displayH = 0

let boxX = 0
let boxY = 0
let boxW = 0
let boxH = 0
let dragging = false
let dragType: 'move' | 'tl' | 'tr' | 'bl' | 'br' | '' = ''
let dragStartX = 0
let dragStartY = 0
let boxStartX = 0
let boxStartY = 0
let boxStartW = 0
let boxStartH = 0

function initCanvas() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    displayW = container!.clientWidth
    displayH = Math.round((img!.naturalHeight / img!.naturalWidth) * displayW)
    canvas.width = displayW
    canvas.height = displayH
    ctx = canvas.getContext('2d')!

    if (props.lockRatio && props.aspectRatio) {
      boxW = Math.min(displayW * 0.6, (displayH / props.aspectRatio) * 0.6)
      boxH = boxW / props.aspectRatio
    } else {
      boxW = displayW * 0.4
      boxH = displayH * 0.4
    }
    boxX = (displayW - boxW) / 2
    boxY = (displayH - boxH) / 2
    clampBox()
    emitCrop()
    draw()
  }
  img.src = props.imageSrc
}

function clampBox() {
  if (boxX < 0) boxX = 0
  if (boxY < 0) boxY = 0
  if (boxX + boxW > displayW) boxX = displayW - boxW
  if (boxY + boxH > displayH) boxY = displayH - boxH
}

function emitCrop() {
  emit('cropChange', boxX / displayW, boxY / displayH, boxW / displayW, boxH / displayH)
}

function draw() {
  if (!ctx || !img) return
  ctx.clearRect(0, 0, displayW, displayH)
  ctx.drawImage(img, 0, 0, displayW, displayH)

  ctx.fillStyle = 'rgba(0,0,0,0.4)'
  ctx.fillRect(0, 0, displayW, boxY)
  ctx.fillRect(0, boxY, boxX, boxH)
  ctx.fillRect(boxX + boxW, boxY, displayW - boxX - boxW, boxH)
  ctx.fillRect(0, boxY + boxH, displayW, displayH - boxY - boxH)

  ctx.strokeStyle = '#2563eb'
  ctx.lineWidth = 2
  ctx.strokeRect(boxX, boxY, boxW, boxH)

  const handleSize = 10
  ctx.fillStyle = '#ffffff'
  ctx.strokeStyle = '#2563eb'
  ctx.lineWidth = 1
  const corners = [
    [boxX, boxY],
    [boxX + boxW, boxY],
    [boxX, boxY + boxH],
    [boxX + boxW, boxY + boxH]
  ]
  for (const [cx, cy] of corners) {
    ctx.fillRect(cx - handleSize / 2, cy - handleSize / 2, handleSize, handleSize)
    ctx.strokeRect(cx - handleSize / 2, cy - handleSize / 2, handleSize, handleSize)
  }
}

function getDragType(mx: number, my: number): 'tl' | 'tr' | 'bl' | 'br' | 'move' | '' {
  const threshold = 15
  if (Math.abs(mx - boxX) < threshold && Math.abs(my - boxY) < threshold) return 'tl'
  if (Math.abs(mx - boxX - boxW) < threshold && Math.abs(my - boxY) < threshold) return 'tr'
  if (Math.abs(mx - boxX) < threshold && Math.abs(my - boxY - boxH) < threshold) return 'bl'
  if (Math.abs(mx - boxX - boxW) < threshold && Math.abs(my - boxY - boxH) < threshold) return 'br'
  if (mx > boxX && mx < boxX + boxW && my > boxY && my < boxY + boxH) return 'move'
  return ''
}

function onMouseDown(e: MouseEvent) {
  const rect = canvasRef.value!.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top
  dragType = getDragType(mx, my)
  if (!dragType) return
  dragging = true
  dragStartX = mx
  dragStartY = my
  boxStartX = boxX
  boxStartY = boxY
  boxStartW = boxW
  boxStartH = boxH
}

function onMouseMove(e: MouseEvent) {
  const rect = canvasRef.value!.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  if (dragging) {
    const dx = mx - dragStartX
    const dy = my - dragStartY
    if (dragType === 'move') {
      boxX = boxStartX + dx
      boxY = boxStartY + dy
    } else {
      if (dragType === 'tl') {
        boxX = boxStartX + dx
        boxY = boxStartY + dy
        boxW = boxStartW - dx
        boxH = boxStartH - dy
      } else if (dragType === 'tr') {
        boxY = boxStartY + dy
        boxW = boxStartW + dx
        boxH = boxStartH - dy
      } else if (dragType === 'bl') {
        boxX = boxStartX + dx
        boxW = boxStartW - dx
        boxH = boxStartH + dy
      } else if (dragType === 'br') {
        boxW = boxStartW + dx
        boxH = boxStartH + dy
      }
      if (props.lockRatio && props.aspectRatio) {
        boxH = boxW / props.aspectRatio
      }
    }
    clampBox()
    emitCrop()
    draw()
    return
  }

  const dt = getDragType(mx, my)
  const c = canvasRef.value!
  if (dt === 'tl' || dt === 'br') c.style.cursor = 'nwse-resize'
  else if (dt === 'tr' || dt === 'bl') c.style.cursor = 'nesw-resize'
  else if (dt === 'move') c.style.cursor = 'move'
  else c.style.cursor = 'crosshair'
}

function onMouseUp() {
  dragging = false
  dragType = ''
}

function onTouchStart(e: TouchEvent) {
  if (e.touches.length === 1) {
    const t = e.touches[0]
    onMouseDown({ clientX: t.clientX, clientY: t.clientY } as MouseEvent)
  }
}

function onTouchMove(e: TouchEvent) {
  e.preventDefault()
  if (e.touches.length === 1) {
    const t = e.touches[0]
    onMouseMove({ clientX: t.clientX, clientY: t.clientY } as MouseEvent)
  }
}

function onTouchEnd() {
  onMouseUp()
}

watch(() => props.imageSrc, () => nextTick(initCanvas))
watch(() => props.aspectRatio, () => {
  if (props.lockRatio && props.aspectRatio && boxW > 0) {
    boxH = boxW / props.aspectRatio
    clampBox()
    emitCrop()
    draw()
  }
})

onMounted(() => nextTick(initCanvas))
</script>

<template>
  <div ref="containerRef" class="border border-gray-200 rounded-lg bg-gray-100 relative select-none overflow-hidden">
    <canvas
      ref="canvasRef"
      class="w-full cursor-crosshair"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      @touchstart.prevent="onTouchStart"
      @touchmove.prevent="onTouchMove"
      @touchend="onTouchEnd"
    />
  </div>
</template>