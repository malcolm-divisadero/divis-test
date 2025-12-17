import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [signingIn, setSigningIn] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const [authError, setAuthError] = useState(null)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signInWithGoogle = async () => {
    setSigningIn(true)
    setAuthError(null)
    
    try {
      // Use environment variable if set, otherwise use current origin (automatically adapts to dev/prod)
      const redirectTo = import.meta.env.VITE_AUTH_REDIRECT_URL || window.location.origin
      
      console.log('OAuth redirect to:', redirectTo)
      console.log('Current origin:', window.location.origin)
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: redirectTo,
        },
      })
      
      if (error) {
        console.error('Error signing in with Google:', error)
        setAuthError(error.message || 'Failed to sign in with Google')
        throw error
      }
      
      return data
    } catch (error) {
      setAuthError(error.message || 'Failed to sign in')
      throw error
    } finally {
      setSigningIn(false)
    }
  }

  const signOut = async () => {
    setSigningOut(true)
    setAuthError(null)
    
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('Error signing out:', error)
        setAuthError(error.message || 'Failed to sign out')
        throw error
      }
      // Clear user and session on successful sign out
      setUser(null)
      setSession(null)
    } catch (error) {
      setAuthError(error.message || 'Failed to sign out')
      throw error
    } finally {
      setSigningOut(false)
    }
  }

  const value = {
    user,
    session,
    loading,
    signingIn,
    signingOut,
    authError,
    signInWithGoogle,
    signOut,
    clearError: () => setAuthError(null),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}


