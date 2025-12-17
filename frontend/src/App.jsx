import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import InviteUser from './components/InviteUser'
import AcceptInvite from './pages/AcceptInvite'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function AppContent() {
  const { 
    user, 
    session, 
    loading: authLoading, 
    signingIn, 
    signingOut, 
    authError,
    signInWithGoogle, 
    signOut,
    clearError
  } = useAuth()
  const [count, setCount] = useState(0)
  const [apiMessage, setApiMessage] = useState('')
  const [healthStatus, setHealthStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [backendProfilesCount, setBackendProfilesCount] = useState(null)
  const [brands, setBrands] = useState([])
  const [brandsLoading, setBrandsLoading] = useState(false)
  const [brandsError, setBrandsError] = useState(null)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [currentOrgSlug, setCurrentOrgSlug] = useState('default-org')
  const [orgInfo, setOrgInfo] = useState(null)
  const [orgLoading, setOrgLoading] = useState(false)
  const [orgError, setOrgError] = useState(null)
  const [isSuperuser, setIsSuperuser] = useState(false)

  useEffect(() => {
    // Check if we're on the accept-invite page
    const isAcceptInvitePage = window.location.pathname.includes('/auth/accept-invite') || 
                                window.location.search.includes('success') ||
                                window.location.search.includes('error')
    
    if (isAcceptInvitePage) {
      // Show accept invite page
      return
    }

    // Fetch data from backend on component mount
    fetchApiData()
    // Test backend profiles endpoint
    fetchBackendProfiles()
    // Fetch brands from backend
    fetchBrands()
  }, [])

  // Fetch org info when user is signed in
  useEffect(() => {
    if (user && session) {
      fetchOrgInfo()
    } else {
      setOrgInfo(null)
    }
  }, [user, session])

  const fetchOrgInfo = async () => {
    if (!session || !session.access_token) {
      return
    }

    setOrgLoading(true)
    setOrgError(null)

    try {
      const response = await fetch(`${API_URL}/org/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`)
      }

      const data = await response.json()
      console.log('[ORG] Response:', data)
      console.log('[ORG] is_superuser value:', data.is_superuser, 'type:', typeof data.is_superuser)

      if (data.status === 'success' && data.org) {
        setOrgInfo(data.org)
        setCurrentOrgSlug(data.org.org_slug)
        // Explicitly convert to boolean - handle true, "true", 1, etc.
        const superuserValue = data.is_superuser === true || data.is_superuser === 'true' || data.is_superuser === 1
        console.log('[ORG] Setting isSuperuser to:', superuserValue)
        setIsSuperuser(superuserValue)
        setOrgError(null)
      } else {
        const errorMsg = data.error || data.detail || 'Failed to fetch organization info'
        console.error('[ORG] Error:', errorMsg)
        setOrgError(errorMsg)
      }
    } catch (error) {
      console.error('[ORG] Fetch error:', error)
      setOrgError(error.message || 'Failed to fetch organization info')
    } finally {
      setOrgLoading(false)
    }
  }

  // Check if we should show accept invite page
  const urlParams = new URLSearchParams(window.location.search)
  const isAcceptInvite = window.location.pathname.includes('/auth/accept-invite') || 
                         urlParams.get('success') || 
                         urlParams.get('error')

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


  // Show accept invite page if on that route
  if (isAcceptInvite) {
    return <AcceptInvite />
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
            <p style={{ marginTop: '5px' }}>
              <strong>Superuser:</strong> {isSuperuser ? (
                <span style={{ color: 'purple', fontWeight: 'bold' }}>⭐ Yes</span>
              ) : (
                <span style={{ color: '#666' }}>No</span>
              )}
            </p>
            {session && (
              <p style={{ fontSize: '0.8em', color: '#666' }}>
                Session expires: {new Date(session.expires_at * 1000).toLocaleString()}
              </p>
            )}
            
            {/* Organization Info */}
            {orgLoading ? (
              <p style={{ marginTop: '15px', fontSize: '0.9em' }}>Loading organization info...</p>
            ) : orgError ? (
              <div style={{ marginTop: '15px' }}>
                <p style={{ color: 'orange', fontSize: '0.9em' }}>
                  ⚠ {orgError}
                </p>
                <button onClick={fetchOrgInfo} style={{ fontSize: '0.8em', marginTop: '5px' }}>
                  Retry
                </button>
              </div>
            ) : orgInfo ? (
              <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
                <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Organization</h3>
                <p style={{ margin: '5px 0' }}><strong>Name:</strong> {orgInfo.org_slug}</p>
                <p style={{ margin: '5px 0' }}><strong>ID:</strong> {orgInfo.org_id}</p>
                {orgInfo.user_count !== undefined && (
                  <p style={{ margin: '5px 0' }}><strong>Members:</strong> {orgInfo.user_count}</p>
                )}
                <p style={{ margin: '5px 0' }}>
                  <strong>Your Role:</strong> {isSuperuser ? (
                    <span style={{ color: 'purple', fontWeight: 'bold' }}>⭐ Superuser</span>
                  ) : (
                    <span style={{ color: '#666' }}>Member</span>
                  )}
                </p>
                {orgInfo.created_at && (
                  <p style={{ margin: '5px 0', fontSize: '0.9em', color: '#666' }}>
                    Created: {new Date(orgInfo.created_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            ) : null}
            
            <button 
              onClick={async () => {
                try {
                  await signOut()
                } catch (error) {
                  // Error is handled in AuthContext
                }
              }}
              disabled={signingOut}
              style={{ marginTop: '10px' }}
            >
              {signingOut ? 'Signing out...' : 'Sign Out'}
            </button>
            {authError && (
              <div style={{ marginTop: '10px' }}>
                <p style={{ color: 'red', fontSize: '0.9em' }}>
                  Error: {authError}
                </p>
                <button onClick={clearError} style={{ fontSize: '0.8em', marginTop: '5px' }}>
                  Dismiss
                </button>
              </div>
            )}
            <div style={{ marginTop: '15px' }}>
              <button 
                onClick={() => setShowInviteForm(!showInviteForm)}
                style={{ marginTop: '10px' }}
                disabled={!orgInfo}
              >
                {showInviteForm ? 'Hide' : 'Invite User'}
              </button>
              {showInviteForm && session && orgInfo && (
                <InviteUser 
                  orgSlug={currentOrgSlug}
                  session={session}
                  onSuccess={(data) => {
                    console.log('Invite sent:', data)
                    setShowInviteForm(false)
                    // Refresh org info to update member count
                    fetchOrgInfo()
                  }}
                />
              )}
            </div>
          </div>
        ) : (
          <div>
            <p>Not signed in</p>
            <button 
              onClick={async () => {
                try {
                  await signInWithGoogle()
                } catch (error) {
                  // Error is handled in AuthContext
                }
              }}
              disabled={signingIn}
            >
              {signingIn ? 'Redirecting to Google...' : 'Sign in with Google'}
            </button>
            {authError && (
              <div style={{ marginTop: '10px' }}>
                <p style={{ color: 'red', fontSize: '0.9em' }}>
                  Error: {authError}
                </p>
                <button onClick={clearError} style={{ fontSize: '0.8em', marginTop: '5px' }}>
                  Dismiss
                </button>
              </div>
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
