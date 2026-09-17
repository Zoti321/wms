import { requestData } from '@/api/client'
import type { LoginRequest, MeData, TokenData } from '@/types/api'

export async function login(payload: LoginRequest): Promise<TokenData> {
  return requestData<TokenData>('/auth/login', {
    method: 'POST',
    data: payload,
    auth: false,
  })
}

export async function fetchMe(): Promise<MeData> {
  return requestData<MeData>('/auth/me')
}
