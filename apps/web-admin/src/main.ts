import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import { vPermission } from '@/directives/permission'
import router from '@/router'
import 'element-plus/dist/index.css'
import '@/styles/global.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.directive('permission', vPermission)

app.mount('#app')
