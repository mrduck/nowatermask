<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Undo2 } from 'lucide-vue-next'

const props = defineProps<{ imageSrc: string }>()
const emit = defineEmits<{ maskReady: [maskBlob: Blob | null] }>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const isDrawing = ref(false)
const brushSize = ref(20)
const isEraser = ref(false)

let img: HTMLImageElement | null = null
let ctx: CanvasRenderingContext2D | null = null
let maskCanvas: HTMLCanvasElement | null = null
let maskCtx: CanvasRenderingContext2D | null = null
let displayWidth = 0
let displayHeight = 0

function initCanvas() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    displayWidth = container!.clientWidth
    displayHeight = Math.round((img!.naturalHeight / img!.naturalWidth) * displayWidth)

    canvas.width = displayWidth
    canvas.height = displayHeight
    ctx = canvas.getContext('2d')!
    ctx.drawImage(img!, 0, 0, displayWidth, displayHeight)

    maskCanvas = document.createElement('canvas')
    maskCanvas.width = img!.naturalWidth
    maskCanvas.height = img!.naturalHeight
    maskCtx = maskCanvas.getContext('2d')!
  }
  img.src = props.imageSrc
}

function getPos(e: MouseEvent | Touch): { x: number; y: number } {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
}

function startDraw(e: MouseEvent | Touch) {
  isDrawing.value = true
  const pos = getPos(e)
  draw(pos.x, pos.y)
}

function draw(x: number, y: number) {
  if (!ctx || !maskCtx || !canvasRef.value) return

  const scaleX = maskCanvas!.width / displayWidth
  const scaleY = maskCanvas!.height / displayHeight

  ctx.save()
  if (isEraser.value) {
    ctx.globalCompositeOperation = 'destination-out'
    ctx.beginPath()
    ctx.arc(x, y, brushSize.value, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()

    maskCtx.save()
    maskCtx.globalCompositeOperation = 'destination-out'
    maskCtx.beginPath()
    maskCtx.arc(x * scaleX, y * scaleY, brushSize.value * scaleX, 0, Math.PI * 2)
    maskCtx.fill()
    maskCtx.restore()
  } else {
    ctx.globalAlpha = 0.6
    ctx.fillStyle = '#ef4444'
    ctx.beginPath()
    ctx.arc(x, y, brushSize.value, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()

    maskCtx.fillStyle = '#ffffff'
    maskCtx.beginPath()
    maskCtx.arc(x * scaleX, y * scaleY, brushSize.value * scaleX, 0, Math.PI * 2)
    maskCtx.fill()
  }

  emitMask()
}

function endDraw() {
  isDrawing.value = false
}

function onMouseDown(e: MouseEvent) {
  startDraw(e)
}
function onMouseMove(e: MouseEvent) {
  if (!isDrawing.value) return
  draw(e.offsetX, e.offsetY)
}
function onMouseUp() {
  endDraw()
}

function onTouchStart(e: TouchEvent) {
  e.preventDefault()
  startDraw(e.touches[0])
}
function onTouchMove(e: TouchEvent) {
  e.preventDefault()
  if (!isDrawing.value) return
  draw(e.touches[0].clientX - canvasRef.value!.getBoundingClientRect().left,
       e.touches[0].clientY - canvasRef.value!.getBoundingClientRect().top)
}
function onTouchEnd() {
  endDraw()
}

function clearMask() {
  if (!ctx || !maskCtx || !canvasRef.value || !maskCanvas) return
  ctx.clearRect(0, 0, displayWidth, displayHeight)
  ctx.drawImage(img!, 0, 0, displayWidth, displayHeight)
  maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height)
  emitMask()
}

function emitMask() {
  if (!maskCanvas) {
    emit('maskReady', null)
    return
  }
  maskCanvas.toBlob((blob) => {
    emit('maskReady', blob)
  }, 'image/png')
}

watch(() => props.imageSrc, () => {
  nextTick(initCanvas)
})

onMounted(() => {
  nextTick(initCanvas)
})

onUnmounted(() => {
  img = null
})
</script>

<template>
  <div class="flex-1">
    <div class="border border-gray-200 rounded-lg bg-gray-50 relative select-none" ref="containerRef">
      <canvas
        ref="canvasRef"
        class="w-full cursor-crosshair rounded"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseUp"
        @touchstart.passive="false"
      />
    </div>
    <div class="mt-2 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-1 text-sm text-gray-600">
          Brush:
          <input
            type="range"
            v-model.number="brushSize"
            min="5"
            max="60"
            class="w-20 h-1 accent-blue-500"
          />
          <span class="text-xs text-gray-400 w-6">{{ brushSize }}</span>
        </label>
        <button
          @click="isEraser = !isEraser"
          class="px-2 py-1 rounded text-xs transition"
          :class="isEraser ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          {{ isEraser ? 'Eraser' : 'Brush' }}
        </button>
        <button
          @click="clearMask"
          class="flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-100 text-gray-600 hover:bg-gray-200 transition"
        >
          <Undo2 class="w-3 h-3" />
          Clear
        </button>
      </div>
      <span class="text-xs text-gray-400">Paint over watermarks to mark them</span>
    </div>
  </div>
</template>