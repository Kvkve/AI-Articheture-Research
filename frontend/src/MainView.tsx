import { useCallback, useEffect, useState } from 'react'
import { followAddress, openConversation, readConversationId } from './address.ts'
import {
  listConversations,
  SignInAgainError,
  startConversation,
  type Conversation,
  type User,
} from './backend.ts'
import ChatView from './ChatView.tsx'
import ConversationList from './ConversationList.tsx'

type MainViewProps = {
  token: string
  user: User
  onSignOut: () => void
}

// The view of a signed-in user: the list of conversations on the left, the
// chat on the right, the user's name and "Sign out" above them.
function MainView({ token, user, onSignOut }: MainViewProps) {
  const [conversations, setConversations] = useState<Conversation[] | null>(null)
  const [listError, setListError] = useState<string | null>(null)
  const [openId, setOpenId] = useState<string | null>(readConversationId)

  // The back and forward buttons change the address; the page follows it.
  useEffect(() => followAddress(() => setOpenId(readConversationId())), [])

  // Reads the list again. The returned promise never fails, so a caller need
  // not catch. The setters run in the callbacks of the promise, only after
  // the answer has come.
  const refreshList = useCallback(
    () =>
      listConversations(token).then(
        (list) => {
          setConversations(list)
          setListError(null)
        },
        (error: unknown) => {
          if (error instanceof SignInAgainError) {
            onSignOut()
          } else {
            setListError(error instanceof Error ? error.message : String(error))
          }
        },
      ),
    [token, onSignOut],
  )

  // The list is read when the main view opens.
  useEffect(() => {
    void refreshList()
  }, [refreshList])

  async function handleNewConversation() {
    try {
      const conversation = await startConversation(token)
      await refreshList()
      openConversation(conversation.id)
    } catch (error) {
      if (error instanceof SignInAgainError) {
        onSignOut()
      } else {
        setListError(error instanceof Error ? error.message : String(error))
      }
    }
  }

  return (
    <div className="main-view">
      <header className="top-bar">
        <span className="app-name">AI Agent Platform</span>
        <span className="signed-in-as">Signed in as {user.username}</span>
        <button type="button" onClick={onSignOut}>
          Sign out
        </button>
      </header>
      <ConversationList
        conversations={conversations}
        openId={openId}
        error={listError}
        onNewConversation={handleNewConversation}
      />
      {openId === null ? (
        <main className="chat chat-empty">
          <p>Choose a conversation on the left, or start a new one.</p>
        </main>
      ) : (
        // The key gives each conversation its own chat view. Opening another
        // one removes the old view, which closes an answer that is arriving.
        <ChatView
          key={openId}
          token={token}
          conversationId={openId}
          onStreamStarted={refreshList}
          onSignOut={onSignOut}
        />
      )}
    </div>
  )
}

export default MainView
