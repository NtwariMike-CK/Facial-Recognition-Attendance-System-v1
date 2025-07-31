"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useAuth } from "@/components/auth-provider"
import { useToast } from "@/hooks/use-toast"
import { Plus, MessageSquare, Clock, CheckCircle, AlertCircle, X } from "lucide-react"

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

export default function EmployeeTickets() {
  const [tickets, setTickets] = useState<TicketData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedTicket, setSelectedTicket] = useState<TicketData | null>(null)
  const [messageDialogTicket, setMessageDialogTicket] = useState<TicketData | null>(null)
  const [newTicketMessage, setNewTicketMessage] = useState("")
  const { token, user } = useAuth()
  const { toast } = useToast()

  // // DUMMY DATA - Replace with real API calls for production
  // const dummyTickets: TicketData[] = [
  //   {
  //     id: 1,
  //     admin_id: 1,
  //     employee_id: user?.id || 1,
  //     message:
  //       "I'm having trouble with the facial recognition system. It's not detecting my face properly even though I'm looking directly at the camera. I've tried adjusting the lighting and camera angle, but the issue persists. Could you please help me resolve this issue? This is affecting my daily attendance tracking and I'm concerned about my records being inaccurate. I've also noticed that the system works better in the morning but struggles in the afternoon when the lighting changes.",
  //     status: "in_progress",
  //     created_at: "2024-01-20T09:30:00Z",
  //     updated_at: "2024-01-21T10:15:00Z",
  //     employee_name: user?.name || "Employee",
  //   },
  //   {
  //     id: 2,
  //     admin_id: 1,
  //     employee_id: user?.id || 1,
  //     message:
  //       "My attendance record shows I was absent yesterday, but I was actually present and clocked in through the system. Can you please check and correct this discrepancy? I remember arriving at exactly 8:55 AM and leaving at 5:30 PM. I was working on the quarterly financial reports and several colleagues can confirm my presence. This error is concerning as it might affect my performance review.",
  //     status: "solved",
  //     created_at: "2024-01-19T14:15:00Z",
  //     updated_at: "2024-01-20T09:45:00Z",
  //     employee_name: user?.name || "Employee",
  //   },
  //   {
  //     id: 3,
  //     admin_id: 1,
  //     employee_id: user?.id || 1,
  //     message:
  //       "I would like to update my profile picture for better facial recognition accuracy. The current image seems to be causing recognition issues since I got a new haircut and glasses. How can I upload a new photo to the system? Also, should I take the photo in any specific lighting conditions or angle for better recognition?",
  //     status: "pending",
  //     created_at: "2024-01-18T11:45:00Z",
  //     updated_at: "2024-01-18T11:45:00Z",
  //     employee_name: user?.name || "Employee",
  //   },
  // ]

  // const fetchTickets = async () => {
  //   setIsLoading(true)
  //   try {
  //     // PRODUCTION: Replace with real API call
  //     // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/employee/tickets`, {
  //     //   headers: { Authorization: `Bearer ${token}` }
  //     // })
  //     // const data = await response.json()
  //     // setTickets(data)

  //     // Simulate API delay
  //     await new Promise((resolve) => setTimeout(resolve, 800))
  //     setTickets(dummyTickets)
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

  // const createTicket = async () => {
  //   if (!newTicketMessage.trim()) {
  //     toast({
  //       title: "Error",
  //       description: "Please enter a message for your ticket",
  //       variant: "destructive",
  //     })
  //     return
  //   }

  //   try {
  //     // PRODUCTION: Replace with real API call
  //     // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/employee/tickets`, {
  //     //   method: "POST",
  //     //   headers: {
  //     //     "Content-Type": "application/json",
  //     //     Authorization: `Bearer ${token}`
  //     //   },
  //     //   body: JSON.stringify({ message: newTicketMessage })
  //     // })
  //     // const newTicket = await response.json()

  //     // Simulate creating new ticket - ALWAYS starts with "pending" status
  //     const newTicket: TicketData = {
  //       id: tickets.length + 1,
  //       admin_id: 1,
  //       employee_id: user?.id || 1,
  //       message: newTicketMessage,
  //       status: "pending", // Always starts as pending
  //       created_at: new Date().toISOString(),
  //       updated_at: new Date().toISOString(),
  //       employee_name: user?.name || "Employee",
  //     }

  //     setTickets([newTicket, ...tickets])
  //     setNewTicketMessage("")
  //     setIsDialogOpen(false)

  //     toast({
  //       title: "Success",
  //       description: "Ticket submitted successfully. An admin will review it soon.",
  //     })
  //   } catch (error) {
  //     toast({
  //       title: "Error",
  //       description: "Failed to create ticket",
  //       variant: "destructive",
  //     })
  //   }
  // }



  const fetchTickets = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/employee/tickets`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
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
  
  const createTicket = async () => {
    if (!newTicketMessage.trim()) {
      toast({
        title: "Error",
        description: "Please enter a message for your ticket",
        variant: "destructive",
      })
      return
    }
  
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/employee/tickets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: newTicketMessage }),
      })
  
      if (!response.ok) {
        throw new Error("Failed to create ticket")
      }
  
      const newTicket: TicketData = await response.json()
      setTickets([newTicket, ...tickets])
      setNewTicketMessage("")
      setIsDialogOpen(false)
  
      toast({
        title: "Success",
        description: "Ticket submitted successfully. An admin will review it soon.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create ticket",
        variant: "destructive",
      })
    }
  }
  


  useEffect(() => {
    if (token) {
      fetchTickets()
    }
  }, [token])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <AlertCircle className="h-4 w-4" />
      case "in_progress":
        return <Clock className="h-4 w-4" />
      case "solved":
        return <CheckCircle className="h-4 w-4" />
      default:
        return <MessageSquare className="h-4 w-4" />
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

  const getStatusMessage = (status: string) => {
    switch (status) {
      case "pending":
        return "⏳ Your ticket is waiting to be reviewed by an admin."
      case "in_progress":
        return "🔄 An admin is currently working on your ticket."
      case "solved":
        return "✅ Your ticket has been resolved by an admin."
      default:
        return ""
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
        <h1 className="text-3xl font-bold">My Support Tickets</h1>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Submit New Ticket
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Submit Support Ticket</DialogTitle>
              <DialogDescription>
                Describe your issue or request. An admin will review and respond to your ticket.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="message">Describe your issue</Label>
                <Textarea
                  id="message"
                  placeholder="Please describe your issue in detail..."
                  value={newTicketMessage}
                  onChange={(e) => setNewTicketMessage(e.target.value)}
                  rows={5}
                />
                <p className="text-xs text-muted-foreground">
                  Your ticket will be submitted with "Pending" status and reviewed by an admin.
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={createTicket}>Submit Ticket</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Tickets Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {tickets.filter((t) => t.status === "pending").length}
            </div>
            <p className="text-xs text-muted-foreground">Waiting for admin review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Being Worked On</CardTitle>
            <Clock className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {tickets.filter((t) => t.status === "in_progress").length}
            </div>
            <p className="text-xs text-muted-foreground">Admin is working on it</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {tickets.filter((t) => t.status === "solved").length}
            </div>
            <p className="text-xs text-muted-foreground">Issue resolved</p>
          </CardContent>
        </Card>
      </div>

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Your Support Tickets ({tickets.length})</CardTitle>
          <CardDescription>Track your support requests and their current status</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ticket ID</TableHead>
                <TableHead>Your Message</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Submitted</TableHead>
                <TableHead>Last Updated</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tickets.map((ticket) => (
                <TableRow key={ticket.id}>
                  <TableCell className="font-medium">#{ticket.id}</TableCell>
                  <TableCell className="max-w-xs">
                    <div className="flex items-center space-x-2">
                      <span className="truncate">{truncateMessage(ticket.message)}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setMessageDialogTicket(ticket)}
                        className="p-1 h-6 w-6"
                        title="View full message"
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
                    <Button variant="outline" size="sm" onClick={() => setSelectedTicket(ticket)}>
                      View Status
                    </Button>
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
                <DialogTitle>Your Support Message</DialogTitle>
                <DialogDescription>
                  Ticket #{messageDialogTicket?.id} • Submitted on{" "}
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
              <span className="text-sm font-medium">Current Status:</span>
              <Badge className={`${getStatusColor(messageDialogTicket?.status || "")} flex items-center space-x-1`}>
                {getStatusIcon(messageDialogTicket?.status || "")}
                <span className="capitalize">{messageDialogTicket?.status?.replace("_", " ")}</span>
              </Badge>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {getStatusMessage(messageDialogTicket?.status || "")}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMessageDialogTicket(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Ticket Status Dialog - READ ONLY for employees */}
      <Dialog open={!!selectedTicket} onOpenChange={() => setSelectedTicket(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Ticket Status - #{selectedTicket?.id}</DialogTitle>
            <DialogDescription>
              Submitted on {selectedTicket?.created_at ? new Date(selectedTicket.created_at).toLocaleDateString() : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Your Message:</h4>
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
              Last updated by admin:{" "}
              {selectedTicket?.updated_at ? new Date(selectedTicket.updated_at).toLocaleString() : ""}
            </div>

            {/* Status-specific messages */}
            <div
              className={`border rounded-lg p-3 ${
                selectedTicket?.status === "pending"
                  ? "bg-yellow-50 border-yellow-200"
                  : selectedTicket?.status === "in_progress"
                    ? "bg-blue-50 border-blue-200"
                    : "bg-green-50 border-green-200"
              }`}
            >
              <p
                className={`text-sm ${
                  selectedTicket?.status === "pending"
                    ? "text-yellow-800"
                    : selectedTicket?.status === "in_progress"
                      ? "text-blue-800"
                      : "text-green-800"
                }`}
              >
                {getStatusMessage(selectedTicket?.status || "")}
              </p>

              {selectedTicket?.status === "solved" && (
                <p className="text-xs text-green-700 mt-2">
                  If you need further assistance, please submit a new ticket.
                </p>
              )}
            </div>

            {/* Status progression indicator */}
            <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
              <h5 className="text-sm font-medium mb-2">Status Progression:</h5>
              <div className="flex items-center space-x-2 text-xs">
                <div
                  className={`flex items-center space-x-1 ${
                    selectedTicket?.status === "pending" ? "text-yellow-600 font-medium" : "text-gray-400"
                  }`}
                >
                  <AlertCircle className="h-3 w-3" />
                  <span>Pending</span>
                </div>
                <span className="text-gray-400">→</span>
                <div
                  className={`flex items-center space-x-1 ${
                    selectedTicket?.status === "in_progress" ? "text-blue-600 font-medium" : "text-gray-400"
                  }`}
                >
                  <Clock className="h-3 w-3" />
                  <span>In Progress</span>
                </div>
                <span className="text-gray-400">→</span>
                <div
                  className={`flex items-center space-x-1 ${
                    selectedTicket?.status === "solved" ? "text-green-600 font-medium" : "text-gray-400"
                  }`}
                >
                  <CheckCircle className="h-3 w-3" />
                  <span>Solved</span>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedTicket(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
