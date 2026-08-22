let unauthorizedHandler: (() => void) | null = null

export function registerUnauthorizedHandler(handler: () => void): void {
  unauthorizedHandler = handler
}

export function resetUnauthorizedHandler(): void {
  unauthorizedHandler = null
}

export function notifyUnauthorized(): void {
  unauthorizedHandler?.()
}
