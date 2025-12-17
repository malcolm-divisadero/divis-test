import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function AppContent() {
  const { user, session, loading: authLoading, signInWithGoogle, signOut } = useAuth()
  const [count, setCount] = useState(0)
  const [apiMessage, setApiMessage] = useState('')
  const [healthStatus, setHealthStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [backendProfilesCount, setBackendProfilesCount] = useState(null)
  const [brands, setBrands] = useState([])
  const [brandsLoading, setBrandsLoading] = useState(false)
  const [brandsError, setBrandsError] = useState(null)
  const [signInError, setSignInError] = useState(null)

  useEffect(() => {
    // Fetch data from backend on component mount
    fetchApiData()
    // Test backend profiles endpoint
    fetchBackendProfiles()
    // Fetch brands from backend
    fetchBrands()
  }, [])

  const fetchBackendProfiles = async () => {
    try {
      const response = await fetch(`${API_URL}/profiles`)
      const data = await response.json()
      if (data.status === 'success') {
        setBackendProfilesCount(data.count)
      }
    } catch (error) {
      console.error('Error fetching profiles from backend:', error)
    }
  }

  const fetchBrands = async () => {
    setBrandsLoading(true)
    setBrandsError(null)
    try {
      const response = await fetch(`${API_URL}/brands`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setBrands(data.brands || [])
      } else {
        throw new Error(data.error || 'Failed to fetch brands')
      }
    } catch (error) {
      console.error('Error fetching brands:', error)
      setBrandsError(error.message || 'Failed to fetch brands')
    } finally {
      setBrandsLoading(false)
    }
  }

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
        <h2>Authentication</h2>
        {authLoading ? (
          <p>Loading auth state...</p>
        ) : user ? (
          <div>
            <p style={{ color: 'green' }}><strong>✓ Signed in as:</strong> {user.email}</p>
            <p><strong>User ID:</strong> {user.id}</p>
            {session && (
              <p style={{ fontSize: '0.8em', color: '#666' }}>
                Session expires: {new Date(session.expires_at * 1000).toLocaleString()}
              </p>
            )}
            <button onClick={signOut} style={{ marginTop: '10px' }}>
              Sign Out
            </button>
          </div>
        ) : (
          <div>
            <p>Not signed in</p>
            <button 
              onClick={async () => {
                try {
                  setSignInError(null)
                  await signInWithGoogle()
                } catch (error) {
                  setSignInError(error.message || 'Failed to sign in')
                }
              }}
            >
              Sign in with Google
            </button>
            {signInError && (
              <p style={{ color: 'red', fontSize: '0.9em', marginTop: '10px' }}>
                Error: {signInError}
              </p>
            )}
          </div>
        )}
      </div>
      
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
        <h2>Database Connection</h2>
        {backendProfilesCount !== null && (
          <p><strong>Profiles Count:</strong> {backendProfilesCount}</p>
        )}
        <p style={{ color: 'green' }}><strong>✓ Architecture:</strong> Frontend → Backend → Supabase</p>
      </div>

      <div className="card">
        <h2>Brands</h2>
        {brandsLoading ? (
          <p>Loading brands...</p>
        ) : brandsError ? (
          <div>
            <p style={{ color: 'red' }}><strong>Error:</strong> {brandsError}</p>
            <button onClick={fetchBrands}>
              Retry
            </button>
          </div>
        ) : brands.length > 0 ? (
          <div>
            <p><strong>Found {brands.length} brand(s):</strong></p>
            <ul style={{ textAlign: 'left', display: 'inline-block' }}>
              {brands.map((brand) => (
                <li key={brand.brand_id}>
                  <strong>{brand.name}</strong> ({brand.slug})
                  {brand.description && (
                    <div style={{ fontSize: '0.9em', color: '#666', marginLeft: '20px' }}>
                      {brand.description}
                    </div>
                  )}
                </li>
              ))}
            </ul>
            <button onClick={fetchBrands} style={{ marginTop: '10px' }}>
              Refresh Brands
            </button>
          </div>
        ) : (
          <div>
            <p>No brands found</p>
            <button onClick={fetchBrands}>
              Load Brands
            </button>
          </div>
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

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
