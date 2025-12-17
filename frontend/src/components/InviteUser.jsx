import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function InviteUser({ orgSlug, session, onSuccess }) {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleInvite = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      if (!session || !session.access_token) {
        throw new Error('You must be signed in to invite users')
      }

      console.log(`[INVITE] Sending invite request for ${email} to org ${orgSlug}`)
      console.log('[INVITE] Session token:', session.access_token ? 'Present' : 'Missing')
      console.log('[INVITE] API URL:', `${API_URL}/org/${orgSlug}/invite`)
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => {
        console.error('[INVITE] Request timeout after 30 seconds')
        controller.abort()
      }, 30000) // 30 second timeout
      
      try {
        const startTime = Date.now()
        console.log('[INVITE] Starting fetch request...')
        
        const response = await fetch(`${API_URL}/org/${orgSlug}/invite`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`
          },
          body: JSON.stringify({ email }),
          signal: controller.signal
        })

        clearTimeout(timeoutId)
        const duration = Date.now() - startTime
        console.log(`[INVITE] Response received after ${duration}ms, status: ${response.status}`)
        
        let data
        try {
          data = await response.json()
        } catch (e) {
          const text = await response.text()
          console.error('[INVITE] Failed to parse JSON:', text)
          throw new Error(`Invalid JSON response: ${text}`)
        }
        
        console.log('[INVITE] Response data:', data)

        if (!response.ok) {
          throw new Error(data.detail || data.error || `Failed to send invite (${response.status})`)
        }

        setSuccess(true)
        setEmail('')
        if (onSuccess) {
          onSuccess(data)
        }
      } catch (fetchError) {
        clearTimeout(timeoutId)
        if (fetchError.name === 'AbortError') {
          throw new Error('Request timed out. Please check your connection and try again.')
        }
        throw fetchError
      }
    } catch (err) {
      console.error('Invite error:', err)
      setError(err.message || 'Failed to send invite')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      padding: '12px', 
      background: '#f9fafb', 
      border: '1px solid #e5e7eb', 
      borderRadius: '6px' 
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600', color: '#1a1a1a' }}>
        Invite User
      </h3>
      <form onSubmit={handleInvite}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email@example.com"
            required
            style={{ 
              flex: 1,
              padding: '6px 10px', 
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '13px',
              outline: 'none'
            }}
            disabled={loading}
          />
          <button 
            type="submit" 
            disabled={loading || !email}
            style={{
              padding: '6px 12px',
              background: loading || !email ? '#d1d5db' : '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: loading || !email ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
      {error && (
        <div style={{ 
          marginTop: '8px', 
          padding: '6px 8px', 
          background: '#fee2e2', 
          borderRadius: '4px' 
        }}>
          <p style={{ color: '#dc2626', fontSize: '12px', margin: 0 }}>
            {error}
          </p>
        </div>
      )}
      {success && (
        <div style={{ 
          marginTop: '8px', 
          padding: '6px 8px', 
          background: '#d1fae5', 
          borderRadius: '4px' 
        }}>
          <p style={{ color: '#065f46', fontSize: '12px', margin: 0 }}>
            ✓ Invitation sent successfully!
          </p>
        </div>
      )}
    </div>
  )
}

