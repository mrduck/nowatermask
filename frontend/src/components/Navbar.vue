<script setup lang="ts">
import { Droplets, Scissors, FileDown } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <nav class="bg-white border-b border-gray-100 sticky top-0 z-50">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
      <router-link to="/" class="flex items-center gap-2 font-bold text-lg text-gray-900 hover:text-blue-600 transition-colors">
        <Droplets class="w-5 h-5 text-blue-500" />
        nowatermask.biz
      </router-link>
      <div class="flex items-center gap-1">
        <router-link
          to="/"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          :class="route.path === '/' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
        >
          Watermark
        </router-link>
        <router-link
          to="/crop"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1"
          :class="route.path === '/crop' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
        >
          <Scissors class="w-3.5 h-3.5" />
          ID Photo
        </router-link>
        <router-link
          to="/compress"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1"
          :class="route.path === '/compress' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'"
        >
          <FileDown class="w-3.5 h-3.5" />
          Compress
        </router-link>
      </div>
    </div>
  </nav>
</template>