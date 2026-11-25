import Markdown from 'react-markdown'
import type { Message } from './backend.ts'

type ChatMessageProps = {
  role: Message['role']
  text: string
}

// One message of the chat. The user's text is shown as it was written, with
// its line breaks. The assistant's text is drawn as Markdown. react-markdown
// keeps its default settings: it does not run or draw HTML that an answer
// holds, which keeps a script in an answer from reaching the token.
function ChatMessage({ role, text }: ChatMessageProps) {
  if (role === 'user') {
    return (
      <article className="message message-user" aria-label="Your message">
        <p className="user-text">{text}</p>
      </article>
    )
  }
  return (
    <article className="message message-assistant" aria-label="Answer">
      <Markdown>{text}</Markdown>
    </article>
  )
}

export default ChatMessage
