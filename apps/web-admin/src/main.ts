import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import { registerUnauthorizedHandler } from '@/api/unauthorized'
import { vPermission } from '@/directives/permission'
import router from '@/router'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import 'element-plus/dist/index.css'
import '@/styles/global.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.directive('permission', vPermission)

registerUnauthorizedHandler(() => {
  useAuthStore(pinia).logout()
  useAppStore(pinia).clearWarehouse()
  if (router.currentRoute.value.name !== ROUTE_NAMES.login) {
    void router.push({ name: ROUTE_NAMES.login })
  }
})

app.mount('#app')
