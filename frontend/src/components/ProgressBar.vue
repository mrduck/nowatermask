<script setup lang="ts">
defineProps<{
  value: number
  message: string
}>()
</script>

<template>
  <div class="max-w-sm mx-auto">
    <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
      <div
        class="h-full bg-blue-500 rounded-full transition-all duration-500 ease-out"
        :style="{ width: `${value}%` }"
      />
    </div>
    <p class="mt-3 text-sm text-gray-600">{{ message }} ({{ value }}%)</p>
  </div>
</template>