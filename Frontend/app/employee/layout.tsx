"use client"

import type React from "react"

import { useAuth } from "@/components/auth-provider"
import { LayoutWrapper } from "@/components/layout-wrapper"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function EmployeeLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && (!user || user.user_type !== "employee")) {
      router.push("/auth/employee/login")
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!user || user.user_type !== "employee") {
    return null
  }

  return <LayoutWrapper userType="employee">{children}</LayoutWrapper>
}
