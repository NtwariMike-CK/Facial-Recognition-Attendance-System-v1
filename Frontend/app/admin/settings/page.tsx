"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { useAuth } from "@/components/auth-provider"
import { useToast } from "@/hooks/use-toast"
import { useTheme } from "next-themes"
import { User, Lock, Palette, Save } from "lucide-react"

export default function AdminSettings() {
  const { user, token } = useAuth()
  const { theme, setTheme } = useTheme()
  const { toast } = useToast()

  const [profileData, setProfileData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    role: user?.role || "admin",
  })

  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  })


  const updateProfile = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(profileData),
      })
  
      if (!response.ok) throw new Error("Failed to update profile")
  
      toast({
        title: "Success",
        description: "Profile updated successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive",
      })
    }
  }

  
  const updatePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast({
        title: "Error",
        description: "New passwords do not match",
        variant: "destructive",
      })
      return
    }
  
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/profile/password`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: passwordData.current_password,
          new_password: passwordData.new_password,
        }),
      })
  
      if (!response.ok) throw new Error("Failed to update password")
  
      setPasswordData({
        current_password: "",
        new_password: "",
        confirm_password: "",
      })
  
      toast({
        title: "Success",
        description: "Password updated successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update password",
        variant: "destructive",
      })
    }
  }
  


  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <User className="h-5 w-5" />
              <span>Profile Information</span>
            </CardTitle>
            <CardDescription>Update your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                placeholder="Your full name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                placeholder="your.email@company.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={profileData.role}
                onChange={(e) => setProfileData({ ...profileData, role: e.target.value })}
                placeholder="Administrator"
              />
            </div>

            <div className="space-y-2">
              <Label>Company</Label>
              <Input value={user?.company || ""} disabled />
              <p className="text-xs text-muted-foreground">Company cannot be changed</p>
            </div>

            <Button onClick={updateProfile} className="w-full">
              <Save className="h-4 w-4 mr-2" />
              Save Profile
            </Button>
          </CardContent>
        </Card>

        {/* Password Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Lock className="h-5 w-5" />
              <span>Change Password</span>
            </CardTitle>
            <CardDescription>Update your account password</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current_password">Current Password</Label>
              <Input
                id="current_password"
                type="password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                placeholder="Enter current password"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                placeholder="Enter new password"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm New Password</Label>
              <Input
                id="confirm_password"
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                placeholder="Confirm new password"
              />
            </div>

            <Button
              onClick={updatePassword}
              className="w-full"
              disabled={!passwordData.current_password || !passwordData.new_password || !passwordData.confirm_password}
            >
              <Lock className="h-4 w-4 mr-2" />
              Update Password
            </Button>
          </CardContent>
        </Card>

        {/* Theme Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Palette className="h-5 w-5" />
              <span>Appearance</span>
            </CardTitle>
            <CardDescription>Customize the application theme</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Dark Mode</Label>
                <p className="text-sm text-muted-foreground">Switch between light and dark themes</p>
              </div>
              <Switch checked={theme === "dark"} onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")} />
            </div>

            <div className="pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Current theme: <span className="font-medium capitalize">{theme}</span>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* System Information */}
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
            <CardDescription>Application and account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">User ID:</span>
              <span className="font-medium">{user?.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Account Type:</span>
              <span className="font-medium capitalize">{user?.user_type}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Company:</span>
              <span className="font-medium">{user?.company}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Version:</span>
              <span className="font-medium">FRAS v1.0.0</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
