"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useAuth } from "@/components/auth-provider"
import { useToast } from "@/hooks/use-toast"
import { Plus, Edit, Trash2, Upload, Download } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface Employee {
  id: number
  name: string
  email: string
  role: string
  department: string
  image_path: string | null
  company: string
  created_at: string
}

export default function EmployeeManagement() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null)
  const [filters, setFilters] = useState({
    employee_id: "",
    department: "",
  })
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    role: "",
    department: "IT", // Updated default value
  })
  const { token } = useAuth()
  const { toast } = useToast()



  const fetchEmployees = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
  
      if (!response.ok) throw new Error("Failed to fetch employees")
  
      const data: Employee[] = await response.json()
      setEmployees(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch employees",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }
  


  const handleCreateEmployee = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      })
  
      if (!response.ok) throw new Error("Failed to create employee")
  
      const newEmployee: Employee = await response.json()
      setEmployees([...employees, newEmployee])
      setIsDialogOpen(false)
      setFormData({ name: "", email: "", role: "", department: "IT" })
  
      toast({
        title: "Success",
        description: "Employee created successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create employee",
        variant: "destructive",
      })
    }
  }
  


  const handleUpdateEmployee = async () => {
    if (!editingEmployee) return
  
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees/${editingEmployee.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      })
  
      if (!response.ok) throw new Error("Failed to update employee")
  
      const updatedEmployee: Employee = await response.json()
      setEmployees(employees.map((emp) => (emp.id === updatedEmployee.id ? updatedEmployee : emp)))
      setIsDialogOpen(false)
      setEditingEmployee(null)
      setFormData({ name: "", email: "", role: "", department: "IT" })
  
      toast({
        title: "Success",
        description: "Employee updated successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update employee",
        variant: "destructive",
      })
    }
  }
  


  const handleDeleteEmployee = async (id: number) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
  
      if (!response.ok) throw new Error("Failed to delete employee")
  
      setEmployees(employees.filter((emp) => emp.id !== id))
  
      toast({
        title: "Success",
        description: "Employee deleted successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete employee",
        variant: "destructive",
      })
    }
  }
  


  const handleImageUpload = async (employeeId: number, file: File) => {
    try {
      const formData = new FormData()
      formData.append("file", file)
  
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees/${employeeId}/upload-image`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })
  
      if (!response.ok) throw new Error("Failed to upload image")
  
      const imageUrl = await response.json()
  
      const updatedEmployees = employees.map((emp) =>
        emp.id === employeeId ? { ...emp, image_path: imageUrl } : emp
      )
  
      setEmployees(updatedEmployees)
  
      toast({
        title: "Success",
        description: "Image uploaded successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upload image",
        variant: "destructive",
      })
    }
  }
  

  // Fix 1: Updated downloadCSV function
  const downloadCSV = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees/download`, {
        headers: {
          Authorization: `Bearer ${token}`, // Use the token from useAuth hook
          Accept: "text/csv"
        }
      })

      if (!response.ok) {
        throw new Error("Failed to download CSV")
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)

      const a = document.createElement("a")
      a.href = url
      a.download = "employees.csv"
      a.click()
      window.URL.revokeObjectURL(url)

      toast({
        title: "Success",
        description: "Employee data downloaded successfully",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to download employee data",
        variant: "destructive",
      })
    }
  }



  useEffect(() => {
    if (token) {
      fetchEmployees()
    }
  }, [token])

  const filteredEmployees = employees.filter((emp) => {
    return (
      (!filters.employee_id || emp.id.toString().includes(filters.employee_id)) &&
      (!filters.department || filters.department === "all" || emp.department.toLowerCase().includes(filters.department.toLowerCase()))
    )
  })

  const openCreateDialog = () => {
    setEditingEmployee(null)
    setFormData({ name: "", email: "", role: "", department: "IT" }) // Updated default value
    setIsDialogOpen(true)
  }

  const openEditDialog = (employee: Employee) => {
    setEditingEmployee(employee)
    setFormData({
      name: employee.name,
      email: employee.email,
      role: employee.role,
      department: employee.department,
    })
    setIsDialogOpen(true)
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
        <h1 className="text-3xl font-bold">Employee Management</h1>
        <div className="flex space-x-2">
          <Button onClick={downloadCSV} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button onClick={openCreateDialog}>
            <Plus className="h-4 w-4 mr-2" />
            Add Employee
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="employee_id">Employee ID</Label>
              <Input
                id="employee_id"
                placeholder="Search by ID"
                value={filters.employee_id}
                onChange={(e) => setFilters({ ...filters, employee_id: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="department">Department</Label>
              <Select
                value={filters.department}
                onValueChange={(value) => setFilters({ ...filters, department: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Departments</SelectItem> {/* Updated value prop */}
                  <SelectItem value="IT">IT</SelectItem>
                  <SelectItem value="HR">HR</SelectItem>
                  <SelectItem value="Finance">Finance</SelectItem>
                  <SelectItem value="Marketing">Marketing</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Employee Table */}
      <Card>
        <CardHeader>
          <CardTitle>Employees ({filteredEmployees.length})</CardTitle>
          <CardDescription>Manage your company employees</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Photo</TableHead>
                <TableHead>ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmployees.map((employee) => (
                <TableRow key={employee.id}>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={employee.image_path || undefined} />
                        <AvatarFallback>{employee.name.charAt(0)}</AvatarFallback>
                      </Avatar>
                      <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        id={`upload-${employee.id}`}
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) handleImageUpload(employee.id, file)
                        }}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => document.getElementById(`upload-${employee.id}`)?.click()}
                      >
                        <Upload className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell>{employee.id}</TableCell>
                  <TableCell className="font-medium">{employee.name}</TableCell>
                  <TableCell>{employee.email}</TableCell>
                  <TableCell>{employee.role}</TableCell>
                  <TableCell>{employee.department}</TableCell>
                  <TableCell>{new Date(employee.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm" onClick={() => openEditDialog(employee)}>
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteEmployee(employee.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingEmployee ? "Edit Employee" : "Create Employee"}</DialogTitle>
            <DialogDescription>
              {editingEmployee ? "Update employee information" : "Add a new employee to your company"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Employee name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="employee@company.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                placeholder="Job title"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="department">Department</Label>
              <Select
                value={formData.department}
                onValueChange={(value) => setFormData({ ...formData, department: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="IT">IT</SelectItem>
                  <SelectItem value="HR">HR</SelectItem>
                  <SelectItem value="Finance">Finance</SelectItem>
                  <SelectItem value="Marketing">Marketing</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={editingEmployee ? handleUpdateEmployee : handleCreateEmployee}>
              {editingEmployee ? "Update" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
