import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [count, setCount] = useState(0)
  const [apiMessage, setApiMessage] = useState('')
  const [healthStatus, setHealthStatus] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Fetch data from backend on component mount
    fetchApiData()
  }, [])

  const fetchApiData = async () => {
    setLoading(true)
    try {
      // Fetch root endpoint
      const rootResponse = await fetch(`${API_URL}/`)
      const rootData = await rootResponse.json()
      setApiMessage(rootData.message || '')

      // Fetch health endpoint
      const healthResponse = await fetch(`${API_URL}/health`)
      const healthData = await healthResponse.json()
      setHealthStatus(healthData.status || '')
    } catch (error) {
      console.error('Error fetching data from backend:', error)
      setApiMessage('Error connecting to backend')
      setHealthStatus('unhealthy')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Divisadero</h1>
      
      <div className="card">
        <h2>Backend Connection</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <>
            <p><strong>API Message:</strong> {apiMessage}</p>
            <p><strong>Health Status:</strong> {healthStatus}</p>
            <button onClick={fetchApiData}>
              Refresh API Data
            </button>
          </>
        )}
      </div>

      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
