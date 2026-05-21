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
  a.download = 'id_photo_layout_4x6.png'
  a.click()
}
</script>

<template>
  <div class="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-900">4x6 Photo Paper Layout Preview</h3>
      <button @click="emit('back')" class="text-sm text-gray-500 hover:text-gray-700">Back to Crop</button>
    </div>

    <div v-if="isGenerating" class="py-12 text-center text-gray-500">
      <span class="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2 align-middle"></span>
      Generating layout...
    </div>

    <template v-else-if="layoutSrc">
      <div class="border rounded-lg overflow-hidden bg-gray-100">
        <img :src="layoutSrc" class="w-full" alt="4x6 Layout Preview" />
      </div>
      <p class="mt-3 text-xs text-gray-400 text-center">4x6 photo paper (152×102mm @ 300DPI)</p>
      <button
        @click="downloadLayout"
        class="mt-4 w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition flex items-center justify-center gap-2"
      >
        <Download class="w-4 h-4" />
        Download Layout
      </button>
    </template>
  </div>
</template>