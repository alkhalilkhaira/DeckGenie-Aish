import { useState } from 'react'
import LandingPage from './components/LandingPage'
import GenerationProgress from './components/GenerationProgress'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('landing') // 'landing', 'generating', 'preview'
  const [sessionId, setSessionId] = useState(null)

  const handleGenerateStart = (newSessionId) => {
    setSessionId(newSessionId)
    setCurrentView('generating')
  }

  const handleBack = () => {
    setCurrentView('landing')
    setSessionId(null)
  }

  const handlePreview = (sessionId) => {
    // TODO: Implement preview functionality
    console.log('Preview presentation:', sessionId)
  }

  return (
    <div className="App">
      {currentView === 'landing' && (
        <LandingPage onGenerateStart={handleGenerateStart} />
      )}
      
      {currentView === 'generating' && sessionId && (
        <GenerationProgress 
          sessionId={sessionId}
          onBack={handleBack}
          onPreview={handlePreview}
        />
      )}
    </div>
  )
}

export default App
