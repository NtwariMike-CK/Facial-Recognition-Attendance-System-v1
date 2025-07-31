"use client"

import { useEffect, useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { useAuth } from "@/components/auth-provider"
import { useToast } from "@/hooks/use-toast"
import { Camera, Play, Square, Settings, RefreshCw, AlertCircle } from "lucide-react"

interface CameraSettings {
  id: number
  company: string
  camera_type: string
  camera_source: string
  blinking_threshold: number
  arrival_time: string
  departure_time: string
  recognition_active: boolean
  created_at: string
  updated_at: string
}

interface CameraStatus {
  is_running: boolean
  frame_ready: boolean
  company: string
  employees_loaded: number
  camera_source: string
  camera_type: string
  current_fps?: number
  frame_counter?: number
  streaming_clients?: number
  blink_threshold?: number
  checkout_delay_minutes?: number
}

export default function CameraSettings() {
  const [settings, setSettings] = useState<CameraSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRecognitionActive, setIsRecognitionActive] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [cameraStatus, setCameraStatus] = useState<CameraStatus | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [isStarting, setIsStarting] = useState(false)
  const [isStopping, setIsStopping] = useState(false)
  
  const imgRef = useRef<HTMLImageElement>(null)
  const previewIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null)
  
  const [formData, setFormData] = useState({
    camera_type: "webcam",
    camera_source: "0",
    blinking_threshold: 3,
    arrival_time: "09:00",
    departure_time: "17:00",
  })
  const { token } = useAuth()
  const { toast } = useToast()

  const API_URL = process.env.NEXT_PUBLIC_API_URL

  const fetchCameraSettings = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_URL}/admin/camera-settings`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setSettings(data)
        setFormData({
          camera_type: data.camera_type,
          camera_source: data.camera_source,
          blinking_threshold: data.blinking_threshold,
          arrival_time: data.arrival_time,
          departure_time: data.departure_time,
        })
        setIsRecognitionActive(data.recognition_active)
      } else {
        throw new Error('Failed to fetch settings')
      }
    } catch (error) {
      console.error('Error fetching camera settings:', error)
      toast({
        title: "Error",
        description: "Failed to fetch camera settings",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const updateCameraSettings = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/camera-settings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      })
      
      if (response.ok) {
        const updated = await response.json()
        setSettings(updated)
        toast({
          title: "Success",
          description: "Camera settings updated successfully",
        })
        
        // If recognition is running, it will restart automatically with new settings
        if (isRecognitionActive) {
          toast({
            title: "Info",
            description: "Recognition system will restart with new settings",
          })
        }
      } else {
        throw new Error('Failed to update settings')
      }
    } catch (error) {
      console.error('Error updating camera settings:', error)
      toast({
        title: "Error", 
        description: "Failed to update camera settings",
        variant: "destructive",
      })
    }
  }

  // const startRecognition = async () => {
  //   setIsStarting(true)
  //   try {
  //     const response = await fetch(`${API_URL}/admin/camera-settings/start-recognition?show_preview=${showPreview}`, {
  //       method: "POST",
  //       headers: { Authorization: `Bearer ${token}` }
  //     })

  //     if (!response.ok) {
  //       const errorData = await response.json().catch(() => ({}))
  //       throw new Error(errorData.detail || "Failed to start recognition")
  //     }

  //     const result = await response.json()
  //     setIsRecognitionActive(true)
      
  //     // Start status monitoring
  //     startStatusMonitoring()

  //     // Start preview if enabled and recognition started successfully
  //     if (showPreview) {
  //       // Wait a moment for camera to initialize
  //       setTimeout(() => {
  //         startVideoPreview()
  //       }, 2000)
  //     }

  //     toast({
  //       title: "Success",
  //       description: result.message || "Facial recognition started",
  //     })
  //   } catch (error) {
  //     console.error('Error starting recognition:', error)
  //     toast({
  //       title: "Error",
  //       description: error instanceof Error ? error.message : "Failed to start recognition",
  //       variant: "destructive",
  //     })
  //   } finally {
  //     setIsStarting(false)
  //   }
  // }

  // const stopRecognition = async () => {
  //   setIsStopping(true)
  //   try {
  //     const response = await fetch(`${API_URL}/admin/camera-settings/stop-recognition`, {
  //       method: "POST",
  //       headers: { Authorization: `Bearer ${token}` },
  //     })

  //     // Always update UI state, regardless of API response (killer switch behavior)
  //     setIsRecognitionActive(false)
  //     stopVideoPreview()
  //     stopStatusMonitoring()

  //     if (response.ok) {
  //       const result = await response.json()
  //       toast({
  //         title: "Success",
  //         description: result.message || "Facial recognition stopped",
  //       })
  //     } else {
  //       // Even if API fails, show that we forced stop
  //       toast({
  //         title: "Warning",
  //         description: "Recognition stopped (forced)",
  //         variant: "destructive",
  //       })
  //     }
  //   } catch (error) {
  //     // Even if request fails completely, update UI state (killer switch)
  //     setIsRecognitionActive(false)
  //     stopVideoPreview()
  //     stopStatusMonitoring()
      
  //     toast({
  //       title: "Warning",
  //       description: "Recognition stopped (forced - network error)",
  //       variant: "destructive",
  //     })
  //   } finally {
  //     setIsStopping(false)
  //   }
  // }

  // const startVideoPreview = () => {
  //   if (!imgRef.current) return
    
  //   setPreviewError(null)
    
  //   // Try streaming endpoint first
  //   const streamUrl = `${API_URL}/admin/camera-stream`
  //   console.log('Starting video preview with stream URL:', streamUrl)
    
  //   if (imgRef.current) {
  //     imgRef.current.src = streamUrl
      
  //     // Handle stream errors by falling back to frame polling
  //     imgRef.current.onerror = (e) => {
  //       console.warn("Stream failed, falling back to frame polling:", e)
  //       setPreviewError("Live stream unavailable, using frame polling")
  //       startFramePolling()
  //     }
      
  //     // Handle successful stream load
  //     imgRef.current.onload = () => {
  //       console.log("Stream loaded successfully")
  //       setPreviewError(null)
  //     }
  //   }
  // }

  // const startFramePolling = () => {
  //   if (previewIntervalRef.current) {
  //     clearInterval(previewIntervalRef.current)
  //   }

  //   previewIntervalRef.current = setInterval(async () => {
  //     try {
  //       const response = await fetch(`${API_URL}/admin/camera-preview-frame`, {
  //         headers: { Authorization: `Bearer ${token}` }
  //       })
        
  //       if (response.ok) {
  //         const data = await response.json()
  //         if (imgRef.current && data.frame) {
  //           imgRef.current.src = data.frame
  //           setPreviewError(null)
  //         }
  //       } else if (response.status === 400) {
  //         // Recognition not running
  //         setPreviewError("Recognition system not running")
  //         stopVideoPreview()
  //       } else if (response.status === 503) {
  //         setPreviewError("Camera initializing, please wait...")
  //       }
  //     } catch (error) {
  //       console.error("Failed to fetch preview frame:", error)
  //       setPreviewError("Failed to fetch camera frame")
  //     }
  //   }, 200)
  // }

  // const stopVideoPreview = () => {
  //   if (imgRef.current) {
  //     imgRef.current.src = ""
  //     imgRef.current.onerror = null
  //     imgRef.current.onload = null
  //   }
    
  //   if (previewIntervalRef.current) {
  //     clearInterval(previewIntervalRef.current)
  //     previewIntervalRef.current = null
  //   }
    
  //   setPreviewError(null)
  // }

  // const startStatusMonitoring = () => {
  //   if (statusIntervalRef.current) {
  //     clearInterval(statusIntervalRef.current)
  //   }
    
  //   // Check status every 3 seconds while recognition is supposed to be running
  //   statusIntervalRef.current = setInterval(() => {
  //     if (isRecognitionActive) {
  //       fetchCameraStatus()
  //     }
  //   }, 3000)
  // }

  // const stopStatusMonitoring = () => {
  //   if (statusIntervalRef.current) {
  //     clearInterval(statusIntervalRef.current)
  //     statusIntervalRef.current = null
  //   }
  // }

  // const refreshStatus = () => {
  //   fetchCameraStatus()
  // }

  // useEffect(() => {
  //   if (token) {
  //     fetchCameraSettings()
  //     fetchCameraStatus()
      
  //     return () => {
  //       stopVideoPreview()
  //       stopStatusMonitoring()
  //     }
  //   }
  // }, [token])

  // // Update preview when showPreview changes or recognition state changes
  // useEffect(() => {
  //   if (isRecognitionActive && showPreview) {
  //     startVideoPreview()
  //     startStatusMonitoring()
  //   } else {
  //     stopVideoPreview()
  //     if (!isRecognitionActive) {
  //       stopStatusMonitoring()
  //     }
  //   }
  // }, [showPreview, isRecognitionActive])

  // if (isLoading) {
  //   return (
  //     <div className="flex items-center justify-center h-64">
  //       <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
  //     </div>
  //   )
  // }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Camera Settings</h1>
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh Status</span>
          </Button>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isRecognitionActive ? "bg-green-500" : "bg-red-500"}`}></div>
            <span className="text-sm">Recognition {isRecognitionActive ? "Active" : "Inactive"}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Settings Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Recognition Settings</span>
            </CardTitle>
            <CardDescription>Configure your facial recognition system</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="camera_type">Camera Type</Label>
              <Select
                value={formData.camera_type}
                onValueChange={(value) => setFormData({ ...formData, camera_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="webcam">Webcam</SelectItem>
                  <SelectItem value="ip">IP Camera</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="camera_source">Camera Source</Label>
              <Input
                id="camera_source"
                value={formData.camera_source}
                onChange={(e) => setFormData({ ...formData, camera_source: e.target.value })}
                placeholder={formData.camera_type === "webcam" ? "0" : "192.168.1.100"}
              />
              <p className="text-xs text-muted-foreground">
                {formData.camera_type === "webcam"
                  ? "Use 0 for default camera, 1 for second camera, etc."
                  : "Enter IP address of your IP camera"}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="blinking_threshold">Blinking Threshold</Label>
              <Input
                id="blinking_threshold"
                type="number"
                step="1"
                min="1"
                max="10"
                value={formData.blinking_threshold}
                onChange={(e) => setFormData({ ...formData, blinking_threshold: Number.parseFloat(e.target.value) })}
              />
              <p className="text-xs text-muted-foreground">Sensitivity for blink detection (1 - 10)</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="arrival_time">Arrival Time</Label>
                <Input
                  id="arrival_time"
                  type="time"
                  value={formData.arrival_time}
                  onChange={(e) => setFormData({ ...formData, arrival_time: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="departure_time">Departure Time</Label>
                <Input
                  id="departure_time"
                  type="time"
                  value={formData.departure_time}
                  onChange={(e) => setFormData({ ...formData, departure_time: e.target.value })}
                />
              </div>
            </div>

            <Button 
              onClick={updateCameraSettings} 
              className="w-full"
              disabled={isRecognitionActive && isStarting}
            >
              Save Settings
            </Button>
          </CardContent>
        </Card>
        
      </div>
    </div>
  )
}