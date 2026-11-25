import { useCallback, useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import {
  AnswerStoppedError,
  BackendError,
  readHistory,
  sendMessage,
  SignInAgainError,
  type Message,
  type StreamMessage,
} from './backend.ts'
import ChatMessage from './ChatMessage.tsx'

type ChatViewProps = {
  token: string
  conversationId: string
  // Called when the stream of an answer starts: the backend has then written
  // the title and the time of the last activity, so the list is right.
  onStreamStarted: () => void
  onSignOut: () => void
}

// What the chat is doing now.
// - loading: the history is being read for the first time.
// - ready: the history is shown and a message can be sent.
// - sending: a message was sent; its answer has not ended.
// - rereading: after an error, a cut or a stop, the history is read again.
// - notFound: the backend has no such conversation for this user.
// - failed: the history could not be read.
type Phase = 'loading' | 'ready' | 'sending' | 'rereading' | 'notFound' | 'failed'

// The message that was sent and the answer so far, shown below the history
// until the history is read again or the answer ends.
type Pending = {
  userText: string
  answer: string
  firstPieceArrived: boolean
}

const CONNECTION_LOST_TEXT = 'The connection was lost before the answer ended.'

// How close to the bottom, in pixels, still counts as "at the bottom", so
// that a small scroll by the user's hand does not stop the following.
const BOTTOM_MARGIN_PIXELS = 40

function ChatView({ token, conversationId, onStreamStarted, onSignOut }: ChatViewProps) {
  const [phase, setPhase] = useState<Phase>('loading')
  const [messages, setMessages] = useState<Message[]>([])
  const [pending, setPending] = useState<Pending | null>(null)
  const [draft, setDraft] = useState('')
  const [errorLine, setErrorLine] = useState<string | null>(null)
  const [notFoundText, setNotFoundText] = useState<string | null>(null)
  const [stopped, setStopped] = useState(false)

  // The way to close the connection of the answer that is arriving.
  const controllerRef = useRef<AbortController | null>(null)
  // True once this view is going away. A request that ends after that
  // changes nothing on the page.
  const leavingRef = useRef(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const followBottomRef = useRef(true)

  // Reads the history and shows it. isCurrent says whether the answer still
  // belongs on the page when it arrives. The setters run in the callbacks of
  // the promise, only after the answer has come.
  const loadHistory = useCallback(
    (isCurrent: () => boolean) =>
      readHistory(token, conversationId).then(
        (history) => {
          if (!isCurrent()) {
            return
          }
          setMessages(history)
          setPending(null)
          setPhase('ready')
        },
        (error: unknown) => {
          if (!isCurrent()) {
            return
          }
          // Only the history says what was stored. Without it, a message
          // that was sent and the part of its answer must not stay on the
          // page as if they were stored.
          setPending(null)
          if (error instanceof SignInAgainError) {
            onSignOut()
          } else if (error instanceof BackendError && error.status === 404) {
            setNotFoundText(error.message)
            setPhase('notFound')
          } else {
            setErrorLine(textOf(error))
            setPhase('failed')
          }
        },
      ),
    [token, conversationId, onSignOut],
  )

  useEffect(() => {
    let current = true
    void loadHistory(() => current)
    return () => {
      current = false
    }
  }, [loadHistory])

  // Leaving the conversation, signing out, and closing or reloading the page
  // all close the connection of an answer that is arriving.
  useEffect(() => {
    leavingRef.current = false
    function leave() {
      leavingRef.current = true
      controllerRef.current?.abort()
    }
    window.addEventListener('pagehide', leave)
    return () => {
      window.removeEventListener('pagehide', leave)
      leave()
    }
  }, [])

  // Keeps the newest text in view while an answer grows, unless the user has
  // scrolled up.
  useEffect(() => {
    const box = scrollRef.current
    if (box !== null && followBottomRef.current) {
      box.scrollTop = box.scrollHeight
    }
  }, [messages, pending, phase])

  function handleScroll() {
    const box = scrollRef.current
    if (box !== null) {
      followBottomRef.current = box.scrollHeight - box.scrollTop - box.clientHeight < BOTTOM_MARGIN_PIXELS
    }
  }

  async function rereadHistory() {
    setPhase('rereading')
    await loadHistory(() => !leavingRef.current)
  }

  async function sendDraft() {
    const text = draft
    if (phase !== 'ready' || text.trim() === '') {
      return
    }
    setErrorLine(null)
    setStopped(false)
    setPending({ userText: text, answer: '', firstPieceArrived: false })
    setPhase('sending')
    followBottomRef.current = true
    const controller = new AbortController()
    controllerRef.current = controller

    let stream: AsyncGenerator<StreamMessage>
    try {
      stream = await sendMessage(token, conversationId, text, controller.signal)
    } catch (error) {
      controllerRef.current = null
      if (leavingRef.current) {
        return
      }
      if (error instanceof SignInAgainError) {
        onSignOut()
      } else if (error instanceof AnswerStoppedError) {
        // Stopped before the backend answered. Whether the message was
        // stored is not known here; the history tells.
        setStopped(true)
        await rereadHistory()
      } else {
        // Refused before the stream: nothing was stored. The text goes back
        // into the box so the user can change it and send it again.
        setPending(null)
        setDraft(text)
        setErrorLine(textOf(error))
        setPhase('ready')
      }
      return
    }

    setDraft('')
    onStreamStarted()

    let answer = ''
    let ending: 'end' | 'error' | 'cut' = 'cut'
    try {
      for await (const message of stream) {
        if (message.type === 'text') {
          answer += message.text
          const answerSoFar = answer
          setPending({ userText: text, answer: answerSoFar, firstPieceArrived: true })
        } else if (message.type === 'end') {
          ending = 'end'
        } else {
          ending = 'error'
          setErrorLine(message.message)
        }
      }
    } catch (error) {
      controllerRef.current = null
      if (leavingRef.current) {
        return
      }
      if (error instanceof AnswerStoppedError) {
        setStopped(true)
      } else {
        setErrorLine(textOf(error))
      }
      await rereadHistory()
      return
    }
    // The loop ends when the stream has closed, not at the "end" message, so
    // a new message cannot meet a conversation that is still busy.
    controllerRef.current = null
    if (leavingRef.current) {
      return
    }

    if (ending === 'end') {
      setMessages((shown) => [...shown, { role: 'user', text }, { role: 'assistant', text: answer }])
      setPending(null)
      setPhase('ready')
      return
    }
    if (ending === 'cut') {
      setErrorLine(CONNECTION_LOST_TEXT)
    }
    await rereadHistory()
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void sendDraft()
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== 'Enter' || event.shiftKey) {
      return
    }
    // While an input method composes a text, as for Chinese, Enter picks the
    // characters and must not send. Some browsers mark this only with the
    // old key code 229, so both are checked.
    if (event.nativeEvent.isComposing || event.keyCode === 229) {
      return
    }
    event.preventDefault()
    void sendDraft()
  }

  function handleStop() {
    controllerRef.current?.abort()
  }

  const canWrite = phase === 'ready'
  const canSend = canWrite && draft.trim() !== ''

  return (
    <main className="chat">
      <div className="chat-messages" ref={scrollRef} onScroll={handleScroll}>
        {phase === 'loading' && <p className="chat-note">Reading the history…</p>}
        {phase === 'notFound' && (
          <p className="error-line" role="alert">
            {notFoundText}
          </p>
        )}
        {messages.map((message, index) => (
          <ChatMessage key={index} role={message.role} text={message.text} />
        ))}
        {pending !== null && <ChatMessage role="user" text={pending.userText} />}
        {pending !== null && pending.firstPieceArrived && <ChatMessage role="assistant" text={pending.answer} />}
        {pending !== null && !pending.firstPieceArrived && phase === 'sending' && (
          <p className="chat-note" role="status">
            The model is working…
          </p>
        )}
      </div>
      {stopped && (
        <p className="notice-line" role="status">
          The answer was stopped.
        </p>
      )}
      {errorLine !== null && (
        <p className="error-line" role="alert">
          {errorLine}
        </p>
      )}
      {phase !== 'notFound' && (
        <form className="message-form" onSubmit={handleSubmit}>
          {/* Read-only rather than disabled while it cannot send, so the box
              keeps the focus and the user can write on after an answer. */}
          <textarea
            aria-label="Message"
            placeholder="Write a message. Enter sends, Shift and Enter makes a new line."
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            readOnly={!canWrite}
            rows={3}
          />
          {phase === 'sending' ? (
            <button type="button" onClick={handleStop}>
              Stop
            </button>
          ) : (
            <button type="submit" disabled={!canSend}>
              Send
            </button>
          )}
        </form>
      )}
    </main>
  )
}

function textOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

export default ChatView
