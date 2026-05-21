<script setup lang="ts">
import { ref } from 'vue'
import { useHead } from '@unhead/vue'
import { ArrowRight, Shield, Zap, Download } from 'lucide-vue-next'
import ImageUploader from '@/components/ImageUploader.vue'
import WatermarkMasker from '@/components/WatermarkMasker.vue'
import ResultPreview from '@/components/ResultPreview.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { removeWatermarkManual } from '@/utils/api'

useHead({
  title: 'AI Watermark Remover - Free Online Tool | Remove Watermarks from Photos',
  meta: [
    { name: 'description', content: 'Free online watermark remover. Paint over watermarks with brush tool for precise removal. Supports ID photos, portraits, AI-generated images. Completely free.' },
    { property: 'og:title', content: 'AI Watermark Remover - Free Online Tool | Remove Watermarks from Photos' },
    { property: 'og:description', content: 'Free online watermark remover. Paint over watermarks with brush tool for precise removal. Supports ID photos, portraits, AI-generated images. Completely free.' },
    { property: 'og:url', content: (typeof window !== 'undefined' ? window.location.origin : '') + '/' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: 'AI Watermark Remover - Free Online Tool | Remove Watermarks from Photos' },
    { name: 'twitter:description', content: 'Free online watermark remover. Paint over watermarks with brush tool for precise removal. Completely free.' }
  ],
  link: [
    { rel: 'canonical', href: (typeof window !== 'undefined' ? window.location.origin : '') + '/' }
  ],
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebApplication',
        name: 'AI Watermark Remover',
        description: 'Free online watermark remover. Paint over watermarks with brush tool for precise removal.',
        applicationCategory: 'MultimediaApplication',
        operatingSystem: 'Web',
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
      })
    }
  ]
})

const step = ref<'idle' | 'upload' | 'processing' | 'done'>('idle')
const uploadedFile = ref<File | null>(null)
const originalPreview = ref<string>('')
const resultPreview = ref<string>('')
const resultBlob = ref<Blob | null>(null)
const progress = ref(0)
const processingMessage = ref('')
const error = ref('')
const isProcessing = ref(false)
const maskBlob = ref<Blob | null>(null)

function handleFileSelected(file: File, preview: string) {
  uploadedFile.value = file
  originalPreview.value = preview
  maskBlob.value = null
  step.value = 'upload'
  error.value = ''
}

function handleMaskReady(blob: Blob | null) {
  maskBlob.value = blob
}

async function handleStartRemoval() {
  if (!uploadedFile.value || isProcessing.value) return
  if (!maskBlob.value) {
    error.value = 'Please mark the watermark area with the brush first'
    return
  }

  isProcessing.value = true
  step.value = 'processing'
  progress.value = 5
  processingMessage.value = 'Processing...'
  error.value = ''

  try {
    const blob = await removeWatermarkManual(
      uploadedFile.value,
      maskBlob.value,
      (pct) => { progress.value = Math.round(pct) }
    )
    resultBlob.value = blob
    resultPreview.value = URL.createObjectURL(blob)
    progress.value = 100
    processingMessage.value = 'Done!'
    step.value = 'done'
  } catch (err) {
    console.error('Removal error:', err)
    error.value = 'Processing failed. Please check your connection and try again.'
    processingMessage.value = 'Error'
    progress.value = 0
    setTimeout(() => { step.value = 'upload' }, 2000)
  } finally {
    isProcessing.value = false
  }
}

function handleReset() {
  step.value = 'idle'
  uploadedFile.value = null
  originalPreview.value = ''
  resultPreview.value = ''
  resultBlob.value = null
  maskBlob.value = null
  error.value = ''
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-16">
    <section class="text-center mb-12">
      <h1 class="text-3xl md:text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">
        Watermark Remover
      </h1>
      <p class="text-lg text-gray-600 max-w-2xl mx-auto">
        Professional watermark removal tool. Simply paint over watermarks and remove them instantly, <span class="text-green-600 font-semibold">100% free</span>
      </p>
    </section>

    <ImageUploader
      v-if="step === 'idle'"
      @file-selected="handleFileSelected"
    />

    <div v-if="step === 'upload'" class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-semibold text-gray-900">Manual Brush Removal</h3>
        <button @click="handleReset" class="text-sm text-gray-500 hover:text-gray-700">Select Another</button>
      </div>
      <div class="flex flex-col md:flex-row gap-4">
        <div class="flex-1">
          <img :src="originalPreview" class="w-full rounded-lg border" alt="Original" />
        </div>
        <WatermarkMasker
          :image-src="originalPreview"
          @mask-ready="handleMaskReady"
        />
      </div>
      <button
        @click="handleStartRemoval"
        :disabled="isProcessing"
        class="mt-6 w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <template v-if="isProcessing">
          <span class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
          Processing...
        </template>
        <template v-else>
          Remove Watermark
          <ArrowRight class="w-4 h-4" />
        </template>
      </button>
      <p v-if="error" class="mt-3 text-sm text-red-500 text-center">{{ error }}</p>
    </div>

    <div v-if="step === 'processing'" class="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm text-center">
      <h3 class="text-lg font-semibold text-gray-900 mb-6">Processing your photo</h3>
      <ProgressBar :value="progress" :message="processingMessage" />
      <p class="text-sm text-gray-400 mt-4">Please do not close this page</p>
    </div>

    <ResultPreview
      v-if="step === 'done'"
      :image-src="resultPreview"
      :blob="resultBlob"
      @reset="handleReset"
    />
  </div>

  <section class="bg-white py-16 border-t border-gray-100">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <h2 class="text-2xl font-bold text-gray-900 text-center mb-10">Why Choose Us</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="text-center">
          <Shield class="w-10 h-10 text-blue-500 mx-auto mb-3" />
          <h3 class="font-semibold text-gray-900 mb-2">Privacy Safe</h3>
          <p class="text-sm text-gray-500">Photos processed locally, never uploaded or stored</p>
        </div>
        <div class="text-center">
          <Zap class="w-10 h-10 text-blue-500 mx-auto mb-3" />
          <h3 class="font-semibold text-gray-900 mb-2">Fast Processing</h3>
          <p class="text-sm text-gray-500">Brush to mark, precise and fast watermark removal</p>
        </div>
        <div class="text-center">
          <Download class="w-10 h-10 text-blue-500 mx-auto mb-3" />
          <h3 class="font-semibold text-gray-900 mb-2">HD Output</h3>
          <p class="text-sm text-gray-500">Original quality preserved, no resolution loss</p>
        </div>
      </div>
    </div>
  </section>
</template>