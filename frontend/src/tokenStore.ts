// The one place that touches sessionStorage. The owner chose the storage of
// the tab: the token stays after a reload, and is gone when the tab is
// closed. Two tabs can hold two different users.

const TOKEN_KEY = 'token'

export function readToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function saveToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}
