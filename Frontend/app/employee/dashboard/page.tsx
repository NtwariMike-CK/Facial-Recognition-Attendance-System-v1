"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/components/auth-provider"
import { useToast } from "@/hooks/use-toast"
import { Calendar, Clock, UserCheck, UserX, TrendingUp } from "lucide-react"

interface EmployeeDashboardData {
  total_present: number
  total_late: number
  total_absent: number
  average_arrival_time: string
  average_departure_time: string
  recent_attendance: AttendanceRecord[]
}

interface AttendanceRecord {
  id: number
  employee_id: number
  name: string
  arrival_time: string | null
  departure_time: string | null
  hours_worked: number
  status: "present" | "absent" | "late"
  camera_used: string
  date: string
}

export default function EmployeeDashboard() {
  const [dashboardData, setDashboardData] = useState<EmployeeDashboardData | null>(null)
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [dateFilters, setDateFilters] = useState({
    date_from: "",
    date_to: "",
  })
  const { token, user } = useAuth()
  const { toast } = useToast()

  // // DUMMY DATA - Replace with real API calls for production
  // const dummyDashboardData: EmployeeDashboardData = {
  //   total_present: 18,
  //   total_late: 3,
  //   total_absent: 2,
  //   average_arrival_time: "09:15",
  //   average_departure_time: "17:30",
  //   recent_attendance: [
  //     {
  //       id: 1,
  //       employee_id: user?.id || 1,
  //       name: user?.name || "Employee",
  //       arrival_time: "2024-01-22T09:10:00Z",
  //       departure_time: "2024-01-22T17:25:00Z",
  //       hours_worked: 8.25,
  //       status: "present",
  //       camera_used: "webcam",
  //       date: "2024-01-22T00:00:00Z",
  //     },
  //     {
  //       id: 2,
  //       employee_id: user?.id || 1,
  //       name: user?.name || "Employee",
  //       arrival_time: "2024-01-21T09:25:00Z",
  //       departure_time: "2024-01-21T17:15:00Z",
  //       hours_worked: 7.83,
  //       status: "late",
  //       camera_used: "webcam",
  //       date: "2024-01-21T00:00:00Z",
  //     },
  //     {
  //       id: 3,
  //       employee_id: user?.id || 1,
  //       name: user?.name || "Employee",
  //       arrival_time: null,
  //       departure_time: null,
  //       hours_worked: 0,
  //       status: "absent",
  //       camera_used: "",
  //       date: "2024-01-20T00:00:00Z",
  //     },
  //     {
  //       id: 4,
  //       employee_id: user?.id || 1,
  //       name: user?.name || "Employee",
  //       arrival_time: "2024-01-19T09:05:00Z",
  //       departure_time: "2024-01-19T17:35:00Z",
  //       hours_worked: 8.5,
  //       status: "present",
  //       camera_used: "webcam",
  //       date: "2024-01-19T00:00:00Z",
  //     },
  //     {
  //       id: 5,
  //       employee_id: user?.id || 1,
  //       name: user?.name || "Employee",
  //       arrival_time: "2024-01-18T09:30:00Z",
  //       departure_time: "2024-01-18T17:20:00Z",
  //       hours_worked: 7.83,
  //       status: "late",
  //       camera_used: "webcam",
  //       date: "2024-01-18T00:00:00Z",
  //     },
  //   ],
  // }

  // const fetchDashboardData = async () => {
  //   setIsLoading(true)
  //   try {
  //     // PRODUCTION: Replace with real API call
  //     // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/employee/dashboard`, {
  //     //   headers: { Authorization: `Bearer ${token}` }
  //     // })
  //     // const data = await response.json()
  //     // setDashboardData(data)

  //     // Simulate API delay
  //     await new Promise((resolve) => setTimeout(resolve, 800))
  //     setDashboardData(dummyDashboardData)
  //   } catch (error) {
  //     toast({
  //       title: "Error",
  //       description: "Failed to fetch dashboard data",
  //       variant: "destructive",
  //     })
  //   } finally {
  //     setIsLoading(false)
  //   }
  // }

  // const fetchAttendanceRecords = async () => {
  //   try {
  //     // PRODUCTION: Replace with real API call
  //     // const params = new URLSearchParams()
  //     // if (dateFilters.date_from) params.append('date_from', dateFilters.date_from)
  //     // if (dateFilters.date_to) params.append('date_to', dateFilters.date_to)
  //     // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/employee/attendance?${params}`, {
  //     //   headers: { Authorization: `Bearer ${token}` }
  //     // })
  //     // const data = await response.json()
  //     // setAttendanceRecords(data)

  //     // Simulate API delay
  //     await new Promise((resolve) => setTimeout(resolve, 500))
  //     setAttendanceRecords(dummyDashboardData.recent_attendance)
  //   } catch (error) {
  //     toast({
  //       title: "Error",
  //       description: "Failed to fetch attendance records",
  //       variant: "destructive",
  //     })
  //   }
  // }



  const fetchDashboardData = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/employee/dashboard`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })
  
      if (!response.ok) {
        throw new Error("Failed to fetch dashboard data")
      }
  
      const data: EmployeeDashboardData = await response.json()
      setDashboardData(data)
      setAttendanceRecords(data.recent_attendance)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch dashboard data",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  

  const fetchAttendanceRecords = async () => {
    try {
      const params = new URLSearchParams()
      if (dateFilters.date_from) params.append("date_from", dateFilters.date_from)
      if (dateFilters.date_to) params.append("date_to", dateFilters.date_to)
  
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/employee/attendance?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      )
  
      if (!response.ok) {
        throw new Error("Failed to fetch attendance records")
      }
  
      const data: AttendanceRecord[] = await response.json()
      setAttendanceRecords(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch attendance records",
        variant: "destructive",
      })
    }
  }
  


  useEffect(() => {
    if (token) {
      fetchDashboardData()
      fetchAttendanceRecords()
    }
  }, [token])

  useEffect(() => {
    if (token && (dateFilters.date_from || dateFilters.date_to)) {
      fetchAttendanceRecords()
    }
  }, [dateFilters])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "present":
        return "bg-green-100 text-green-800 border-green-200"
      case "late":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "absent":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const formatTime = (timeString: string | null) => {
    if (!timeString) return "N/A"
    return new Date(timeString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

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
        <div>
          <h1 className="text-3xl font-bold">My Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, {user?.name || user?.email}</p>
        </div>
        <Button onClick={fetchDashboardData}>Refresh</Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Days Present</CardTitle>
            <UserCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{dashboardData?.total_present || 0}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Days Late</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{dashboardData?.total_late || 0}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Days Absent</CardTitle>
            <UserX className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{dashboardData?.total_absent || 0}</div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Attendance Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {dashboardData
                ? Math.round(
                    (dashboardData.total_present /
                      (dashboardData.total_present + dashboardData.total_absent + dashboardData.total_late)) *
                      100,
                  )
                : 0}
              %
            </div>
            <p className="text-xs text-muted-foreground">This month</p>
          </CardContent>
        </Card>
      </div>

      {/* Average Times */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>Average Arrival Time</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboardData?.average_arrival_time || "N/A"}</div>
            <p className="text-sm text-muted-foreground">Based on your recent attendance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>Average Departure Time</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboardData?.average_departure_time || "N/A"}</div>
            <p className="text-sm text-muted-foreground">Based on your recent attendance</p>
          </CardContent>
        </Card>
      </div>

      {/* Date Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Attendance Records</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="date_from">From Date</Label>
              <Input
                id="date_from"
                type="date"
                value={dateFilters.date_from}
                onChange={(e) => setDateFilters({ ...dateFilters, date_from: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date_to">To Date</Label>
              <Input
                id="date_to"
                type="date"
                value={dateFilters.date_to}
                onChange={(e) => setDateFilters({ ...dateFilters, date_to: e.target.value })}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Attendance */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Attendance Records</CardTitle>
          <CardDescription>Your attendance history</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Arrival Time</TableHead>
                <TableHead>Departure Time</TableHead>
                <TableHead>Hours Worked</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Camera Used</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {attendanceRecords.map((record) => (
                <TableRow key={record.id}>
                  <TableCell className="font-medium">{new Date(record.date).toLocaleDateString()}</TableCell>
                  <TableCell>{formatTime(record.arrival_time)}</TableCell>
                  <TableCell>{formatTime(record.departure_time)}</TableCell>
                  <TableCell>
                    {record.hours_worked == null ? 'N/A' : `${record.hours_worked.toFixed(2)}h`}
                    </TableCell>
                  <TableCell>
                    <Badge className={`${getStatusColor(record.status)} capitalize`}>{record.status}</Badge>
                  </TableCell>
                  <TableCell className="capitalize">{record.camera_used || "N/A"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
