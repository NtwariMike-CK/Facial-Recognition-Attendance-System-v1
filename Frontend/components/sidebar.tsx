"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/components/auth-provider"
import { LayoutDashboard, Users, Camera, Ticket, Settings, LogOut, ChevronLeft, ChevronRight } from "lucide-react"

interface SidebarProps {
  userType: "admin" | "employee"
  onCollapseChange?: (collapsed: boolean) => void
}

export function Sidebar({ userType, onCollapseChange }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()
  const { logout, user } = useAuth()

  const adminNavItems = [
    { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/admin/employees", label: "User Management", icon: Users },
    { href: "/admin/camera", label: "Camera Settings", icon: Camera },
    { href: "/admin/tickets", label: "Tickets", icon: Ticket },
    { href: "/admin/settings", label: "Settings", icon: Settings },
  ]

  const employeeNavItems = [
    { href: "/employee/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/employee/tickets", label: "Tickets", icon: Ticket },
  ]

  const navItems = userType === "admin" ? adminNavItems : employeeNavItems

  const handleToggle = () => {
    const newCollapsed = !isCollapsed
    setIsCollapsed(newCollapsed)
    onCollapseChange?.(newCollapsed)
  }

  return (
    <>
      {/* Toggle button - always visible */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 bg-background border shadow-md"
        onClick={handleToggle}
      >
        {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </Button>

      {/* Sidebar */}
      <div
        className={cn(
          "fixed left-0 top-0 h-full bg-background border-r transition-all duration-300 z-40",
          isCollapsed ? "w-16" : "w-64",
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">F</span>
              </div>
              {!isCollapsed && (
                <div>
                  <h2 className="font-semibold text-lg">FRAS</h2>
                  <p className="text-xs text-muted-foreground capitalize">{userType} Panel</p>
                </div>
              )}
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const isActive = pathname === item.href
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors",
                        isActive ? "bg-primary text-primary-foreground" : "hover:bg-muted",
                        isCollapsed && "justify-center",
                      )}
                    >
                      <item.icon className="h-5 w-5" />
                      {!isCollapsed && <span>{item.label}</span>}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </nav>

          {/* User info and logout */}
          <div className="p-4 border-t">
            {!isCollapsed && (
              <div className="mb-3">
                <p className="text-sm font-medium">{user?.name || user?.email}</p>
                <p className="text-xs text-muted-foreground">{user?.company}</p>
              </div>
            )}
            <Button
              variant="ghost"
              onClick={logout}
              className={cn("w-full justify-start", isCollapsed && "justify-center px-0")}
            >
              <LogOut className="h-4 w-4" />
              {!isCollapsed && <span className="ml-2">Logout</span>}
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
