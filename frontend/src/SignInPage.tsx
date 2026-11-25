import { useState, type FormEvent } from 'react'
import { signIn } from './backend.ts'

type SignInPageProps = {
  onSignedIn: (token: string) => void
}

function SignInPage({ onSignedIn }: SignInPageProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const token = await signIn(username, password)
      onSignedIn(token)
    } catch (signInError) {
      // A wrong name or password: the text of the backend's answer.
      setError(signInError instanceof Error ? signInError.message : String(signInError))
      setBusy(false)
    }
  }

  return (
    <main className="centered">
      <form className="sign-in" onSubmit={handleSubmit}>
        <h1>Sign in</h1>
        <label>
          User name
          <input
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          Sign in
        </button>
        {error !== null && (
          <p className="error-line" role="alert">
            {error}
          </p>
        )}
      </form>
    </main>
  )
}

export default SignInPage
