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
    <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Invite User to Organization</h3>
      <form onSubmit={handleInvite}>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter email address"
            required
            style={{ padding: '8px', width: '250px', marginRight: '10px' }}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !email}>
            {loading ? 'Sending...' : 'Send Invite'}
          </button>
        </div>
      </form>
      {error && (
        <p style={{ color: 'red', fontSize: '0.9em', marginTop: '10px' }}>
          Error: {error}
        </p>
      )}
      {success && (
        <p style={{ color: 'green', fontSize: '0.9em', marginTop: '10px' }}>
          ✓ Invitation sent successfully!
        </p>
      )}
    </div>
  )
}

