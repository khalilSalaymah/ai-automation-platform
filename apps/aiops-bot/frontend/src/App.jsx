import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import AiOps from './pages/AiOps'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<AiOps />} />
      </Routes>
    </Router>
  )
}

export default App

