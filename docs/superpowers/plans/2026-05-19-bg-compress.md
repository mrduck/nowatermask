# 背景替换 + 图片压缩 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增"换背景"和"图片压缩"两个独立图像工具

**Architecture:** 两个独立页面分别对应两个后端能力：换背景用rembg抠图+合成背景色，压缩用Pillow重编码，均为独立API端点

**Tech Stack:** Vue 3 + FastAPI + rembg (u2net) + Pillow + onnxruntime

---

### Task 1: 背景移除引擎

**Files:**
- Create: `backend/watermark_engine/bg_remover.py`

这个模块负责AI抠图和背景合成。对外暴露两个方法：`remove_background()` 返回RGBA透明图字节，`replace_background()` 接受图片+背景色hex返回合成图字节。

rembg模型已下载到 `backend/models/`，通过环境变量 `U2NET_HOME` 指定，需要重启后端服务。

- [ ] **Step 1: 创建 bg_remover.py**

```python
import os
import io
import cv2
import numpy as np
from typing import Optional

os.environ.setdefault("U2NET_HOME", os.path.join(os.path.dirname(os.path.dirname(__file__)), "models"))


def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)


def remove_background(image_bytes: bytes) -> bytes:
    from rembg import remove

    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img.shape[1] > 1024:
        scale = 1024 / img.shape[1]
        new_w = 1024
        new_h = int(img.shape[0] * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    rgba = remove(img, alpha_matting=False)
    _, buf = cv2.imencode(".png", rgba)
    return buf.tobytes()


def replace_background(image_bytes: bytes, bg_color_hex: str = "#FFFFFF", download_size: Optional[int] = None) -> bytes:
    from rembg import remove

    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    h, w = img.shape[:2]

    process_img = img
    if max(w, h) > 1024:
        scale = 1024 / max(w, h)
        process_img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    rgba = remove(process_img, alpha_matting=False)
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    alpha = cv2.resize(alpha, (w, h))

    bg_color = _hex_to_bgr(bg_color_hex)
    bg = np.full((h, w, 3), bg_color, dtype=np.uint8)

    alpha_3ch = np.stack([alpha] * 3, axis=-1)
    fg_rgb = cv2.resize(rgba[:, :, :3], (w, h))
    result = (fg_rgb.astype(np.float32) * alpha_3ch + bg.astype(np.float32) * (1 - alpha_3ch))
    result = result.astype(np.uint8)

    if download_size:
        result = cv2.resize(result, (download_size, int(download_size * h / w)), interpolation=cv2.INTER_LANCZOS4)
        result = result[:download_size, :]

    _, buf = cv2.imencode(".png", result)
    return buf.tobytes()
```

---

### Task 2: 后端新增 3 个 API 端点

**Files:**
- Modify: `backend/main.py`

在现有端点后追加三个新端点：`/api/remove-bg`（抠图返回透明PNG）、`/api/replace-bg`（抠图+合成背景色）、`/api/compress`（压缩/转格式）。

- [ ] **Step 1: 在 main.py 末尾添加 3 个新端点**

在 `backend/main.py` 末尾（layout 端点之后）追加以下代码：

```python
from watermark_engine.bg_remover import remove_background, replace_background


@app.post("/api/remove-bg")
async def remove_bg(file: UploadFile = File(...)):
    contents = await file.read()
    result_bytes = remove_background(contents)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/replace-bg")
async def replace_bg(
    file: UploadFile = File(...),
    bg_color: str = "FFFFFF",
    download_size: int = 0
):
    contents = await file.read()
    bg_hex = f"#{bg_color}" if not bg_color.startswith("#") else bg_color
    kwargs = {}
    if download_size > 0:
        kwargs["download_size"] = download_size
    result_bytes = replace_background(contents, bg_hex, **kwargs)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/compress")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = 75,
    fmt: str = "jpeg"
):
    from PIL import Image

    contents = await file.read()
    img = Image.open(io.BytesIO(contents))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    out = io.BytesIO()
    save_fmt = "JPEG" if fmt.lower() in ("jpeg", "jpg") else fmt.upper()
    save_kwargs = {}
    if save_fmt == "JPEG":
        save_kwargs = {"quality": quality, "optimize": True}
    elif save_fmt == "PNG":
        save_kwargs = {"optimize": True}
    elif save_fmt == "WEBP":
        save_kwargs = {"quality": quality}

    img.save(out, format=save_fmt, **save_kwargs)
    out.seek(0)

    mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    return StreamingResponse(out, media_type=mime.get(save_fmt, "image/jpeg"))
```

- [ ] **Step 2: 添加 rembg 依赖到 requirements.txt**

在 `backend/requirements.txt` 末尾追加一行：

```
rembg==2.0.75
onnxruntime==1.23.2
```

---

### Task 3: 前端 API 函数

**Files:**
- Modify: `frontend/src/utils/api.ts`

在现有 api.ts 末尾追加三个新的 API 调用函数。

- [ ] **Step 1: 追加 API 函数**

```typescript
export async function removeBackground(file: File): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch('/api/remove-bg', { method: 'POST', body: formData })
  return res.blob()
}

export async function replaceBackground(file: File, bgColor: string, downloadSize: number = 0): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('bg_color', bgColor)
  if (downloadSize > 0) {
    formData.append('download_size', String(downloadSize))
  }
  const res = await fetch('/api/replace-bg', { method: 'POST', body: formData })
  return res.blob()
}

export async function compressImage(file: File, quality: number, format: string): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('quality', String(quality))
  formData.append('fmt', format)
  const res = await fetch('/api/compress', { method: 'POST', body: formData })
  return res.blob()
}
```

---

### Task 4: 前端路由 + 导航栏

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/Navbar.vue`

新增 `/bg` 和 `/compress` 路由，导航栏新增"换背景"和"图片压缩"入口。

- [ ] **Step 1: 更新路由**

将 `router/index.ts` 改为：

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import CropPage from '@/pages/CropPage.vue'
import BgReplacePage from '@/pages/BgReplacePage.vue'
import CompressPage from '@/pages/CompressPage.vue'

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
    },
    {
      path: '/bg',
      name: 'bg',
      component: BgReplacePage
    },
    {
      path: '/compress',
      name: 'compress',
      component: CompressPage
    }
  ]
})

export default router
```

- [ ] **Step 2: 更新导航栏**

将 `Navbar.vue` 的 script 导入增加图标：

```typescript
import { Droplets, Scissors, ImagePlus, FileDown } from 'lucide-vue-next'
```

在导航链接区域（第二个 `router-link` 之后，`</div>` 之前）追加两个链接：

```html
<router-link
  to="/bg"
  class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1"
  :class="route.path === '/bg' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
>
  <ImagePlus class="w-3.5 h-3.5" />
  换背景
</router-link>
<router-link
  to="/compress"
  class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1"
  :class="route.path === '/compress' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
>
  <FileDown class="w-3.5 h-3.5" />
  图片压缩
</router-link>
```

---

### Task 5: 换背景页面 BgReplacePage.vue

**Files:**
- Create: `frontend/src/pages/BgReplacePage.vue`

完整页面：上传 → AI抠图(loading) → 背景色选择器 → 原图/结果对比 → 下载。

状态机：`idle → processing → done`

- [ ] **Step 1: 创建 BgReplacePage.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useHead } from '@unhead/vue'
import { Download, Palette } from 'lucide-vue-next'
import ImageUploader from '@/components/ImageUploader.vue'
import { replaceBackground } from '@/utils/api'

useHead({
  title: 'AI换背景 - 在线免费证件照换背景工具 | 白底蓝底红底',
  meta: [
    { name: 'description', content: '免费在线AI换背景工具，自动抠图替换背景色。支持白色、蓝色、红色等证件照标准背景，完全免费。' }
  ]
})

const PRESET_COLORS = [
  { label: '白色', hex: 'FFFFFF' },
  { label: '蓝色', hex: '438EDB' },
  { label: '红色', hex: 'FF0000' },
  { label: '自定义', hex: '' },
]

const step = ref<'idle' | 'processing' | 'done'>('idle')
const uploadedFile = ref<File | null>(null)
const previewSrc = ref('')
const resultSrc = ref('')
const resultBlob = ref<Blob | null>(null)
const selectedColor = ref('FFFFFF')
const customColor = ref('438EDB')
const colorMode = ref<'preset' | 'custom'>('preset')

const displayHex = ref('FFFFFF')

function handleFileSelected(file: File, preview: string) {
  uploadedFile.value = file
  previewSrc.value = preview
  step.value = 'processing'
  processBg()
}

async function processBg() {
  if (!uploadedFile.value) return

  const bgColor = colorMode.value === 'preset' && selectedColor.value
    ? selectedColor.value
    : customColor.value

  displayHex.value = bgColor

  resultSrc.value = ''
  const blob = await replaceBackground(uploadedFile.value, bgColor)
  resultBlob.value = blob
  resultSrc.value = URL.createObjectURL(blob)
  step.value = 'done'
}

function selectPreset(hex: string) {
  if (!hex) {
    colorMode.value = 'custom'
    return
  }
  colorMode.value = 'preset'
  selectedColor.value = hex
  processBg()
}

function applyCustomColor() {
  colorMode.value = 'custom'
  processBg()
}

function handleReset() {
  step.value = 'idle'
  uploadedFile.value = null
  previewSrc.value = ''
  resultSrc.value = ''
  resultBlob.value = null
}

function downloadResult() {
  if (!resultSrc.value) return
  const a = document.createElement('a')
  a.href = resultSrc.value
  a.download = `换背景_${displayHex.value}.png`
  a.click()
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-16">
    <section class="text-center mb-12">
      <h1 class="text-3xl md:text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">
        AI 换背景
      </h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        上传照片自动抠图，一键替换白底/蓝底/红底，<span class="text-green-600 font-semibold">完全免费</span>
      </p>
    </section>

    <ImageUploader v-if="step === 'idle'" @file-selected="handleFileSelected" />

    <div v-if="step === 'processing'" class="bg-white rounded-2xl border border-gray-200 p-12 shadow-sm text-center">
      <div class="animate-spin inline-block w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full mb-4"></div>
      <p class="text-gray-600 text-lg">AI 正在识别和抠图...</p>
      <p class="text-sm text-gray-400 mt-2">处理时间约 3-10 秒</p>
    </div>

    <div v-if="step === 'done'" class="space-y-6">
      <div class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-900">选择背景颜色</h3>
          <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">重新上传</button>
        </div>

        <div class="flex flex-wrap gap-3 mb-4">
          <button
            v-for="c in PRESET_COLORS"
            :key="c.label"
            @click="selectPreset(c.hex)"
            class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border-2 transition"
            :class="(colorMode === 'preset' && selectedColor === c.hex) || (!c.hex && colorMode === 'custom')
              ? 'border-blue-500 bg-blue-50 text-blue-700'
              : 'border-gray-200 text-gray-600 hover:border-gray-300'"
          >
            <template v-if="c.hex">
              <span class="w-5 h-5 rounded-full border border-gray-300" :style="{ background: '#' + c.hex }"></span>
              {{ c.label }}
            </template>
            <template v-else>
              <Palette class="w-4 h-4" />
              自定义
            </template>
          </button>
        </div>

        <div v-if="colorMode === 'custom'" class="flex items-center gap-3 mb-4">
          <span class="text-sm text-gray-600">#</span>
          <input
            v-model="customColor"
            maxlength="6"
            class="w-24 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono uppercase"
          />
          <button
            @click="applyCustomColor"
            class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition"
          >
            应用
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
          <p class="text-sm font-medium text-gray-500 mb-2">原图</p>
          <div class="border rounded-lg overflow-hidden bg-gray-100 flex justify-center">
            <img :src="previewSrc" class="max-h-80 object-contain" alt="原图" />
          </div>
        </div>
        <div class="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
          <p class="text-sm font-medium text-gray-500 mb-2">结果</p>
          <div class="border rounded-lg overflow-hidden flex justify-center" :style="{ background: '#' + displayHex }">
            <img :src="resultSrc" class="max-h-80 object-contain" alt="换背景结果" />
          </div>
        </div>
      </div>

      <button
        @click="downloadResult"
        class="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
      >
        <Download class="w-4 h-4" />
        下载图片
      </button>
    </div>
  </div>
</template>
```

---

### Task 6: 压缩页面 CompressPage.vue

**Files:**
- Create: `frontend/src/pages/CompressPage.vue`

完整页面：上传 → 质量滑块 → 格式选择 → 原图/压缩图对比 + 体积信息 → 下载。

- [ ] **Step 1: 创建 CompressPage.vue**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useHead } from '@unhead/vue'
import { Download, FileImage } from 'lucide-vue-next'
import ImageUploader from '@/components/ImageUploader.vue'
import { compressImage } from '@/utils/api'

useHead({
  title: '图片压缩 - 在线免费图片压缩工具 | PNG/JPG/WebP',
  meta: [
    { name: 'description', content: '免费在线图片压缩工具，支持PNG/JPG/WebP格式互转。拖拽调整压缩质量，实时预览效果和体积变化。完全免费。' }
  ]
})

const FORMATS = [
  { value: 'jpeg', label: 'JPEG' },
  { value: 'png', label: 'PNG' },
  { value: 'webp', label: 'WebP' },
]

const step = ref<'idle' | 'ready' | 'done'>('idle')
const uploadedFile = ref<File | null>(null)
const previewSrc = ref('')
const resultSrc = ref('')
const resultBlob = ref<Blob | null>(null)
const quality = ref(75)
const format = ref('jpeg')
const isCompressing = ref(false)
const originalSize = ref(0)
const compressedSize = ref(0)

const compressionRatio = ref(0)

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function handleFileSelected(file: File, preview: string) {
  uploadedFile.value = file
  originalSize.value = file.size
  previewSrc.value = preview
  step.value = 'ready'
  doCompress()
}

async function doCompress() {
  if (!uploadedFile.value || isCompressing.value) return
  isCompressing.value = true
  try {
    const blob = await compressImage(uploadedFile.value, quality.value, format.value)
    resultBlob.value = blob
    compressedSize.value = blob.size
    if (uploadedFile.value) {
      compressionRatio.value = Math.round((1 - blob.size / uploadedFile.value.size) * 100)
    }
    resultSrc.value = URL.createObjectURL(blob)
    step.value = 'done'
  } finally {
    isCompressing.value = false
  }
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
watch([quality, format], () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    if (uploadedFile.value) doCompress()
  }, 300)
})

function handleReset() {
  step.value = 'idle'
  uploadedFile.value = null
  previewSrc.value = ''
  resultSrc.value = ''
  resultBlob.value = null
  quality.value = 75
}

function downloadResult() {
  if (!resultSrc.value) return
  const a = document.createElement('a')
  a.href = resultSrc.value
  const ext = format.value === 'jpeg' ? 'jpg' : format.value
  a.download = `compressed.${ext}`
  a.click()
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-16">
    <section class="text-center mb-12">
      <h1 class="text-3xl md:text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">
        图片压缩
      </h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        在线压缩图片体积，支持JPEG/PNG/WebP格式互转，<span class="text-green-600 font-semibold">完全免费</span>
      </p>
    </section>

    <ImageUploader v-if="step === 'idle'" @file-selected="handleFileSelected" />

    <div v-if="step === 'ready' || step === 'done'" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-900">压缩设置</h3>
        <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">重新上传</button>
      </div>

      <div class="space-y-4 mb-6">
        <div>
          <label class="text-sm text-gray-600 block mb-1">输出格式</label>
          <div class="flex gap-2">
            <button
              v-for="f in FORMATS"
              :key="f.value"
              @click="format = f.value"
              class="px-4 py-2 rounded-lg text-sm font-medium border transition"
              :class="format === f.value
                ? 'bg-blue-50 border-blue-500 text-blue-700'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'"
            >
              {{ f.label }}
            </button>
          </div>
        </div>

        <div v-if="format === 'jpeg' || format === 'webp'">
          <label class="text-sm text-gray-600 block mb-1">
            压缩质量：<span class="font-semibold">{{ quality }}%</span>
          </label>
          <input
            type="range"
            min="1"
            max="100"
            v-model="quality"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div class="flex justify-between text-xs text-gray-400 mt-1">
            <span>高压缩</span>
            <span>高质量</span>
          </div>
        </div>
      </div>

      <div v-if="step === 'done'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-sm font-medium text-gray-500 mb-2">原图</p>
          <div class="border rounded-lg overflow-hidden bg-gray-100 flex justify-center">
            <img :src="previewSrc" class="max-h-64 object-contain" alt="原图" />
          </div>
          <p class="text-xs text-gray-400 mt-2">{{ formatSize(originalSize) }}</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-sm font-medium text-gray-500 mb-2">压缩后</p>
          <div class="border rounded-lg overflow-hidden bg-gray-100 flex justify-center">
            <img :src="resultSrc" class="max-h-64 object-contain" alt="压缩后" />
          </div>
          <div class="flex items-center gap-2 mt-2">
            <p class="text-xs text-gray-400">{{ formatSize(compressedSize) }}</p>
            <span class="text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded">
              -{{ compressionRatio }}%
            </span>
            <FileImage class="w-3 h-3 text-green-500" />
          </div>
        </div>
      </div>

      <button
        v-if="step === 'done'"
        @click="downloadResult"
        class="mt-6 w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
      >
        <Download class="w-4 h-4" />
        下载压缩图片
      </button>
    </div>
  </div>
</template>
```

---

### Task 7: 验证测试

**Files:**
- 无新建文件

- [ ] **Step 1: 检查 TypeScript 编译**

```bash
cd frontend && npx vue-tsc --noEmit
```
预期：exit code 0，无错误输出

- [ ] **Step 2: 测试背景移除 API**

```bash
curl -s -X POST http://localhost:8000/api/remove-bg \
  -F "file=@/Users/evil/Downloads/生成图片.png" \
  -o /tmp/bg_test.png
python3 -c "from PIL import Image; img=Image.open('/tmp/bg_test.png'); print(f'remove-bg: {img.size}, mode={img.mode}')"
```
预期：输出 RGBA 图片（mode=RGBA）

- [ ] **Step 3: 测试背景替换 API**

```bash
curl -s -X POST http://localhost:8000/api/replace-bg \
  -F "file=@/Users/evil/Downloads/生成图片.png" \
  -F "bg_color=438EDB" \
  -o /tmp/rbg_test.png
python3 -c "from PIL import Image; img=Image.open('/tmp/rbg_test.png'); print(f'replace-bg: {img.size}, mode={img.mode}')"
```
预期：输出 RGB 图片（蓝色背景）

- [ ] **Step 4: 测试压缩 API**

```bash
curl -s -X POST http://localhost:8000/api/compress \
  -F "file=@/Users/evil/Downloads/生成图片.png" \
  -F "quality=30" \
  -F "fmt=jpeg" \
  -o /tmp/compress_test.jpg
python3 -c "from PIL import Image; import os; img=Image.open('/tmp/compress_test.jpg'); print(f'compress: {img.size}, size={os.path.getsize(\"/tmp/compress_test.jpg\")}b')"
```
预期：成功输出 JPEG

- [ ] **Step 5: 打开前端验证**

打开 `http://localhost:5173/bg` 和 `http://localhost:5173/compress`，确认页面加载无报错

- [ ] **Step 6: 清理临时文件**

```bash
rm -f /tmp/bg_test.png /tmp/rbg_test.png /tmp/compress_test.jpg
```