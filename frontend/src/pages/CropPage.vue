<script setup lang="ts">
import { ref, computed } from 'vue'
import { useHead } from '@unhead/vue'
import { Download, ArrowRight, Grid3X3 } from 'lucide-vue-next'
import ImageUploader from '@/components/ImageUploader.vue'
import CropCanvas from '@/components/CropCanvas.vue'
import LayoutPreview from '@/components/LayoutPreview.vue'
import { cropPhoto, generateLayout } from '@/utils/api'

useHead({
  title: 'ID Photo Crop - Free Online Photo Cropping & Layout Tool | 1in 2in Standard Sizes',
  meta: [
    { name: 'description', content: 'Free online ID photo cropping tool supporting 1-inch, 2-inch and other standard sizes. Manual or auto aspect-ratio crop, generate 4x6 photo paper layout. Completely free.' },
    { property: 'og:title', content: 'ID Photo Crop - Free Online Photo Cropping & Layout Tool | 1in 2in Standard Sizes' },
    { property: 'og:description', content: 'Free online ID photo cropping tool supporting 1-inch, 2-inch and other standard sizes. Manual or auto aspect-ratio crop, generate 4x6 photo paper layout. Completely free.' },
    { property: 'og:url', content: (typeof window !== 'undefined' ? window.location.origin : '') + '/crop' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: 'ID Photo Crop - Free Online Photo Cropping & Layout Tool' },
    { name: 'twitter:description', content: 'Free online ID photo cropping tool. Manual or auto aspect-ratio crop, generate 4x6 photo paper layout. Completely free.' }
  ],
  link: [
    { rel: 'canonical', href: (typeof window !== 'undefined' ? window.location.origin : '') + '/crop' }
  ],
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        name: 'ID Photo Crop Tool',
        description: 'Free online ID photo cropping tool supporting 1-inch, 2-inch and other standard sizes.',
        applicationCategory: 'MultimediaApplication',
        operatingSystem: 'Web',
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
      })
    }
  ]
})

const SPECS: Record<string, { w: number; h: number; label: string }> = {
  '1inch': { w: 295, h: 413, label: '1 inch' },
  's1inch': { w: 260, h: 378, label: 'Small 1 inch' },
  '2inch': { w: 413, h: 579, label: '2 inch' },
  's2inch': { w: 413, h: 531, label: 'Small 2 inch' },
  'big1inch': { w: 390, h: 567, label: 'Large 1 inch' },
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
  a.download = `id_photo_${cropSizeLabel.value}.png`
  a.click()
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-16">
    <section class="text-center mb-12">
      <h1 class="text-3xl md:text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">
        ID Photo Crop
      </h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        Free online ID photo crop & layout tool. Supports 1in/2in standard sizes, auto 4x6 photo paper layout, <span class="text-green-600 font-semibold">100% free</span>
      </p>
    </section>

    <ImageUploader v-if="step === 'idle'" @file-selected="handleFileSelected" />

    <div v-if="step === 'crop'" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-900">Select Crop Area</h3>
        <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">Select Another</button>
      </div>

      <div class="flex flex-wrap gap-4 mb-4">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600">Mode:</span>
          <button
            @click="mode = 'auto'"
            class="px-3 py-1 rounded-lg text-xs font-medium transition"
            :class="mode === 'auto' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'"
          >
            Auto Ratio
          </button>
          <button
            @click="mode = 'manual'"
            class="px-3 py-1 rounded-lg text-xs font-medium transition"
            :class="mode === 'manual' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'"
          >
            Manual
          </button>
        </div>
        <div v-if="mode === 'auto'" class="flex items-center gap-2">
          <span class="text-sm text-gray-600">Size:</span>
          <select
            v-model="selectedSpec"
            class="px-2 py-1 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
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

      <button
        @click="handleCrop"
        :disabled="isCropping"
        class="mt-6 w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <template v-if="isCropping">
          <span class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          Cropping...
        </template>
        <template v-else>
          Crop
          <ArrowRight class="w-4 h-4" />
        </template>
      </button>
    </div>

    <div v-if="step === 'done'" class="space-y-6">
      <div class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-900">Crop Result - {{ cropSizeLabel }}</h3>
          <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">Recrop</button>
        </div>
        <div class="border rounded-lg overflow-hidden bg-gray-100 flex justify-center">
          <img :src="resultSrc" class="max-w-sm" alt="Cropped result" />
        </div>
        <div class="mt-4 flex gap-3">
          <button
            @click="downloadResult"
            class="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2"
          >
            <Download class="w-4 h-4" />
            Download Single
          </button>
          <button
            @click="handleGenerateLayout"
            :disabled="isGeneratingLayout || mode === 'manual'"
            class="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
            :title="mode === 'manual' ? 'Manual mode does not support layout' : 'Generate Layout'"
          >
            <Grid3X3 class="w-4 h-4" />
            Generate Layout
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