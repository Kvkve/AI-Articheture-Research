// The one module that talks to the backend. It is the only file that calls
// fetch: a rule in frontend/eslint.config.js refuses fetch in every other
// file. It knows the addresses, sends the token, and turns the answers into
// the project's own types and errors, so that a component never reads a
// status code.
//
// The types below are written by hand from the models of the backend:
// Token in backend/app/login.py, User in backend/app/users.py, Conversation
// in backend/app/conversations.py, the lists and messages in
// backend/app/protected.py.

import { readAnswerStream, StreamFormatError, type StreamMessage } from './answerStream.ts'

export type { StreamMessage }
export { StreamFormatError }

// Every call goes to the page's own address, under this prefix. The
// development server passes these calls on to the backend with the prefix
// taken off: see the proxy rule in frontend/vite.config.ts, which names the
// same prefix.
export const API_PREFIX = '/api'

export type User = {
  id: number
  username: string
}

export type Conversation = {
  id: string
  // null until the first message of the conversation gives it a title.
  title: string | null
  // Times in UTC, as text in the ISO 8601 form.
  created_at: string
  last_active_at: string
}

export type Message = {
  role: 'user' | 'assistant'
  text: string
}

// The token is missing, not valid or expired. The user must sign in again.
export class SignInAgainError extends Error {
  constructor() {
    super('Your sign-in has ended. Sign in again.')
    this.name = 'SignInAgainError'
  }
}

// The backend answered, but not with a success. The message is a text for
// the user.
export class BackendError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'BackendError'
    this.status = status
  }
}

// No answer came at all: the backend, or the development server in front of
// it, cannot be reached.
export class UnreachableError extends Error {
  constructor() {
    super('The backend cannot be reached. Try again later.')
    this.name = 'UnreachableError'
  }
}

// The user stopped the answer, or left the conversation while it arrived.
export class AnswerStoppedError extends Error {
  constructor() {
    super('The answer was stopped.')
    this.name = 'AnswerStoppedError'
  }
}

const GENERAL_ERROR_TEXT = 'Something went wrong on the server. Try again later.'

export async function signIn(username: string, password: string): Promise<string> {
  // The sign-in endpoint takes a form, not JSON, as the official FastAPI
  // template does. URLSearchParams makes fetch send it as a form.
  const form = new URLSearchParams({ username, password })
  // A 400 here means a wrong name or password, and a 401 cannot come, so
  // this call does not turn a 401 into "sign in again".
  const response = await send('/login/access-token', { method: 'POST', body: form })
  if (!response.ok) {
    throw await errorFromResponse(response)
  }
  const token = await readSuccessBody<{ access_token: string }>(response)
  return token.access_token
}

export async function getCurrentUser(token: string): Promise<User> {
  const response = await sendWithToken(token, '/users/me', { method: 'GET' })
  return readSuccessBody<User>(response)
}

export async function listConversations(token: string): Promise<Conversation[]> {
  const response = await sendWithToken(token, '/conversations', { method: 'GET' })
  const list = await readSuccessBody<{ conversations: Conversation[] }>(response)
  return list.conversations
}

export async function startConversation(token: string): Promise<Conversation> {
  const response = await sendWithToken(token, '/conversations', { method: 'POST' })
  return readSuccessBody<Conversation>(response)
}

export async function readHistory(token: string, conversationId: string): Promise<Message[]> {
  const response = await sendWithToken(token, messagesPath(conversationId), { method: 'GET' })
  const list = await readSuccessBody<{ messages: Message[] }>(response)
  return list.messages
}

// Sends a message. It returns when the backend has answered with status 200,
// that is when the stream starts. A refusal before the stream throws one of
// the errors above, and gives no stream.
//
// The returned messages arrive one by one. The caller tells four endings
// apart: an "end" message; an "error" message; a loop that ends with neither,
// which means the stream was cut off; and AnswerStoppedError, when the signal
// was aborted. A stream that breaks its format throws StreamFormatError.
export async function sendMessage(
  token: string,
  conversationId: string,
  text: string,
  signal: AbortSignal,
): Promise<AsyncGenerator<StreamMessage>> {
  let response: Response
  try {
    response = await sendWithToken(token, messagesPath(conversationId), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal,
    })
  } catch (error) {
    if (signal.aborted) {
      throw new AnswerStoppedError()
    }
    throw error
  }
  if (response.body === null) {
    throw new BackendError(response.status, GENERAL_ERROR_TEXT)
  }
  return readMessages(response.body, signal)
}

async function* readMessages(
  body: ReadableStream<Uint8Array>,
  signal: AbortSignal,
): AsyncGenerator<StreamMessage> {
  try {
    yield* readAnswerStream(body)
  } catch (error) {
    if (signal.aborted) {
      throw new AnswerStoppedError()
    }
    if (error instanceof StreamFormatError) {
      throw error
    }
    // Any other failure while reading is a connection that broke. It ends
    // the loop with no "end" and no "error", the same as a stream that the
    // backend closed early: the caller sees it as cut off.
  }
}

function messagesPath(conversationId: string): string {
  return `/conversations/${encodeURIComponent(conversationId)}/messages`
}

// Sends a request that needs the token. A 401 means "sign in again"; any
// other answer that is not a success becomes a BackendError.
async function sendWithToken(token: string, path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${token}`)
  const response = await send(path, { ...init, headers })
  if (response.status === 401) {
    throw new SignInAgainError()
  }
  if (!response.ok) {
    throw await errorFromResponse(response)
  }
  return response
}

async function send(path: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(API_PREFIX + path, init)
  } catch (error) {
    // A stop by the caller also lands here. The caller knows its own signal
    // and decides what it means, so the error goes on unchanged.
    if (init.signal?.aborted) {
      throw error
    }
    throw new UnreachableError()
  }
}

// Reads the JSON body of a success answer. A body that is not JSON, or a
// connection that breaks while the body arrives, becomes an error of this
// module with a text for the user, not a raw error of the browser.
async function readSuccessBody<T>(response: Response): Promise<T> {
  try {
    const body: T = await response.json()
    return body
  } catch {
    throw new BackendError(response.status, GENERAL_ERROR_TEXT)
  }
}

// The texts of the backend's errors are written for the user, so the page
// shows them as they are. A body of another shape gets a general text.
async function errorFromResponse(response: Response): Promise<BackendError> {
  let body: unknown
  try {
    body = await response.json()
  } catch {
    // For example the plain-text 500 of the framework.
    return new BackendError(response.status, GENERAL_ERROR_TEXT)
  }
  return new BackendError(response.status, textFromErrorBody(body))
}

function textFromErrorBody(body: unknown): string {
  if (typeof body !== 'object' || body === null || !('detail' in body)) {
    return GENERAL_ERROR_TEXT
  }
  const detail = body.detail
  if (typeof detail === 'string') {
    return detail
  }
  // A 422 has a list under "detail". Each entry names its problem in "msg".
  if (Array.isArray(detail) && detail.length > 0) {
    const first: unknown = detail[0]
    if (typeof first === 'object' && first !== null && 'msg' in first && typeof first.msg === 'string') {
      return first.msg
    }
  }
  return GENERAL_ERROR_TEXT
}
