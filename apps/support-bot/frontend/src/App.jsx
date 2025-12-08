import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Support from './pages/Support'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Support />} />
      </Routes>
    </Router>
  )
}

export default App

