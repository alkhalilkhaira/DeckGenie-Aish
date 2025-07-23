import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Download, 
  Eye, 
  Clock,
  FileText,
  Search,
  Sparkles,
  Wrench
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import '../App.css'

const GenerationProgress = ({ sessionId, onBack, onPreview }) => {
  const [status, setStatus] = useState({
    status: 'queued',
    progress: 0,
    current_step: 'Initializing...',
    slides_completed: 0,
    total_slides: 10
  })
  const [isPolling, setIsPolling] = useState(true)
  const [estimatedTime, setEstimatedTime] = useState(180)

  const statusConfig = {
    queued: {
      icon: Clock,
      color: 'text-gray-500',
      bgColor: 'bg-gray-100',
      label: 'Queued'
    },
    researching: {
      icon: Search,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100',
      label: 'Researching'
    },
    planning: {
      icon: FileText,
      color: 'text-purple-500',
      bgColor: 'bg-purple-100',
      label: 'Planning'
    },
    generating: {
      icon: Sparkles,
      color: 'text-green-500',
      bgColor: 'bg-green-100',
      label: 'Generating'
    },
    assembling: {
      icon: Wrench,
      color: 'text-orange-500',
      bgColor: 'bg-orange-100',
      label: 'Assembling'
    },
    completed: {
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      label: 'Completed'
    },
    failed: {
      icon: XCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-100',
      label: 'Failed'
    }
  }

  useEffect(() => {
    if (!isPolling) return

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/presentations/status/${sessionId}`, {
          credentials: 'include'
        })
        const data = await response.json()

        if (response.ok) {
          setStatus(data)
          
          if (data.estimated_remaining) {
            setEstimatedTime(data.estimated_remaining)
          }

          if (data.status === 'completed' || data.status === 'failed') {
            setIsPolling(false)
          }
        } else {
          console.error('Failed to fetch status:', data)
          if (data.error?.code === 'SESSION_NOT_FOUND') {
            setIsPolling(false)
          }
        }
      } catch (error) {
        console.error('Error polling status:', error)
      }
    }

    // Poll immediately, then every 2 seconds
    pollStatus()
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [sessionId, isPolling])

  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/presentations/download/${sessionId}`, {
        credentials: 'include'
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.style.display = 'none'
        a.href = url
        a.download = `presentation_${sessionId}.pptx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        const errorData = await response.json()
        alert(errorData.error?.message || 'Failed to download presentation')
      }
    } catch (error) {
      console.error('Error downloading presentation:', error)
      alert('Failed to download presentation')
    }
  }

  const currentConfig = statusConfig[status.status] || statusConfig.queued
  const StatusIcon = currentConfig.icon

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={onBack}>
                ← Back
              </Button>
              <h1 className="text-xl font-semibold text-gray-900">
                Generating Presentation
              </h1>
            </div>
            <Badge variant="secondary">Session: {sessionId.slice(0, 8)}</Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
              <CardHeader className="text-center">
                <div className={`w-16 h-16 ${currentConfig.bgColor} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <StatusIcon className={`h-8 w-8 ${currentConfig.color}`} />
                </div>
                <CardTitle className="text-2xl">
                  {currentConfig.label}
                </CardTitle>
                <p className="text-gray-600">{status.current_step}</p>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Progress</span>
                    <span>{status.progress}%</span>
                  </div>
                  <Progress value={status.progress} className="h-3" />
                </div>

                {/* Slides Progress */}
                {status.total_slides > 0 && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Slides</span>
                      <span>{status.slides_completed} / {status.total_slides}</span>
                    </div>
                    <Progress 
                      value={(status.slides_completed / status.total_slides) * 100} 
                      className="h-2" 
                    />
                  </div>
                )}

                {/* Time Estimate */}
                {status.status !== 'completed' && status.status !== 'failed' && estimatedTime > 0 && (
                  <div className="text-center text-sm text-gray-600">
                    Estimated time remaining: {formatTime(estimatedTime)}
                  </div>
                )}

                {/* Status-specific content */}
                <AnimatePresence mode="wait">
                  {status.status === 'completed' && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-4"
                    >
                      <div className="text-center text-green-600 font-medium">
                        🎉 Your presentation is ready!
                      </div>
                      <div className="flex space-x-3">
                        <Button 
                          onClick={() => onPreview(sessionId)}
                          variant="outline" 
                          className="flex-1"
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          Preview
                        </Button>
                        <Button 
                          onClick={handleDownload}
                          className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    </motion.div>
                  )}

                  {status.status === 'failed' && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-4"
                    >
                      <div className="text-center text-red-600 font-medium">
                        Generation failed
                      </div>
                      {status.error_message && (
                        <div className="text-sm text-gray-600 text-center">
                          {status.error_message}
                        </div>
                      )}
                      <Button 
                        onClick={onBack}
                        variant="outline" 
                        className="w-full"
                      >
                        Try Again
                      </Button>
                    </motion.div>
                  )}

                  {status.status !== 'completed' && status.status !== 'failed' && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-center"
                    >
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-500" />
                      <p className="text-sm text-gray-600 mt-2">
                        Please wait while we generate your presentation...
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </CardContent>
            </Card>
          </motion.div>

          {/* Generation Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-8"
          >
            <Card className="bg-white/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg">Generation Process</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { key: 'researching', label: 'Research & Data Gathering', icon: Search },
                    { key: 'planning', label: 'Content Planning', icon: FileText },
                    { key: 'generating', label: 'Slide Generation', icon: Sparkles },
                    { key: 'assembling', label: 'Final Assembly', icon: Wrench }
                  ].map((step, index) => {
                    const StepIcon = step.icon
                    const isActive = status.status === step.key
                    const isCompleted = ['researching', 'planning', 'generating', 'assembling'].indexOf(status.status) > index
                    
                    return (
                      <div key={step.key} className="flex items-center space-x-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          isCompleted ? 'bg-green-100 text-green-600' :
                          isActive ? 'bg-blue-100 text-blue-600' :
                          'bg-gray-100 text-gray-400'
                        }`}>
                          {isCompleted ? (
                            <CheckCircle className="h-4 w-4" />
                          ) : (
                            <StepIcon className="h-4 w-4" />
                          )}
                        </div>
                        <span className={`${
                          isCompleted ? 'text-green-600 font-medium' :
                          isActive ? 'text-blue-600 font-medium' :
                          'text-gray-500'
                        }`}>
                          {step.label}
                        </span>
                        {isActive && (
                          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                        )}
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </main>
    </div>
  )
}

export default GenerationProgress

