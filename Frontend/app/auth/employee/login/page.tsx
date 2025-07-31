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



export default function EmployeeLogin() {
  const [formData, setFormData] = useState({
    id: "",
    email: "",
    company: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()
  const { login } = useAuth()
  const router = useRouter()

  // Optional: Timeout wrapper for slow APIs
  const fetchWithTimeout = (url: string, options: RequestInit, timeout = 10000) => {
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

    try {
      const response = await fetchWithTimeout(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/employee/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            id: parseInt(formData.id),
            email: formData.email,
            company: formData.company,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Invalid credentials")
      }

      // ✅ Proceed only on success
      login(data.access_token, {
        id: data.user_id,
        email: formData.email,
        role: "employee",
        company: data.company,
        user_type: "employee",
      })

      toast({
        title: "Login successful",
        description: "Welcome back!",
      })

      router.push("/employee/dashboard")
    } catch (error: any) {
      toast({
        title: "Login failed",
        description: error.message || "Something went wrong. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }





  // const handleSubmit = async (e: React.FormEvent) => {
  //   e.preventDefault()
  //   setIsLoading(true)
  
  //   try {
  //     const response = await fetch(${process.env.NEXT_PUBLIC_API_URL}/auth/employee/login, {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({
  //         id: parseInt(formData.id),
  //         email: formData.email,
  //         company: formData.company,
  //       }),
  //     })
  
  //     const data = await response.json()
  
  //     if (response.ok) {
  //       login(data.access_token, {
  //         id: data.user_id,
  //         email: formData.email,
  //         role: "employee",
  //         company: data.company,
  //         user_type: "employee",
  //       })
  
  //       toast({
  //         title: "Login successful",
  //         description: "Welcome back!",
  //       })
        
  //       router.push("/employee/dashboard")
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
  

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Employee Login</CardTitle>
          <CardDescription className="text-center">Sign in to access your attendance records</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="id">Employee ID</Label>
              <Input
                id="id"
                type="number"
                placeholder="12345"
                value={formData.id}
                onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="employee@company.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                type="text"
                placeholder="Company Name"
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}