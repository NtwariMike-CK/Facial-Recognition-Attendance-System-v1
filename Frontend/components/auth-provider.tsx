"use client"

import type React from "react"

import { createContext, useContext, useEffect, useState } from "react"
import { useRouter } from "next/navigation"

interface User {
  id: number
  name?: string
  email: string
  role: string
  company: string
  user_type: "admin" | "employee"
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const storedToken = localStorage.getItem("fras_token")
    const storedUser = localStorage.getItem("fras_user")

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser)
        setToken(storedToken)
        setUser(parsedUser)
      } catch (error) {
        localStorage.removeItem("fras_token")
        localStorage.removeItem("fras_user")
      }
    }
    setIsLoading(false)
  }, [])

  const login = (newToken: string, newUser: User) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem("fras_token", newToken)
    localStorage.setItem("fras_user", JSON.stringify(newUser))

    // Redirect based on user type
    if (newUser.user_type === "admin") {
      router.push("/admin/dashboard")
    } else {
      router.push("/employee/dashboard")
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem("fras_token")
    localStorage.removeItem("fras_user")
    router.push("/")
  }

  return <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
