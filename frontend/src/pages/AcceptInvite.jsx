import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AcceptInvite() {
  const { user, session } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    // Check URL params for error/success (from backend redirect)
    const params = new URLSearchParams(window.location.search)
    const urlError = params.get('error')
    const urlSuccess = params.get('success')
    
    if (urlError) {
      setError(getErrorMessage(urlError))
    }
    if (urlSuccess === 'true') {
      setSuccess(true)
    }

    // If user is signed in and has invite metadata, auto-accept
    if (user && session && !urlError && !urlSuccess) {
      acceptInvite()
    }
  }, [user, session])

  const acceptInvite = async () => {
    if (!user || !session) {
      setError('Please sign in to accept the invite')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/auth/accept`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Failed to accept invite')
      }

      setSuccess(true)
    } catch (err) {
      setError(err.message || 'Failed to accept invite')
    } finally {
      setLoading(false)
    }
  }

  const getErrorMessage = (errorType) => {
    const errors = {
      missing_token: 'Missing authentication token',
      invalid_token: 'Invalid or expired token',
      no_org: 'No organization found in invite',
      processing_failed: 'Failed to process invite',
      server_error: 'Server error occurred'
    }
    return errors[errorType] || 'An error occurred'
  }

  if (!user) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Accept Invitation</h2>
        <p>Please sign in to accept your invitation.</p>
        <p>After signing in, your invitation will be automatically accepted.</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h2>Accept Invitation</h2>
      
      {loading && <p>Processing invitation...</p>}
      
      {error && (
        <div style={{ color: 'red', marginTop: '20px' }}>
          <p><strong>Error:</strong> {error}</p>
          {user && (
            <button onClick={acceptInvite} style={{ marginTop: '10px' }}>
              Try Again
            </button>
          )}
        </div>
      )}
      
      {success && (
        <div style={{ color: 'green', marginTop: '20px' }}>
          <p><strong>✓ Invitation accepted successfully!</strong></p>
          <p>You are now part of the organization.</p>
        </div>
      )}
      
      {!loading && !error && !success && user && (
        <div>
          <p>Welcome, {user.email}!</p>
          <button onClick={acceptInvite} style={{ marginTop: '10px' }}>
            Accept Invitation
          </button>
        </div>
      )}
    </div>
  )
}

