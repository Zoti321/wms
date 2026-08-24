import type { Directive, DirectiveBinding } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { hasAnyPermission, hasPermission } from '@/utils/permission'

function checkPermission(el: HTMLElement, binding: DirectiveBinding<string | string[]>): void {
  const auth = useAuthStore()
  const required = binding.value

  if (!required) {
    el.style.display = ''
    return
  }

  const allowed = Array.isArray(required)
    ? hasAnyPermission(auth.permissions, required)
    : hasPermission(auth.permissions, required)

  el.style.display = allowed ? '' : 'none'
}

export const vPermission: Directive<HTMLElement, string | string[]> = {
  mounted(el, binding) {
    checkPermission(el, binding)
  },
  updated(el, binding) {
    checkPermission(el, binding)
  },
}
