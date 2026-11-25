import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'
import {
  AnswerStoppedError,
  BackendError,
  getCurrentUser,
  listConversations,
  readHistory,
  sendMessage,
  signIn,
  SignInAgainError,
  UnreachableError,
  type StreamMessage,
} from './backend.ts'

// The tests replace the browser's fetch, so no request leaves the test.
let fakeFetch: Mock<(input: string, init: RequestInit) => Promise<Response>>

beforeEach(() => {
  fakeFetch = vi.fn()
  vi.stubGlobal('fetch', fakeFetch)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function jsonAnswer(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function streamAnswer(text: string): Response {
  return new Response(text, { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
}

describe('backend', () => {
  it('sends the token in the header Authorization, under the prefix /api', async () => {
    fakeFetch.mockResolvedValue(jsonAnswer(200, { id: 1, username: 'alice' }))

    const user = await getCurrentUser('the-token')

    expect(user).toEqual({ id: 1, username: 'alice' })
    const [address, init] = fakeFetch.mock.calls[0]
    expect(address).toBe('/api/users/me')
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer the-token')
  })

  it('turns a 401 into the error "sign in again"', async () => {
    fakeFetch.mockResolvedValue(jsonAnswer(401, { detail: 'Could not validate credentials' }))

    await expect(listConversations('old-token')).rejects.toBeInstanceOf(SignInAgainError)
  })

  it('signs in with a form, not JSON', async () => {
    fakeFetch.mockResolvedValue(jsonAnswer(200, { access_token: 'new-token', token_type: 'bearer' }))

    const token = await signIn('alice', 'a password & more')

    expect(token).toBe('new-token')
    const [address, init] = fakeFetch.mock.calls[0]
    expect(address).toBe('/api/login/access-token')
    expect(init.method).toBe('POST')
    expect(init.body).toBeInstanceOf(URLSearchParams)
    expect(String(init.body)).toBe('username=alice&password=a+password+%26+more')
  })

  it('takes the text of an error from "detail" when it is a string', async () => {
    fakeFetch.mockResolvedValue(jsonAnswer(400, { detail: 'Incorrect user name or password' }))

    const error = await signIn('alice', 'wrong').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(BackendError)
    expect((error as BackendError).status).toBe(400)
    expect((error as BackendError).message).toBe('Incorrect user name or password')
  })

  it('takes the text of a 422 from the "msg" of the first entry', async () => {
    fakeFetch.mockResolvedValue(
      jsonAnswer(422, {
        detail: [
          { type: 'string_too_long', loc: ['body', 'text'], msg: 'The message is longer than 20000 characters.' },
          { type: 'other', loc: ['body'], msg: 'A second problem.' },
        ],
      }),
    )

    const error = await sendMessage('t', 'c1', 'x', new AbortController().signal).catch(
      (caught: unknown) => caught,
    )

    expect(error).toBeInstanceOf(BackendError)
    expect((error as BackendError).status).toBe(422)
    expect((error as BackendError).message).toBe('The message is longer than 20000 characters.')
  })

  it('gives a general text for a body that is not JSON', async () => {
    fakeFetch.mockResolvedValue(
      new Response('Internal Server Error', { status: 500, headers: { 'Content-Type': 'text/plain' } }),
    )

    const error = await readHistory('t', 'c1').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(BackendError)
    expect((error as BackendError).status).toBe(500)
    expect((error as BackendError).message).toBe('Something went wrong on the server. Try again later.')
  })

  it('turns a call that gets no answer into UnreachableError', async () => {
    fakeFetch.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(listConversations('t')).rejects.toBeInstanceOf(UnreachableError)
  })

  it('sends a message as JSON and gives the messages of the stream', async () => {
    fakeFetch.mockResolvedValue(
      streamAnswer('data: {"type":"text","text":"Hi"}\n\ndata: {"type":"end"}\n\n'),
    )

    const stream = await sendMessage('t', 'c1', 'Hello', new AbortController().signal)
    const messages: StreamMessage[] = []
    for await (const message of stream) {
      messages.push(message)
    }

    expect(messages).toEqual([{ type: 'text', text: 'Hi' }, { type: 'end' }])
    const [address, init] = fakeFetch.mock.calls[0]
    expect(address).toBe('/api/conversations/c1/messages')
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"text":"Hello"}')
    expect(new Headers(init.headers).get('Content-Type')).toBe('application/json')
  })

  it('refuses before the stream with an error and no stream', async () => {
    fakeFetch.mockResolvedValue(jsonAnswer(409, { detail: 'The conversation is busy.' }))

    await expect(sendMessage('t', 'c1', 'Hello', new AbortController().signal)).rejects.toThrow(
      'The conversation is busy.',
    )
  })

  it('turns a stop by the user while the answer arrives into AnswerStoppedError', async () => {
    const controller = new AbortController()
    // A body that sends one piece and stays open, then fails as a fetch body
    // does when its signal is aborted.
    const body = new ReadableStream<Uint8Array>({
      start(streamController) {
        streamController.enqueue(new TextEncoder().encode('data: {"type":"text","text":"Hi"}\n\n'))
        controller.signal.addEventListener('abort', () => {
          streamController.error(new DOMException('The operation was aborted.', 'AbortError'))
        })
      },
    })
    fakeFetch.mockResolvedValue(new Response(body, { status: 200 }))

    const stream = await sendMessage('t', 'c1', 'Hello', controller.signal)
    const first = await stream.next()
    controller.abort()

    expect(first.value).toEqual({ type: 'text', text: 'Hi' })
    await expect(stream.next()).rejects.toBeInstanceOf(AnswerStoppedError)
  })

  it('turns a stop before the backend answers into AnswerStoppedError', async () => {
    const controller = new AbortController()
    controller.abort()
    fakeFetch.mockRejectedValue(new DOMException('The operation was aborted.', 'AbortError'))

    await expect(sendMessage('t', 'c1', 'Hello', controller.signal)).rejects.toBeInstanceOf(
      AnswerStoppedError,
    )
  })
})
