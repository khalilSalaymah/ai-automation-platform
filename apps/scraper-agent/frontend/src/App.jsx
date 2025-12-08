import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Scraper from './pages/Scraper'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Scraper />} />
      </Routes>
    </Router>
  )
}

export default App

