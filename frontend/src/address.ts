// The one place that reads and writes the address of the page. A
// conversation has the address #/conversations/<conversation id>. The part
// after "#" never goes to a server: only the page reads it. Any other form,
// an empty one included, opens no conversation.

const CONVERSATION_ADDRESS = /^#\/conversations\/([^/]+)$/

// The id of the conversation that the address opens, or null.
export function readConversationId(): string | null {
  const match = CONVERSATION_ADDRESS.exec(window.location.hash)
  if (match === null) {
    return null
  }
  try {
    return decodeURIComponent(match[1])
  } catch {
    // A "%" that does not start a valid code: not an address of this page.
    return null
  }
}

// The address to put in a link to a conversation.
export function conversationAddress(conversationId: string): string {
  return `#/conversations/${encodeURIComponent(conversationId)}`
}

export function openConversation(conversationId: string): void {
  window.location.hash = conversationAddress(conversationId)
}

export function openNoConversation(): void {
  window.location.hash = '#/'
}

// Calls the function each time the address changes, also by the back and
// forward buttons. Returns a function that stops this.
export function followAddress(onChange: () => void): () => void {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}
