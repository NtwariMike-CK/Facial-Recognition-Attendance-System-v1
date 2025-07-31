"use client"

import type React from "react"

import { useRouter } from "next/navigation"


import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { useAuth } from "@/components/auth-provider"
import Link from "next/link"

export default function AdminLogin() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()
  const { login } = useAuth()
  const router = useRouter()


  // Optional timeout for fetch (10s)
  const fetchWithTimeout = (url: string, options: RequestInit, timeout = 100000) => {
    return Promise.race([
      fetch(url, options),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("Request timed out")), timeout)
      ),
    ])
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
  
  //   try {
  //     const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/admin/login`, {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify(formData),
  //     })
  
  //     const data = await response.json()
  
  //     if (response.ok) {
  //       login(data.access_token, {
  //         id: data.user_id,
  //         name: "Admin User",
  //         email: formData.email,
  //         role: "admin",
  //         company: data.company,
  //         user_type: data.user_type,
  //       })
  
  //       toast({
  //         title: "Login successful",
  //         description: "Welcome back!",
  //       })

  //       router.push("/admin/dashboard") // 👈 optional: redirect after registration
  //     } else {
  //       toast({
  //         title: "Login failed",
  //         description: data.detail || "Invalid credentials",
  //         variant: "destructive",
  //       })
  //     }
  //   } catch (error) {
  //     toast({
  //       title: "Error",
  //       description: "Something went wrong. Please try again.",
  //       variant: "destructive",
  //     })
  //   } finally {
  //     setIsLoading(false)
  //   }
  // }


  try {
    const response = await fetchWithTimeout(
      `${process.env.NEXT_PUBLIC_API_URL}/auth/admin/login`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || "Invalid credentials")
    }

    // ✅ Login only on successful response
    login(data.access_token, {
      id: data.user_id,
      name: "Admin User",
      email: formData.email,
      role: "admin",
      company: data.company,
      user_type: data.user_type,
    })

    toast({
      title: "Login successful",
      description: "Welcome back!",
    })

    router.push("/admin/dashboard")
  } catch (error: any) {
    toast({
      title: "Error",
      description: error.message || "Something went wrong. Please try again.",
      variant: "destructive",
    })
  } finally {
    setIsLoading(false)
  }
}
  

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Admin Login</CardTitle>
          <CardDescription className="text-center">Sign in to your admin account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@company.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            {"Don't have an account? "}
            <Link href="/auth/admin/register" className="text-primary hover:underline">
              Register here
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
