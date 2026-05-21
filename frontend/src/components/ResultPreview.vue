<script setup lang="ts">
import { Download, RefreshCw, Share2 } from 'lucide-vue-next'

const props = defineProps<{
  imageSrc: string
  blob?: Blob | null
}>()

const emit = defineEmits<{
  (e: 'reset'): void
}>()

function downloadImage() {
  const a = document.createElement('a')
  a.href = props.imageSrc
  a.download = 'watermark_free_photo.png'
  a.click()
}
</script>

<template>
  <div class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm text-center">
    <h3 class="text-lg font-semibold text-green-600 mb-4">✅ Done!</h3>
    <div class="max-w-md mx-auto mb-6">
      <img :src="imageSrc" class="w-full rounded-lg shadow-md" alt="Result" />
    </div>
    <div class="flex items-center justify-center gap-3">
      <button
        @click="downloadImage"
        class="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
      >
        <Download class="w-4 h-4" />
        Download Photo
      </button>
      <button
        @click="emit('reset')"
        class="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors flex items-center gap-2"
      >
        <RefreshCw class="w-4 h-4" />
        Process Another
      </button>
    </div>
    <p class="text-xs text-gray-400 mt-4">
      Only use this tool for photos you own or have permission to use
    </p>
  </div>
</template>