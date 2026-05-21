# 证件照裁剪+排版工具 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有去水印工具旁新增独立的"证件照裁剪"工具，支持手动框选和自动等比例裁剪，输出单张电子版和6寸排版图。

**Architecture:** 前端通过 Canvas 实现裁剪框交互（拖拽/锁定比例），后端用 cv2 做精确裁剪和相纸排版。两个工具通过路由 `/` 和 `/crop` 独立分离，Navbar 提供导航切换。

**Tech Stack:** Vue 3 + TypeScript + Tailwind CSS + Canvas API（前端），FastAPI + cv2 + numpy（后端）

---

## 文件结构

```
创建:
  frontend/src/pages/CropPage.vue        # 证件照裁剪主页
  frontend/src/components/CropCanvas.vue # Canvas 裁剪框交互
  frontend/src/components/LayoutPreview.vue # 排版预览
  backend/watermark_engine/cropper.py    # 裁剪+排版引擎

修改:
  frontend/src/router/index.ts           # 新增 /crop 路由
  frontend/src/components/Navbar.vue     # 新增导航链接
  frontend/src/utils/api.ts             # 新增 crop / layout API
  backend/main.py                        # 新增 /api/crop + /api/layout
```

---

### Task 1: 后端裁剪+排版引擎

**Files:**
- Create: `backend/watermark_engine/cropper.py`

- [ ] **Step 1: 创建 cropper.py — 证件照规格定义 + 裁剪 + 排版**

```python
import cv2
import numpy as np

PHOTO_SPECS = {
    "1inch": {"width": 295, "height": 413, "label": "1寸 (25×35mm)"},
    "s1inch": {"width": 260, "height": 378, "label": "小1寸 (22×32mm)"},
    "2inch": {"width": 413, "height": 579, "label": "2寸 (35×49mm)"},
    "s2inch": {"width": 413, "height": 531, "label": "小2寸 (35×45mm)"},
    "big1inch": {"width": 390, "height": 567, "label": "大一寸 (33×48mm)"},
}

LAYOUT_PRESETS = {
    "1inch": {"cols": 4, "rows": 2},
    "s1inch": {"cols": 4, "rows": 2},
    "2inch": {"cols": 2, "rows": 2},
    "s2inch": {"cols": 2, "rows": 2},
    "big1inch": {"cols": 3, "rows": 2},
}

PAPER_6INCH_W = 1800
PAPER_6INCH_H = 1200
PAPER_PADDING = 10
PHOTO_SPACING = 10


class PhotoCropper:

    @staticmethod
    def crop_and_resize(
        image_data: bytes,
        x: float, y: float, w: float, h: float,
        target_w: int, target_h: int
    ) -> bytes:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width = img.shape[:2]

        px = max(0, int(x * width))
        py = max(0, int(y * height))
        pw = min(width - px, int(w * width))
        ph = min(height - py, int(h * height))

        if pw < 10 or ph < 10:
            _, buf = cv2.imencode(".png", img)
            return buf.tobytes()

        cropped = img[py:py+ph, px:px+pw]
        resized = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

        _, buf = cv2.imencode(".png", resized)
        return buf.tobytes()

    @staticmethod
    def generate_layout(
        image_data: bytes,
        spec: str
    ) -> bytes:
        if spec not in PHOTO_SPECS or spec not in LAYOUT_PRESETS:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            _, buf = cv2.imencode(".png", img)
            return buf.tobytes()

        spec_data = PHOTO_SPECS[spec]
        layout = LAYOUT_PRESETS[spec]
        pw, ph = spec_data["width"], spec_data["height"]
        cols, rows = layout["cols"], layout["rows"]

        nparr = np.frombuffer(image_data, np.uint8)
        photo = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        photo = cv2.resize(photo, (pw, ph), interpolation=cv2.INTER_LANCZOS4)

        canvas = np.ones((PAPER_6INCH_H, PAPER_6INCH_W, 3), dtype=np.uint8) * 255

        for row in range(rows):
            for col in range(cols):
                ox = PAPER_PADDING + col * (pw + PHOTO_SPACING)
                oy = PAPER_PADDING + row * (ph + PHOTO_SPACING)
                if ox + pw <= PAPER_6INCH_W and oy + ph <= PAPER_6INCH_H:
                    canvas[oy:oy+ph, ox:ox+pw] = photo

        _, buf = cv2.imencode(".png", canvas)
        return buf.tobytes()
```

---

### Task 2: 后端 API 端点

**Files:**
- Modify: `backend/main.py` (末尾新增端点)

- [ ] **Step 1: 在 main.py 末尾新增 /api/crop 和 /api/layout**

在文件末尾 `if __name__ == "__main__":` 之前新增：

```python
from watermark_engine.cropper import PhotoCropper


@app.post("/api/crop")
async def crop_photo(
    file: UploadFile = File(...),
    x: float = 0.0,
    y: float = 0.0,
    w: float = 0.5,
    h: float = 0.5,
    target_w: int = 295,
    target_h: int = 413
):
    contents = await file.read()
    result_bytes = PhotoCropper.crop_and_resize(contents, x, y, w, h, target_w, target_h)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/layout")
async def layout_photo(
    file: UploadFile = File(...),
    spec: str = "1inch"
):
    contents = await file.read()
    result_bytes = PhotoCropper.generate_layout(contents, spec)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")
```

---

### Task 3: 前端 API 调用

**Files:**
- Modify: `frontend/src/utils/api.ts` (新增 crop / layout 函数)

- [ ] **Step 1: 在 api.ts 末尾新增**

```typescript
export async function cropPhoto(
  file: File,
  x: number, y: number, w: number, h: number,
  targetW: number, targetH: number
): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('x', String(x))
  formData.append('y', String(y))
  formData.append('w', String(w))
  formData.append('h', String(h))
  formData.append('target_w', String(targetW))
  formData.append('target_h', String(targetH))
  const res = await fetch('/api/crop', { method: 'POST', body: formData })
  return res.blob()
}

export async function generateLayout(file: File, spec: string): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('spec', spec)
  const res = await fetch('/api/layout', { method: 'POST', body: formData })
  return res.blob()
}
```

---

### Task 4: 路由 + 导航

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/Navbar.vue`

- [ ] **Step 1: 新增 /crop 路由**

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import CropPage from '@/pages/CropPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage
    },
    {
      path: '/crop',
      name: 'crop',
      component: CropPage
    }
  ]
})

export default router
```

- [ ] **Step 2: Navbar 新增导航链接**

```vue
<script setup lang="ts">
import { Droplets, Scissors } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <nav class="bg-white border-b border-gray-100 sticky top-0 z-50">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2 font-bold text-lg text-gray-900 hover:text-blue-600 transition-colors">
        <Droplets class="w-5 h-5 text-blue-500" />
        去水印工具
      </router-link>
      <div class="flex items-center gap-1">
        <router-link
          to="/"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          :class="route.path === '/' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
        >
          去水印
        </router-link>
        <router-link
          to="/crop"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1"
          :class="route.path === '/crop' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
        >
          <Scissors class="w-3.5 h-3.5" />
          证件照裁剪
        </router-link>
      </div>
    </div>
  </nav>
</template>
```

---

### Task 5: CropCanvas 组件

**Files:**
- Create: `frontend/src/components/CropCanvas.vue`

- [ ] **Step 1: 完整的 Canvas 裁剪框组件**

```vue
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

let boxX = 0, boxY = 0, boxW = 0, boxH = 0
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
      boxW = Math.min(displayW * 0.6, displayH / props.aspectRatio * 0.6)
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
  emit('cropChange',
    boxX / displayW,
    boxY / displayH,
    boxW / displayW,
    boxH / displayH
  )
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
    [boxX, boxY], [boxX + boxW, boxY],
    [boxX, boxY + boxH], [boxX + boxW, boxY + boxH]
  ]
  for (const [cx, cy] of corners) {
    ctx.fillRect(cx - handleSize/2, cy - handleSize/2, handleSize, handleSize)
    ctx.strokeRect(cx - handleSize/2, cy - handleSize/2, handleSize, handleSize)
  }
}

function getDragType(mx: number, my: number): 'tl'|'tr'|'bl'|'br'|'move'|'' {
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
      if (dragType === 'tl') { boxX = boxStartX + dx; boxY = boxStartY + dy; boxW = boxStartW - dx; boxH = boxStartH - dy }
      else if (dragType === 'tr') { boxY = boxStartY + dy; boxW = boxStartW + dx; boxH = boxStartH - dy }
      else if (dragType === 'bl') { boxX = boxStartX + dx; boxW = boxStartW - dx; boxH = boxStartH + dy }
      else if (dragType === 'br') { boxW = boxStartW + dx; boxH = boxStartH + dy }
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
```

---

### Task 6: LayoutPreview 组件

**Files:**
- Create: `frontend/src/components/LayoutPreview.vue`

- [ ] **Step 1: 排版预览 + 下载组件**

```vue
<script setup lang="ts">
import { Download } from 'lucide-vue-next'

const props = defineProps<{
  layoutSrc: string | null
  layoutBlob: Blob | null
  isGenerating: boolean
}>()

const emit = defineEmits<{
  back: []
}>()

function downloadLayout() {
  if (!props.layoutSrc) return
  const a = document.createElement('a')
  a.href = props.layoutSrc
  a.download = '证件照排版_6寸.png'
  a.click()
}
</script>

<template>
  <div class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-900">6寸相纸排版预览</h3>
      <button @click="emit('back')" class="text-sm text-gray-500 hover:text-gray-700">返回裁剪</button>
    </div>

    <div v-if="isGenerating" class="py-12 text-center text-gray-500">
      <span class="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2 align-middle"></span>
      正在生成排版...
    </div>

    <template v-else-if="layoutSrc">
      <div class="border rounded-lg overflow-hidden bg-gray-100">
        <img :src="layoutSrc" class="w-full" alt="6寸排版预览" />
      </div>
      <p class="mt-3 text-xs text-gray-400 text-center">6寸相纸 (152×102mm @ 300DPI)</p>
      <button
        @click="downloadLayout"
        class="mt-4 w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition flex items-center justify-center gap-2"
      >
        <Download class="w-4 h-4" />
        下载排版图
      </button>
    </template>
  </div>
</template>
```

---

### Task 7: CropPage 主页面

**Files:**
- Create: `frontend/src/pages/CropPage.vue`

- [ ] **Step 1: 证件照裁剪完整页面**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useHead } from '@unhead/vue'
import { Download, ArrowRight, Grid3X3 } from 'lucide-vue-next'
import ImageUploader from '@/components/ImageUploader.vue'
import CropCanvas from '@/components/CropCanvas.vue'
import LayoutPreview from '@/components/LayoutPreview.vue'
import { cropPhoto, generateLayout } from '@/utils/api'

useHead({
  title: '证件照裁剪 - 在线免费证件照裁剪排版工具 | 1寸2寸标准尺寸',
  meta: [
    { name: 'description', content: '免费在线证件照裁剪工具，支持1寸、2寸、小1寸等标准尺寸。手动框选或自动等比例裁剪，一键生成6寸相纸排版图，完全免费。' }
  ]
})

const SPECS: Record<string, { w: number; h: number; label: string }> = {
  '1inch': { w: 295, h: 413, label: '1寸' },
  's1inch': { w: 260, h: 378, label: '小1寸' },
  '2inch': { w: 413, h: 579, label: '2寸' },
  's2inch': { w: 413, h: 531, label: '小2寸' },
  'big1inch': { w: 390, h: 567, label: '大一寸' },
}

const step = ref<'idle' | 'crop' | 'done'>('idle')
const mode = ref<'auto' | 'manual'>('auto')
const selectedSpec = ref('1inch')
const uploadedFile = ref<File | null>(null)
const previewSrc = ref('')

const cropX = ref(0)
const cropY = ref(0)
const cropW = ref(0)
const cropH = ref(0)

const resultSrc = ref('')
const resultBlob = ref<Blob | null>(null)
const isCropping = ref(false)

const layoutSrc = ref<string | null>(null)
const layoutBlob = ref<Blob | null>(null)
const showLayout = ref(false)
const isGeneratingLayout = ref(false)

const aspectRatio = computed(() => {
  if (mode.value !== 'auto') return null
  const spec = SPECS[selectedSpec.value]
  return spec.w / spec.h
})

const cropSizeLabel = computed(() => {
  return SPECS[selectedSpec.value].label
})

function handleFileSelected(file: File, preview: string) {
  uploadedFile.value = file
  previewSrc.value = preview
  step.value = 'crop'
}

function handleCropChange(x: number, y: number, w: number, h: number) {
  cropX.value = x
  cropY.value = y
  cropW.value = w
  cropH.value = h
}

async function handleCrop() {
  if (!uploadedFile.value || isCropping.value) return
  isCropping.value = true
  showLayout.value = false
  layoutSrc.value = null
  const spec = mode.value === 'auto' ? SPECS[selectedSpec.value] : null
  try {
    const blob = await cropPhoto(
      uploadedFile.value,
      cropX.value, cropY.value, cropW.value, cropH.value,
      spec?.w ?? Math.round(cropW.value * 1000),
      spec?.h ?? Math.round(cropH.value * 1000)
    )
    resultBlob.value = blob
    resultSrc.value = URL.createObjectURL(blob)
    step.value = 'done'
  } catch (err) {
    console.error(err)
  } finally {
    isCropping.value = false
  }
}

async function handleGenerateLayout() {
  if (!uploadedFile.value || isGeneratingLayout.value) return
  isGeneratingLayout.value = true
  try {
    const blob = await cropPhoto(
      uploadedFile.value,
      cropX.value, cropY.value, cropW.value, cropH.value,
      SPECS[selectedSpec.value].w,
      SPECS[selectedSpec.value].h
    )
    const layoutBlobResult = await generateLayout(
      new File([blob], 'photo.png', { type: 'image/png' }),
      selectedSpec.value
    )
    layoutBlob.value = layoutBlobResult
    layoutSrc.value = URL.createObjectURL(layoutBlobResult)
    showLayout.value = true
  } catch (err) {
    console.error(err)
  } finally {
    isGeneratingLayout.value = false
  }
}

function handleReset() {
  step.value = 'idle'
  uploadedFile.value = null
  previewSrc.value = ''
  resultSrc.value = ''
  resultBlob.value = null
  layoutSrc.value = null
  layoutBlob.value = null
  showLayout.value = false
}

function downloadResult() {
  if (!resultSrc.value) return
  const a = document.createElement('a')
  a.href = resultSrc.value
  a.download = `证件照_${cropSizeLabel.value}.png`
  a.click()
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-16">
    <section class="text-center mb-12">
      <h1 class="text-3xl md:text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">
        证件照裁剪
      </h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        在线免费证件照裁剪排版工具。支持1寸/2寸等标准尺寸，自动排版6寸相纸，<span class="text-green-600 font-semibold">完全免费</span>
      </p>
    </section>

    <ImageUploader v-if="step === 'idle'" @file-selected="handleFileSelected" />

    <div v-if="step === 'crop'" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-900">选择裁剪区域</h3>
        <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">重新选择</button>
      </div>

      <div class="flex flex-wrap gap-4 mb-4">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600">模式：</span>
          <button @click="mode = 'auto'" class="px-3 py-1 rounded-lg text-xs font-medium transition"
            :class="mode === 'auto' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'">自动比例</button>
          <button @click="mode = 'manual'" class="px-3 py-1 rounded-lg text-xs font-medium transition"
            :class="mode === 'manual' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'">手动框选</button>
        </div>
        <div v-if="mode === 'auto'" class="flex items-center gap-2">
          <span class="text-sm text-gray-600">规格：</span>
          <select v-model="selectedSpec" class="px-2 py-1 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option v-for="(spec, key) in SPECS" :key="key" :value="key">{{ spec.label }}</option>
          </select>
        </div>
      </div>

      <CropCanvas
        :image-src="previewSrc"
        :aspect-ratio="aspectRatio"
        :lock-ratio="mode === 'auto'"
        @crop-change="handleCropChange"
      />

      <button @click="handleCrop" :disabled="isCropping"
        class="mt-6 w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50">
        <template v-if="isCropping">
          <span class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          裁剪中...
        </template>
        <template v-else>确认裁剪 <ArrowRight class="w-4 h-4" /></template>
      </button>
    </div>

    <div v-if="step === 'done'" class="space-y-6">
      <div class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-900">裁剪结果 - {{ cropSizeLabel }}</h3>
          <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">重新裁剪</button>
        </div>
        <div class="border rounded-lg overflow-hidden bg-gray-100">
          <img :src="resultSrc" class="w-full max-w-sm mx-auto" alt="裁剪结果" />
        </div>
        <div class="mt-4 flex gap-3">
          <button @click="downloadResult"
            class="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2">
            <Download class="w-4 h-4" /> 下载单张
          </button>
          <button @click="handleGenerateLayout" :disabled="isGeneratingLayout || mode === 'manual'"
            class="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
            :title="mode === 'manual' ? '手动模式下不支持排版' : '生成6寸相纸排版'">
            <Grid3X3 class="w-4 h-4" /> 生成排版
          </button>
        </div>
      </div>

      <LayoutPreview
        v-if="showLayout"
        :layout-src="layoutSrc"
        :layout-blob="layoutBlob"
        :is-generating="isGeneratingLayout"
        @back="showLayout = false"
      />
    </div>
  </div>
</template>
```

---

### Task 8: 验证测试

**Files:** 无新文件

- [ ] **Step 1: TypeScript 编译检查**

```bash
cd /Users/evil/Downloads/project/ai-xuqiu-diaoyan/frontend && npx vue-tsc --noEmit 2>&1
```

预期：无错误

- [ ] **Step 2: 后端启动验证**

```bash
curl -s -X POST http://localhost:8000/api/crop -F "file=@/Users/evil/Downloads/生成图片.png" -F "x=0.3" -F "y=0.3" -F "w=0.4" -F "h=0.4" -F "target_w=295" -F "target_h=413" -o /tmp/crop_test.png && /Library/Frameworks/Python.framework/Versions/3.10/bin/python3 -c "
import cv2
img = cv2.imread('/tmp/crop_test.png')
print(f'Cropped size: {img.shape[1]}x{img.shape[0]}')
" 2>&1
```

预期：`Cropped size: 295x413`

- [ ] **Step 3: 排版 API 验证**

```bash
curl -s -X POST http://localhost:8000/api/layout -F "file=@/tmp/crop_test.png" -F "spec=1inch" -o /tmp/layout_test.png && /Library/Frameworks/Python.framework/Versions/3.10/bin/python3 -c "
import cv2
img = cv2.imread('/tmp/layout_test.png')
print(f'Layout size: {img.shape[1]}x{img.shape[0]}')
" 2>&1
```

预期：`Layout size: 1800x1200`

- [ ] **Step 4: 前端页面加载测试**

打开 `http://localhost:5173/crop`，验证：
- 页面正常加载
- Navbar 导航切换正常
- 上传图片后裁剪框出现
- 拖拽裁剪框正常
- 选择不同规格切换正常

---

### Task 9: 清理

- [ ] **Step 1: 删除临时测试文件**

```bash
rm -f /tmp/crop_test.png /tmp/layout_test.png
```