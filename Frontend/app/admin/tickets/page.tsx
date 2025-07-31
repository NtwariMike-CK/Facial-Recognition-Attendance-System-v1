"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
import { Ticket, Clock, CheckCircle, AlertCircle, MessageSquare, X } from "lucide-react"

interface TicketData {
  id: number
  admin_id: number
  employee_id: number
  message: string
  status: "pending" | "in_progress" | "solved"
  created_at: string
  updated_at: string
  employee_name: string
}

export default function TicketManagement() {
  const [tickets, setTickets] = useState<TicketData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedTicket, setSelectedTicket] = useState<TicketData | null>(null)
  const [messageDialogTicket, setMessageDialogTicket] = useState<TicketData | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const { token } = useAuth()
  const { toast } = useToast()

  // // DUMMY DATA - Replace with real API calls for production
  // const dummyTickets: TicketData[] = [
  //   {
  //     id: 1,
  //     admin_id: 1,
  //     employee_id: 2,
  //     message:
  //       "I'm having trouble with the facial recognition system. It's not detecting my face properly even though I'm looking directly at the camera. I've tried adjusting the lighting and camera angle, but the issue persists. Could you please help me resolve this? This is affecting my daily attendance tracking and I'm concerned about my records being inaccurate.",
  //     status: "pending",
  //     created_at: "2024-01-20T09:30:00Z",
  //     updated_at: "2024-01-20T09:30:00Z",
  //     employee_name: "Jane Smith",
  //   },
  //   {
  //     id: 2,
  //     admin_id: 1,
  //     employee_id: 3,
  //     message:
  //       "My attendance record shows I was absent yesterday, but I was actually present and worked the full day. I remember clocking in around 9:00 AM and leaving at 5:30 PM. Can you please check the system logs and correct this discrepancy? I have witnesses who can confirm I was in the office all day working on the quarterly reports.",
  //     status: "in_progress",
  //     created_at: "2024-01-19T14:15:00Z",
  //     updated_at: "2024-01-20T10:00:00Z",
  //     employee_name: "Mike Johnson",
  //   },
  //   {
  //     id: 3,
  //     admin_id: 1,
  //     employee_id: 4,
  //     message:
  //       "I need to update my profile picture for better facial recognition accuracy. The current image seems to be causing recognition issues since I got a new haircut and glasses. How can I upload a new photo to the system?",
  //     status: "solved",
  //     created_at: "2024-01-18T11:45:00Z",
  //     updated_at: "2024-01-19T09:20:00Z",
  //     employee_name: "Sarah Wilson",
  //   },
  //   {
  //     id: 4,
  //     admin_id: 1,
  //     employee_id: 5,
  //     message:
  //       "The system is marking me as late even when I arrive on time. I usually get to the office by 8:55 AM, but the system shows my arrival time as 9:05 AM or later. There might be a timezone issue or the camera clock needs synchronization. This is affecting my punctuality record unfairly.",
  //     status: "pending",
  //     created_at: "2024-01-20T16:20:00Z",
  //     updated_at: "2024-01-20T16:20:00Z",
  //     employee_name: "David Brown",
  //   },
  //   {
  //     id: 5,
  //     admin_id: 1,
  //     employee_id: 1,
  //     message:
  //       "I can't access my attendance dashboard. It shows an error message when I try to log in with my credentials. The error says 'Authentication failed' even though I'm using the correct employee ID and email. I've tried resetting my browser cache but the problem persists.",
  //     status: "in_progress",
  //     created_at: "2024-01-19T08:30:00Z",
  //     updated_at: "2024-01-20T11:15:00Z",
  //     employee_name: "John Doe",
  //   },
  // ]

  // const fetchTickets = async () => {
  //   setIsLoading(true)
  //   try {
  //     // PRODUCTION: Replace with real API call
  //     // const url = statusFilter !== "all"
  //     //   ? `${process.env.NEXT_PUBLIC_API_URL}/api/admin/tickets?status_filter=${statusFilter}`
  //     //   : `${process.env.NEXT_PUBLIC_API_URL}/api/admin/tickets`
  //     // const response = await fetch(url, {
  //     //   headers: { Authorization: `Bearer ${token}` }
  //     // })
  //     // const data = await response.json()
  //     // setTickets(data)

  //     // Simulate API delay
  //     await new Promise((resolve) => setTimeout(resolve, 800))

  //     let filteredTickets = dummyTickets
  //     if (statusFilter !== "all") {
  //       filteredTickets = dummyTickets.filter((ticket) => ticket.status === statusFilter)
  //     }
  //     setTickets(filteredTickets)
  //   } catch (error) {
  //     toast({
  //       title: "Error",
  //       description: "Failed to fetch tickets",
  //       variant: "destructive",
  //     })
  //   } finally {
  //     setIsLoading(false)
  //   }
  // }

  // const updateTicketStatus = async (ticketId: number, newStatus: "pending" | "in_progress" | "solved") => {
  //   try {
  //     // PRODUCTION: Replace with real API call
  //     // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/tickets/${ticketId}`, {
  //     //   method: "PUT",
  //     //   headers: {
  //     //     "Content-Type": "application/json",
  //     //     Authorization: `Bearer ${token}`
  //     //   },
  //     //   body: JSON.stringify({ status: newStatus })
  //     // })
  //     // const updatedTicket = await response.json()

  //     // Simulate updating ticket
  //     const updatedTickets = tickets.map((ticket) =>
  //       ticket.id === ticketId ? { ...ticket, status: newStatus, updated_at: new Date().toISOString() } : ticket,
  //     )
  //     setTickets(updatedTickets)
  //     setSelectedTicket(null)

  //     toast({
  //       title: "Success",
  //       description: `Ticket status updated to ${newStatus.replace("_", " ")}`,
  //     })
  //   } catch (error) {
  //     toast({
  //       title: "Error",
  //       description: "Failed to update ticket status",
  //       variant: "destructive",
  //     })
  //   }
  // }



  const fetchTickets = async () => {
    setIsLoading(true)
    try {
      const url =
        statusFilter !== "all"
          ? `${process.env.NEXT_PUBLIC_API_URL}/admin/tickets?status_filter=${statusFilter}`
          : `${process.env.NEXT_PUBLIC_API_URL}/admin/tickets`
  
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
  
      if (!response.ok) {
        throw new Error("Failed to fetch tickets")
      }
  
      const data: TicketData[] = await response.json()
      setTickets(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch tickets",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }
  
  const updateTicketStatus = async (
    ticketId: number,
    newStatus: "pending" | "in_progress" | "solved"
  ) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/tickets/${ticketId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ status: newStatus }),
        }
      )
  
      if (!response.ok) {
        throw new Error("Failed to update ticket status")
      }
  
      const updatedTicket: TicketData = await response.json()
  
      setTickets((prev) =>
        prev.map((ticket) =>
          ticket.id === updatedTicket.id ? updatedTicket : ticket
        )
      )
      setSelectedTicket(null)
  
      toast({
        title: "Success",
        description: `Ticket status updated to ${newStatus.replace("_", " ")}`,
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update ticket status",
        variant: "destructive",
      })
    }
  }
  

  useEffect(() => {
    if (token) {
      fetchTickets()
    }
  }, [token, statusFilter])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <AlertCircle className="h-4 w-4" />
      case "in_progress":
        return <Clock className="h-4 w-4" />
      case "solved":
        return <CheckCircle className="h-4 w-4" />
      default:
        return <Ticket className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "in_progress":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "solved":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const truncateMessage = (message: string, maxLength = 50) => {
    return message.length > maxLength ? message.substring(0, maxLength) + "..." : message
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
        <h1 className="text-3xl font-bold">Ticket Management</h1>
        <Button onClick={fetchTickets}>Refresh</Button>
      </div>

      {/* Status Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Tickets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tickets</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="solved">Solved</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tickets Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tickets</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {tickets.filter((t) => t.status === "pending").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {tickets.filter((t) => t.status === "in_progress").length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Solved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {tickets.filter((t) => t.status === "solved").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Support Tickets ({tickets.length})</CardTitle>
          <CardDescription>Manage employee support requests</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Employee</TableHead>
                <TableHead>Message</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tickets.map((ticket) => (
                <TableRow key={ticket.id}>
                  <TableCell className="font-medium">#{ticket.id}</TableCell>
                  <TableCell>{ticket.employee_name}</TableCell>
                  <TableCell className="max-w-xs">
                    <div className="flex items-center space-x-2">
                      <span className="truncate">{truncateMessage(ticket.message)}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setMessageDialogTicket(ticket)}
                        className="p-1 h-6 w-6"
                      >
                        <MessageSquare className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={`${getStatusColor(ticket.status)} flex items-center space-x-1 w-fit`}>
                      {getStatusIcon(ticket.status)}
                      <span className="capitalize">{ticket.status.replace("_", " ")}</span>
                    </Badge>
                  </TableCell>
                  <TableCell>{new Date(ticket.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(ticket.updated_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <div className="flex space-x-1">
                      <Button variant="outline" size="sm" onClick={() => setSelectedTicket(ticket)}>
                        Manage
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Message Dialog */}
      <Dialog open={!!messageDialogTicket} onOpenChange={() => setMessageDialogTicket(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>Message from {messageDialogTicket?.employee_name}</DialogTitle>
                <DialogDescription>
                  Ticket #{messageDialogTicket?.id} • Created on{" "}
                  {messageDialogTicket?.created_at ? new Date(messageDialogTicket.created_at).toLocaleDateString() : ""}
                </DialogDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setMessageDialogTicket(null)} className="h-6 w-6 p-0">
                <X className="h-4 w-4" />
              </Button>
            </div>
          </DialogHeader>

          <div className="space-y-4">
            <div className="max-h-96 overflow-y-auto">
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{messageDialogTicket?.message}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Status:</span>
              <Badge className={`${getStatusColor(messageDialogTicket?.status || "")} flex items-center space-x-1`}>
                {getStatusIcon(messageDialogTicket?.status || "")}
                <span className="capitalize">{messageDialogTicket?.status?.replace("_", " ")}</span>
              </Badge>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMessageDialogTicket(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Ticket Management Dialog */}
      <Dialog open={!!selectedTicket} onOpenChange={() => setSelectedTicket(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Manage Ticket #{selectedTicket?.id}</DialogTitle>
            <DialogDescription>
              Submitted by {selectedTicket?.employee_name} on{" "}
              {selectedTicket?.created_at ? new Date(selectedTicket.created_at).toLocaleDateString() : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Message:</h4>
              <div className="max-h-32 overflow-y-auto bg-muted p-3 rounded-lg">
                <p className="text-sm">{selectedTicket?.message}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">Current Status:</span>
              <Badge className={`${getStatusColor(selectedTicket?.status || "")} flex items-center space-x-1`}>
                {getStatusIcon(selectedTicket?.status || "")}
                <span className="capitalize">{selectedTicket?.status?.replace("_", " ")}</span>
              </Badge>
            </div>

            <div className="text-xs text-muted-foreground">
              Last updated: {selectedTicket?.updated_at ? new Date(selectedTicket.updated_at).toLocaleString() : ""}
            </div>
          </div>

          <DialogFooter className="flex space-x-2">
            {selectedTicket?.status === "pending" && (
              <Button
                onClick={() => updateTicketStatus(selectedTicket.id, "in_progress")}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Mark In Progress
              </Button>
            )}
            {selectedTicket?.status === "in_progress" && (
              <Button
                onClick={() => updateTicketStatus(selectedTicket.id, "solved")}
                className="bg-green-600 hover:bg-green-700"
              >
                Mark Solved
              </Button>
            )}
            {selectedTicket?.status === "solved" && (
              <Button onClick={() => updateTicketStatus(selectedTicket.id, "pending")} variant="outline">
                Reopen Ticket
              </Button>
            )}
            <Button variant="outline" onClick={() => setSelectedTicket(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
