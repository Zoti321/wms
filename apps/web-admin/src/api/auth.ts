import { apiClient, requestData } from '@/api/client'
import type { ApiEnvelope, MeData, TokenData } from '@/types/api'

export interface LoginPayload {
  username: string
  password: string
}

export async function login(payload: LoginPayload): Promise<TokenData> {
  return requestData(
    apiClient.post<ApiEnvelope<TokenData>>('/auth/login', payload),
  )
}

export async function fetchMe(): Promise<MeData> {
  return requestData(apiClient.get<ApiEnvelope<MeData>>('/auth/me'))
}
