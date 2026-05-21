import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import CropPage from '@/pages/CropPage.vue'
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
      path: '/compress',
      name: 'compress',
      component: CompressPage
    }
  ]
})

export default router