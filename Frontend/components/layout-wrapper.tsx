"use client"

import type React from "react"

import { useAuth } from "@/components/auth-provider"
import { Sidebar } from "@/components/sidebar"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface LayoutWrapperProps {
  children: React.ReactNode
  userType: "admin" | "employee"
}

export function LayoutWrapper({ children, userType }: LayoutWrapperProps) {
  const { user } = useAuth()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar userType={userType} onCollapseChange={setSidebarCollapsed} />
      <main className={cn("transition-all duration-300", sidebarCollapsed ? "ml-16" : "ml-64")}>
        <div className="p-6 pt-16">{children}</div>
      </main>
    </div>
  )
}
