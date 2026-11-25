import { useCallback, useEffect, useState } from 'react'
import { openNoConversation } from './address.ts'
import { getCurrentUser, SignInAgainError, type User } from './backend.ts'
import MainView from './MainView.tsx'
import SignInPage from './SignInPage.tsx'
import { readToken, removeToken, saveToken } from './tokenStore.ts'

// Decides what the page shows: the sign-in page, or the main view of the
// signed-in user.
function App() {
  const [token, setToken] = useState<string | null>(readToken)
  const [user, setUser] = useState<User | null>(null)
  const [unreachable, setUnreachable] = useState(false)

  // With a token, read who is signed in: after a sign-in, and when the page
  // loads with a token from an earlier visit.
  useEffect(() => {
    if (token === null) {
      return
    }
    let ignore = false
    getCurrentUser(token).then(
      (currentUser) => {
        if (!ignore) {
          setUser(currentUser)
        }
      },
      (error: unknown) => {
        if (ignore) {
          return
        }
        if (error instanceof SignInAgainError) {
          // The token is no longer valid: the same as signing out.
          removeToken()
          openNoConversation()
          setToken(null)
        } else {
          // The token may still be good, so the user is not signed out.
          setUnreachable(true)
        }
      },
    )
    return () => {
      ignore = true
    }
  }, [token])

  function signIn(newToken: string) {
    saveToken(newToken)
    setUser(null)
    setUnreachable(false)
    setToken(newToken)
  }

  // Also used after any 401. The backend has no sign-out, so this only makes
  // the browser forget the token. An answer that is arriving stops, because
  // the chat view goes away and closes its connection.
  // useCallback keeps the same function from one drawing to the next, so the
  // views that depend on it do not read their data again for no reason.
  const signOut = useCallback(() => {
    removeToken()
    setToken(null)
    setUser(null)
    setUnreachable(false)
    openNoConversation()
  }, [])

  if (token === null) {
    return <SignInPage onSignedIn={signIn} />
  }
  if (user !== null) {
    return <MainView token={token} user={user} onSignOut={signOut} />
  }
  if (unreachable) {
    return (
      <main className="centered">
        <p role="alert">The backend cannot be reached. Try again later.</p>
      </main>
    )
  }
  return (
    <main className="centered">
      <p>Loading…</p>
    </main>
  )
}

export default App
