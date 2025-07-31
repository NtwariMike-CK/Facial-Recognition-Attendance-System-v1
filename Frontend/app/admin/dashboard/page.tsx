"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAuth } from "@/components/auth-provider"
import { useToast } from "@/hooks/use-toast"
import { Users, UserCheck, UserX, Clock, TrendingUp, TrendingDown, Minus } from "lucide-react"

interface DashboardData {
  total_employees: number
  present_today: number
  absent_today: number
  late_today: number
  attendance_by_department: Record<string, any>
  late_days_week: Record<string, any>
  arrival_time_trend: Array<Record<string, any>>
}

interface DepartmentComparison {
  departments: Array<{
    department: string
    total_employees: number
    attendance_rate: number
    late_rate: number
    avg_arrival_time: string
    present_count: number
    late_count: number
  }>
}

interface QuickStats {
  today_present: number
  yesterday_present: number
  change_from_yesterday: number
  weekly_average: number
  trend: 'up' | 'down' | 'stable'
}

interface RecentActivity {
  activities: Array<{
    id: number
    employee_name: string
    employee_id: string
    department: string
    date: string
    arrival_time: string
    status: string
    timestamp: string
  }>
}

export default function AdminDashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [departmentComparison, setDepartmentComparison] = useState<DepartmentComparison | null>(null)

  const [quickStats, setQuickStats] = useState<QuickStats | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivity | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [filters, setFilters] = useState({
    date: "",
    employee_id: "",
    department: "",
  })
  const { token } = useAuth()
  const { toast } = useToast()

  const fetchDashboardData = async () => {
    setIsLoading(true)
    try {
      // Build query parameters
      const params = new URLSearchParams()
      if (filters.date) params.append('date_filter', filters.date)
      if (filters.employee_id) params.append('employee_id', filters.employee_id)
      if (filters.department) params.append('department', filters.department)

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/dashboard?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        }
      )

      if (!response.ok) {
        throw new Error("Failed to fetch dashboard data")
      }

      const data: DashboardData = await response.json()
      setDashboardData(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load dashboard data.",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchQuickStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/quick-stats`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        }
      )

      if (response.ok) {
        const data: QuickStats = await response.json()
        setQuickStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch quick stats:", error)
    }
  }


  const fetchDepartmentComparison = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/department-comparison?days=30`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        }
      )
  
      if (response.ok) {
        const data: DepartmentComparison = await response.json()
        setDepartmentComparison(data)
      }
    } catch (error) {
      console.error("Failed to fetch department comparison:", error)
    }
  }

  const fetchRecentActivity = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/recent-activity?limit=5`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
          }
        }
      )

      if (response.ok) {
        const data: RecentActivity = await response.json()
        setRecentActivity(data)
      }
    } catch (error) {
      console.error("Failed to fetch recent activity:", error)
    }
  }

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const applyFilters = () => {
    fetchDashboardData()
  }

  const clearFilters = () => {
    setFilters({ date: "", employee_id: "", department: "" })
    // Auto-apply after clearing
    setTimeout(() => fetchDashboardData(), 100)
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />
      default:
        return <Minus className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'present':
        return 'text-green-600 bg-green-50'
      case 'late':
        return 'text-yellow-600 bg-yellow-50'
      case 'absent':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  useEffect(() => {
    if (token) {
      fetchDashboardData()
      fetchQuickStats()
      fetchRecentActivity()
      fetchDepartmentComparison()
      
      // Set up auto-refresh every 5 minutes
      const interval = setInterval(() => {
        fetchDashboardData()
        fetchQuickStats()
        fetchRecentActivity()
        fetchDepartmentComparison()
      }, 5 * 60 * 1000)

      return () => clearInterval(interval)
    }
  }, [token])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Button onClick={fetchDashboardData}>Refresh</Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="space-y-2">
              <Label htmlFor="date">Date</Label>
              <Input
                id="date"
                type="date"
                value={filters.date}
                onChange={(e) => handleFilterChange('date', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="employee_id">Employee ID</Label>
              <Input
                id="employee_id"
                placeholder="Enter employee ID"
                value={filters.employee_id}
                onChange={(e) => handleFilterChange('employee_id', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="department">Department</Label>
              <Select
                value={filters.department}
                onValueChange={(value) => handleFilterChange('department', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Departments</SelectItem>
                  <SelectItem value="hr">HR</SelectItem>
                  <SelectItem value="it">IT</SelectItem>
                  <SelectItem value="finance">Finance</SelectItem>
                  <SelectItem value="marketing">Marketing</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={applyFilters}>Apply Filters</Button>
            <Button variant="outline" onClick={clearFilters}>Clear Filters</Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.total_employees || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Present Today</CardTitle>
            <UserCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {dashboardData?.present_today || 0}
            </div>
            {quickStats && (
              <div className="flex items-center text-xs text-muted-foreground mt-1">
                {getTrendIcon(quickStats.trend)}
                <span className="ml-1">
                  {quickStats.change_from_yesterday > 0 ? '+' : ''}
                  {quickStats.change_from_yesterday} from yesterday
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Absent Today</CardTitle>
            <UserX className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {dashboardData?.absent_today || 0}
            </div>
            {quickStats && (
              <div className="text-xs text-muted-foreground mt-1">
                Weekly avg: {quickStats.weekly_average}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Late Today</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {dashboardData?.late_today || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Department Summary</CardTitle>
            <CardDescription>Attendance breakdown by department (Last 30 days)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {departmentComparison?.departments.map((dept) => (
                <div key={dept.department} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex-1">
                    <span className="font-medium capitalize">{dept.department}</span>
                    <div className="text-xs text-muted-foreground mt-1">
                      {dept.total_employees} employees • Avg arrival: {dept.avg_arrival_time}
                    </div>
                  </div>
                  <div className="flex space-x-4 text-sm">
                    <div className="text-center">
                      <div className="text-green-600 font-medium">{dept.present_count}</div>
                      <div className="text-xs text-muted-foreground">Present</div>
                    </div>
                    <div className="text-center">
                      <div className="text-yellow-600 font-medium">{dept.late_count}</div>
                      <div className="text-xs text-muted-foreground">Late</div>
                    </div>
                    <div className="text-center">
                      <div className="text-blue-600 font-medium">{dept.attendance_rate}%</div>
                      <div className="text-xs text-muted-foreground">Rate</div>
                    </div>
                  </div>
                </div>
              ))}
              {(!departmentComparison?.departments || departmentComparison.departments.length === 0) && (
                <div className="text-center text-muted-foreground py-4">
                  No department data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>


        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest attendance records</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentActivity?.activities.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex-1">
                    <div className="font-medium">{activity.employee_name}</div>
                    <div className="text-sm text-muted-foreground">
                      {activity.employee_id} • {activity.department}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                      {activity.status}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {activity.arrival_time}
                    </div>
                  </div>
                </div>
              ))}
              {(!recentActivity?.activities || recentActivity.activities.length === 0) && (
                <div className="text-center text-muted-foreground py-4">
                  No recent activity
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Late Days Pattern */}
      {dashboardData?.late_days_week && Object.keys(dashboardData.late_days_week).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Late Days Pattern</CardTitle>
            <CardDescription>Days when employees are most likely to be late</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-4">
              {Object.entries(dashboardData.late_days_week).map(([day, count]) => (
                <div key={day} className="text-center">
                  <div className="text-sm font-medium text-muted-foreground">{day.slice(0, 3)}</div>
                  <div className="text-2xl font-bold text-yellow-600 mt-1">{count as number}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}