"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/auth-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Users, Shield, Camera, BarChart3 } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && user) {
      if (user.user_type === "admin") {
        router.push("/admin/dashboard")
      } else {
        router.push("/employee/dashboard")
      }
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">FRAS</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">Facial Recognition Attendance System</p>
          <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
            Advanced attendance tracking system using cutting-edge facial recognition technology
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Card className="text-center">
            <CardHeader>
              <Camera className="h-12 w-12 mx-auto text-blue-600" />
              <CardTitle>Facial Recognition</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Advanced AI-powered facial recognition for accurate attendance tracking</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <BarChart3 className="h-12 w-12 mx-auto text-green-600" />
              <CardTitle>Real-time Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Comprehensive dashboards with real-time attendance analytics</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Users className="h-12 w-12 mx-auto text-purple-600" />
              <CardTitle>Employee Management</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Complete employee management system with role-based access</CardDescription>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <Shield className="h-12 w-12 mx-auto text-red-600" />
              <CardTitle>Secure & Reliable</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Enterprise-grade security with reliable attendance tracking</CardDescription>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-center space-x-4">
          <Link href="/auth/admin/login">
            <Button size="lg" className="px-8">
              Admin Login
            </Button>
          </Link>
          <Link href="/auth/employee/login">
            <Button variant="outline" size="lg" className="px-8 bg-transparent">
              Employee Login
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
