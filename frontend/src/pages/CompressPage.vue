<script setup lang="ts">
import { ref, watch } from 'vue'
import { useHead } from '@unhead/vue'
import { Download, FileImage } from 'lucide-vue-next'
import ImageUploader from '@/components/ImageUploader.vue'
import { compressImage } from '@/utils/api'

useHead({
  title: 'Image Compressor - Free Online Image Compression | PNG/JPG/WebP',
  meta: [
    { name: 'description', content: 'Free online image compression tool. Supports PNG/JPG/WebP format conversion. Adjust quality with slider, real-time preview and size comparison. 100% free.' },
    { property: 'og:title', content: 'Image Compressor - Free Online Image Compression | PNG/JPG/WebP' },
    { property: 'og:description', content: 'Free online image compression tool. Supports PNG/JPG/WebP format conversion. Adjust quality with slider, real-time preview and size comparison.' },
    { property: 'og:url', content: (typeof window !== 'undefined' ? window.location.origin : '') + '/compress' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: 'Image Compressor - Free Online Image Compression' },
    { name: 'twitter:description', content: 'Free online image compression tool. Supports PNG/JPG/WebP format conversion. Real-time preview. 100% free.' }
  ],
  link: [
    { rel: 'canonical', href: (typeof window !== 'undefined' ? window.location.origin : '') + '/compress' }
  ],
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        name: 'Image Compressor',
        description: 'Free online image compression tool. Supports PNG/JPG/WebP format conversion.',
        applicationCategory: 'MultimediaApplication',
        operatingSystem: 'Web',
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
      })
    }
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
        Image Compressor
      </h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        Compress images online. Supports JPEG/PNG/WebP conversion, <span class="text-green-600 font-semibold">100% free</span>
      </p>
    </section>

    <ImageUploader v-if="step === 'idle'" @file-selected="handleFileSelected" />

    <div v-if="step === 'ready' || step === 'done'" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-900">Compression Settings</h3>
        <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">Upload New</button>
      </div>

      <div class="space-y-4 mb-6">
        <div>
          <label class="text-sm text-gray-600 block mb-1">Output Format</label>
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
            Quality: <span class="font-semibold">{{ quality }}%</span>
          </label>
          <input
            type="range"
            min="1"
            max="100"
            v-model="quality"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div class="flex justify-between text-xs text-gray-400 mt-1">
            <span>High Compression</span>
            <span>High Quality</span>
          </div>
        </div>
      </div>

      <div v-if="step === 'done'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-sm font-medium text-gray-500 mb-2">Original</p>
          <div class="border rounded-lg overflow-hidden bg-gray-100 flex justify-center">
            <img :src="previewSrc" class="max-h-64 object-contain" alt="Original" />
          </div>
          <p class="text-xs text-gray-400 mt-2">{{ formatSize(originalSize) }}</p>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-4">
          <p class="text-sm font-medium text-gray-500 mb-2">Compressed</p>
          <div class="border rounded-lg overflow-hidden bg-gray-100 flex justify-center">
            <img :src="resultSrc" class="max-h-64 object-contain" alt="Compressed" />
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
        Download Compressed Image
      </button>
    </div>
  </div>
</template>