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
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <header style={{ marginBottom: '30px', borderBottom: '2px solid #e0e0e0', paddingBottom: '20px' }}>
        <h1 style={{ margin: 0, fontSize: '28px', fontWeight: '600', color: '#1a1a1a' }}>Divisadero</h1>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        {/* Authentication Card */}
        <div style={{ 
          background: '#fff', 
          border: '1px solid #e0e0e0', 
          borderRadius: '8px', 
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: '600', color: '#333' }}>Account</h2>
          {authLoading ? (
            <p style={{ color: '#666', fontSize: '14px' }}>Loading...</p>
          ) : user ? (
            <div>
              <div style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                  <span style={{ fontWeight: '500', color: '#1a1a1a' }}>{user.email}</span>
                </div>
                {isSuperuser && (
                  <span style={{ 
                    display: 'inline-block',
                    background: '#f3e8ff', 
                    color: '#7c3aed', 
                    padding: '2px 8px', 
                    borderRadius: '4px', 
                    fontSize: '12px', 
                    fontWeight: '600',
                    marginTop: '4px'
                  }}>
                    ⭐ Superuser
                  </span>
                )}
              </div>

              {/* Organization Info */}
              {orgLoading ? (
                <p style={{ color: '#666', fontSize: '13px', marginTop: '12px' }}>Loading org...</p>
              ) : orgError ? (
                <div style={{ marginTop: '12px', padding: '8px', background: '#fef3c7', borderRadius: '4px' }}>
                  <p style={{ color: '#92400e', fontSize: '12px', margin: 0 }}>⚠ {orgError}</p>
                  <button 
                    onClick={fetchOrgInfo} 
                    style={{ 
                      fontSize: '11px', 
                      marginTop: '6px',
                      padding: '4px 8px',
                      background: '#fff',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Retry
                  </button>
                </div>
              ) : orgInfo ? (
                <div style={{ 
                  marginTop: '12px', 
                  padding: '12px', 
                  background: '#f9fafb', 
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>{orgInfo.org_slug}</span>
                    {isSuperuser ? (
                      <span style={{ fontSize: '11px', color: '#7c3aed', fontWeight: '500' }}>Superuser</span>
                    ) : (
                      <span style={{ fontSize: '11px', color: '#6b7280' }}>Member</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#6b7280' }}>
                    <span>ID: {orgInfo.org_id}</span>
                    {orgInfo.user_count !== undefined && <span>• {orgInfo.user_count} members</span>}
                  </div>
                </div>
              ) : null}

              <div style={{ marginTop: '16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button 
                  onClick={async () => {
                    try {
                      await signOut()
                    } catch (error) {
                      // Error is handled in AuthContext
                    }
                  }}
                  disabled={signingOut}
                  style={{ 
                    padding: '6px 12px',
                    background: '#ef4444',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '500',
                    cursor: signingOut ? 'not-allowed' : 'pointer',
                    opacity: signingOut ? 0.6 : 1
                  }}
                >
                  {signingOut ? 'Signing out...' : 'Sign Out'}
                </button>
                {orgInfo && (
                  <button 
                    onClick={() => setShowInviteForm(!showInviteForm)}
                    style={{ 
                      padding: '6px 12px',
                      background: showInviteForm ? '#6b7280' : '#3b82f6',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    {showInviteForm ? 'Hide Invite' : 'Invite User'}
                  </button>
                )}
              </div>

              {showInviteForm && session && orgInfo && (
                <div style={{ marginTop: '12px' }}>
                  <InviteUser 
                    orgSlug={currentOrgSlug}
                    session={session}
                    onSuccess={(data) => {
                      console.log('Invite sent:', data)
                      setShowInviteForm(false)
                      fetchOrgInfo()
                    }}
                  />
                </div>
              )}

              {authError && (
                <div style={{ marginTop: '12px', padding: '8px', background: '#fee2e2', borderRadius: '4px' }}>
                  <p style={{ color: '#dc2626', fontSize: '12px', margin: '0 0 6px 0' }}>Error: {authError}</p>
                  <button 
                    onClick={clearError} 
                    style={{ 
                      fontSize: '11px',
                      padding: '4px 8px',
                      background: '#fff',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div>
              <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '12px' }}>Not signed in</p>
              <button 
                onClick={async () => {
                  try {
                    await signInWithGoogle()
                  } catch (error) {
                    // Error is handled in AuthContext
                  }
                }}
                disabled={signingIn}
                style={{ 
                  padding: '8px 16px',
                  background: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: signingIn ? 'not-allowed' : 'pointer',
                  opacity: signingIn ? 0.6 : 1,
                  width: '100%'
                }}
              >
                {signingIn ? 'Redirecting...' : 'Sign in with Google'}
              </button>
              {authError && (
                <div style={{ marginTop: '12px', padding: '8px', background: '#fee2e2', borderRadius: '4px' }}>
                  <p style={{ color: '#dc2626', fontSize: '12px', margin: '0 0 6px 0' }}>Error: {authError}</p>
                  <button 
                    onClick={clearError} 
                    style={{ 
                      fontSize: '11px',
                      padding: '4px 8px',
                      background: '#fff',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Brands Card */}
        <div style={{ 
          background: '#fff', 
          border: '1px solid #e0e0e0', 
          borderRadius: '8px', 
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: '600', color: '#333' }}>Brands</h2>
          {brandsLoading ? (
            <p style={{ color: '#666', fontSize: '14px' }}>Loading...</p>
          ) : brandsError ? (
            <div>
              <p style={{ color: '#dc2626', fontSize: '13px', marginBottom: '8px' }}>Error: {brandsError}</p>
              <button 
                onClick={fetchBrands}
                style={{ 
                  padding: '6px 12px',
                  background: '#f3f4f6',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                Retry
              </button>
            </div>
          ) : brands.length > 0 ? (
            <div>
              <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '12px' }}>{brands.length} brand{brands.length !== 1 ? 's' : ''}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {brands.map((brand) => (
                  <div 
                    key={brand.brand_id}
                    style={{ 
                      padding: '10px', 
                      background: '#f9fafb', 
                      borderRadius: '6px',
                      border: '1px solid #e5e7eb',
                      textAlign: 'left'
                    }}
                  >
                    <div style={{ fontWeight: '600', fontSize: '14px', color: '#1a1a1a', marginBottom: '4px' }}>
                      {brand.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>{brand.slug}</div>
                    {brand.description && (
                      <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                        {brand.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '8px' }}>No brands found</p>
              <button 
                onClick={fetchBrands}
                style={{ 
                  padding: '6px 12px',
                  background: '#f3f4f6',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                Load Brands
              </button>
            </div>
          )}
        </div>
      </div>

      {/* System Status - Compact */}
      <div style={{ 
        background: '#fff', 
        border: '1px solid #e0e0e0', 
        borderRadius: '8px', 
        padding: '16px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginTop: '20px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>Backend: </span>
              <span style={{ fontSize: '12px', fontWeight: '500', color: healthStatus === 'healthy' ? '#10b981' : '#dc2626' }}>
                {healthStatus || 'checking...'}
              </span>
            </div>
            {backendProfilesCount !== null && (
              <div>
                <span style={{ fontSize: '12px', color: '#6b7280' }}>Profiles: </span>
                <span style={{ fontSize: '12px', fontWeight: '500', color: '#1a1a1a' }}>{backendProfilesCount}</span>
              </div>
            )}
            <div>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>Architecture: </span>
              <span style={{ fontSize: '12px', color: '#10b981' }}>Frontend → Backend → Supabase</span>
            </div>
          </div>
        </div>
      </div>
    </div>
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
