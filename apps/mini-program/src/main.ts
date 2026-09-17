import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { setUnauthorizedHandler } from '@/api/client'
import { clearAccessToken } from '@/utils/tokenStorage'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)

  setUnauthorizedHandler(() => {
    clearAccessToken()
    uni.reLaunch({ url: '/pages/login/login' })
  })

  return { app }
}
