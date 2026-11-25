import { conversationAddress } from './address.ts'
import type { Conversation } from './backend.ts'

type ConversationListProps = {
  // null while the list is read for the first time.
  conversations: Conversation[] | null
  openId: string | null
  error: string | null
  onNewConversation: () => void
}

// The list keeps the order that the backend gives, the latest activity first.
// It does not sort by itself.
function ConversationList({ conversations, openId, error, onNewConversation }: ConversationListProps) {
  return (
    <nav className="conversation-list" aria-label="Conversations">
      <button type="button" onClick={onNewConversation}>
        New conversation
      </button>
      {error !== null && (
        <p className="error-line" role="alert">
          {error}
        </p>
      )}
      {conversations === null ? (
        <p>Loading…</p>
      ) : (
        <ul>
          {conversations.map((conversation) => (
            <li key={conversation.id}>
              <a
                href={conversationAddress(conversation.id)}
                aria-current={conversation.id === openId ? 'page' : undefined}
              >
                {conversation.title ?? 'New conversation'}
              </a>
            </li>
          ))}
        </ul>
      )}
    </nav>
  )
}

export default ConversationList
