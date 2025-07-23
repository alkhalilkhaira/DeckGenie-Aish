import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Loader2, Sparkles, FileText, Download, Mic, Palette, Globe } from 'lucide-react'
import { motion } from 'framer-motion'
import '../App.css'

const LandingPage = ({ onGenerateStart }) => {
  const [prompt, setPrompt] = useState('')
  const [slideCount, setSlideCount] = useState(10)
  const [theme, setTheme] = useState('corporate')
  const [includeAudio, setIncludeAudio] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  const themes = [
    {
      id: 'corporate',
      name: 'Corporate',
      description: 'Professional business design',
      colors: ['#1f2937', '#3b82f6', '#10b981']
    },
    {
      id: 'startup',
      name: 'Startup',
      description: 'Modern and dynamic',
      colors: ['#7c3aed', '#f59e0b', '#ef4444']
    },
    {
      id: 'academic',
      name: 'Academic',
      description: 'Scholarly and research-focused',
      colors: ['#374151', '#6366f1', '#059669']
    }
  ]

  const slideCounts = [5, 10, 15]

  const handleGenerate = async () => {
    if (!prompt.trim() || prompt.length < 10) {
      alert('Please enter a topic with at least 10 characters')
      return
    }

    setIsGenerating(true)
    
    try {
      const response = await fetch('/api/presentations/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          prompt: prompt.trim(),
          slide_count: slideCount,
          theme: theme,
          include_tts: includeAudio,
          language: 'en'
        })
      })

      const data = await response.json()

      if (data.success) {
        onGenerateStart(data.session_id)
      } else {
        alert(data.error?.message || 'Failed to start presentation generation')
        setIsGenerating(false)
      }
    } catch (error) {
      console.error('Error starting generation:', error)
      alert('Failed to connect to server. Please try again.')
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Prompt2Presentation</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="secondary">AI-Powered</Badge>
              <Button variant="ghost" size="sm">Help</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          {/* Hero Section */}
          <div className="text-center mb-12">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl font-bold text-gray-900 mb-6"
            >
              Create Professional Presentations
              <span className="text-blue-600"> with AI</span>
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-xl text-gray-600 mb-8"
            >
              Transform any topic into a stunning PowerPoint presentation in seconds.
              Powered by AI with authentic data from trusted sources.
            </motion.p>
          </div>

          {/* Generation Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <Card className="p-8 shadow-xl border-0 bg-white/90 backdrop-blur-sm">
              <CardContent className="space-y-8">
                {/* Prompt Input */}
                <div className="space-y-3">
                  <label className="text-lg font-semibold text-gray-900">
                    Enter your topic or prompt
                  </label>
                  <Textarea
                    placeholder="e.g., History of Artificial Intelligence, Marketing Strategy for 2025, Climate Change Solutions..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="min-h-[120px] text-lg resize-none border-2 focus:border-blue-500 transition-colors"
                    disabled={isGenerating}
                  />
                  <div className="flex justify-between text-sm text-gray-500">
                    <span>Be specific for better results</span>
                    <span>{prompt.length}/500</span>
                  </div>
                </div>

                {/* Slide Count Selection */}
                <div className="space-y-3">
                  <label className="text-lg font-semibold text-gray-900">
                    Number of slides
                  </label>
                  <div className="flex space-x-3">
                    {slideCounts.map((count) => (
                      <Button
                        key={count}
                        variant={slideCount === count ? "default" : "outline"}
                        onClick={() => setSlideCount(count)}
                        disabled={isGenerating}
                        className="flex-1 h-12 text-lg"
                      >
                        {count} Slides
                      </Button>
                    ))}
                  </div>
                  {slideCount > 12 && (
                    <p className="text-sm text-amber-600">
                      Maximum 12 slides available. Upgrade for more slides.
                    </p>
                  )}
                </div>

                {/* Theme Selection */}
                <div className="space-y-3">
                  <label className="text-lg font-semibold text-gray-900">
                    Presentation theme
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {themes.map((themeOption) => (
                      <Card
                        key={themeOption.id}
                        className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                          theme === themeOption.id
                            ? 'ring-2 ring-blue-500 shadow-lg'
                            : 'hover:shadow-md'
                        }`}
                        onClick={() => !isGenerating && setTheme(themeOption.id)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center space-x-3 mb-3">
                            <div className="flex space-x-1">
                              {themeOption.colors.map((color, index) => (
                                <div
                                  key={index}
                                  className="w-4 h-4 rounded-full"
                                  style={{ backgroundColor: color }}
                                />
                              ))}
                            </div>
                            <h3 className="font-semibold">{themeOption.name}</h3>
                          </div>
                          <p className="text-sm text-gray-600">{themeOption.description}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>

                {/* Advanced Options */}
                <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 flex items-center">
                    <Palette className="h-5 w-5 mr-2" />
                    Advanced Options
                  </h3>
                  
                  <div className="space-y-3">
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={includeAudio}
                        onChange={(e) => setIncludeAudio(e.target.checked)}
                        disabled={isGenerating}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <div className="flex items-center space-x-2">
                        <Mic className="h-4 w-4" />
                        <span>Include voice narration</span>
                      </div>
                    </label>

                    <div className="flex items-center space-x-3 text-gray-500">
                      <Globe className="h-4 w-4" />
                      <span>Language: English</span>
                    </div>
                  </div>
                </div>

                {/* Generate Button */}
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating || !prompt.trim() || prompt.length < 10}
                  className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-200"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      Starting Generation...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5 mr-2" />
                      Generate Presentation
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Features */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">AI-Powered Content</h3>
              <p className="text-gray-600">
                Intelligent content generation with authentic data from trusted sources
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Download className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Instant Download</h3>
              <p className="text-gray-600">
                Download your presentation as a PowerPoint file ready to use
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Professional Design</h3>
              <p className="text-gray-600">
                Beautiful, professional themes suitable for any audience
              </p>
            </div>
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}

export default LandingPage

