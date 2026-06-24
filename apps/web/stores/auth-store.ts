/**
 * Authentication State Store
 *
 * Zustand store for managing auth state including:
 * - User session
 * - Token management
 * - Login/logout operations
 */

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

// User interface
export interface User {
  id: string
  email: string
  name?: string
  role?: string
  is_superuser?: boolean
}

// Auth state interface
interface AuthStore {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean

  // Actions
  login: (user: User, token: string) => void
  logout: () => void
  setToken: (token: string | null) => void
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  clearAuth: () => void
}

// Create auth store
export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false,

        // Login user
        login: (user, token) =>
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          }),

        // Logout user
        logout: () => {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        },

        // Set token
        setToken: (token) =>
          set({
            token,
            isAuthenticated: !!token,
          }),

        // Set user
        setUser: (user) =>
          set({
            user,
            isAuthenticated: !!user,
          }),

        // Set loading state
        setLoading: (loading) => set({ isLoading: loading }),

        // Clear all auth data
        clearAuth: () =>
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          }),
      }),
      {
        name: 'auth-store',
        partialize: (state) => ({
          user: state.user,
          token: state.token,
        }),
        version: 1,
      },
    ),
    {
      enabled: process.env.NODE_ENV === 'development',
    },
  ),
)

// Check if user is authenticated
export function isAuthenticated(): boolean {
  const auth = useAuthStore.getState()
  return auth.isAuthenticated
}

// Get current user
export function getCurrentUser(): User | null {
  return useAuthStore.getState().user
}

// Get current token
export function getCurrentToken(): string | null {
  return useAuthStore.getState().token
}

// Sign out
export function signOut(): void {
  useAuthStore.getState().logout()
}
