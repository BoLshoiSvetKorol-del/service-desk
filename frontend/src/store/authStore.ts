import { create } from 'zustand'
import { User } from '../types/user'
import { setAuthTokens as _setTokens, clearAuthTokens } from '../api/client'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  login: (user: User, accessToken: string, refreshToken: string) => void
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login(user, accessToken, refreshToken) {
    _setTokens(accessToken, refreshToken)
    set({ user, isAuthenticated: true })
  },

  logout() {
    clearAuthTokens()
    set({ user: null, isAuthenticated: false })
  },

  setUser(user) {
    set({ user })
  },
}))
