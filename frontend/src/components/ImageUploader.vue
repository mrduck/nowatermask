<script setup lang="ts">
import { ref } from 'vue'
import { Upload, Image } from 'lucide-vue-next'

const emit = defineEmits<{
  (e: 'file-selected', file: File, preview: string): void
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const previewSrc = ref('')

function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) processFile(file)
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) processFile(file)
}

function processFile(file: File) {
  if (!file.type.startsWith('image/')) return
  const reader = new FileReader()
  reader.onload = () => {
    previewSrc.value = reader.result as string
    emit('file-selected', file, previewSrc.value)
  }
  reader.readAsDataURL(file)
}

function triggerUpload() {
  fileInput.value?.click()
}
</script>

<template>
  <div class="bg-white rounded-2xl border-2 border-dashed p-8 md:p-12 mt-6 shadow-sm transition-all"
    :class="isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-300'"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      class="hidden"
      @change="onFileChange"
    />
    <div class="text-center">
      <div v-if="!previewSrc">
        <Upload class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p class="text-gray-700 font-medium mb-1">Drag & drop your photo here, or click to upload</p>
        <p class="text-sm text-gray-400">Supports JPG / PNG / WebP, up to 20MB</p>
        <button
          @click="triggerUpload"
          class="mt-4 px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          Select Photo
        </button>
      </div>
      <div v-else class="flex flex-col items-center">
        <Image class="w-8 h-8 text-green-500 mb-2" />
        <p class="text-green-600 font-medium">Ready</p>
      </div>
    </div>
  </div>
</template>