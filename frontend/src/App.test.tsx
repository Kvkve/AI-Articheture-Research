import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'
import App from './App.tsx'

// The tests replace the browser's fetch with this function. It answers by
// the method and the address, like a small backend.
type Route = (init: RequestInit) => Response | Promise<Response>
let routes: Record<string, Route>
let fakeFetch: Mock<(input: string, init: RequestInit) => Promise<Response>>

function jsonAnswer(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const ALICE = { id: 1, username: 'alice' }
const NO_TITLE = {
  id: 'c1',
  title: null,
  created_at: '2026-11-25T10:00:00.000Z',
  last_active_at: '2026-11-25T10:00:00.000Z',
}

beforeEach(() => {
  sessionStorage.clear()
  window.location.hash = ''
  routes = {}
  fakeFetch = vi.fn(async (input: string, init: RequestInit) => {
    const route = routes[`${init.method} ${input}`]
    if (route === undefined) {
      return jsonAnswer(500, { detail: `No route in the test for ${init.method} ${input}` })
    }
    return route(init)
  })
  vi.stubGlobal('fetch', fakeFetch)
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

function signedInAsAlice(conversations: unknown[]) {
  sessionStorage.setItem('token', 'alice-token')
  routes['GET /api/users/me'] = () => jsonAnswer(200, ALICE)
  routes['GET /api/conversations'] = () => jsonAnswer(200, { conversations })
}

describe('App', () => {
  it('shows the sign-in form when the browser holds no token', () => {
    render(<App />)

    expect(screen.getByRole('textbox', { name: 'User name' })).toBeDefined()
    expect(screen.getByLabelText('Password')).toBeDefined()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDefined()
  })

  it('shows the text of the answer for a wrong name or password', async () => {
    routes['POST /api/login/access-token'] = () =>
      jsonAnswer(400, { detail: 'Incorrect user name or password' })
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByRole('textbox', { name: 'User name' }), 'alice')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect((await screen.findByRole('alert')).textContent).toBe('Incorrect user name or password')
  })

  it('signs in, stores the token and shows the main view', async () => {
    routes['POST /api/login/access-token'] = () => jsonAnswer(200, { access_token: 'alice-token' })
    routes['GET /api/users/me'] = () => jsonAnswer(200, ALICE)
    routes['GET /api/conversations'] = () =>
      jsonAnswer(200, { conversations: [{ ...NO_TITLE, id: 'c2', title: 'About tea' }, NO_TITLE] })
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByRole('textbox', { name: 'User name' }), 'alice')
    await user.type(screen.getByLabelText('Password'), 'right')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Signed in as alice')).toBeDefined()
    expect(sessionStorage.getItem('token')).toBe('alice-token')
    const list = screen.getByRole('navigation', { name: 'Conversations' })
    const links = await within(list).findAllByRole('link')
    // The order of the backend, and "New conversation" for no title.
    expect(links.map((link) => link.textContent)).toEqual(['About tea', 'New conversation'])
    expect(links[0].getAttribute('href')).toBe('#/conversations/c2')
  })

  it('removes a token that the backend refuses and shows the sign-in page', async () => {
    sessionStorage.setItem('token', 'old-token')
    routes['GET /api/users/me'] = () => jsonAnswer(401, { detail: 'Could not validate credentials' })
    render(<App />)

    expect(await screen.findByRole('button', { name: 'Sign in' })).toBeDefined()
    expect(sessionStorage.getItem('token')).toBeNull()
  })

  it('keeps the token when the backend cannot be reached', async () => {
    sessionStorage.setItem('token', 'alice-token')
    fakeFetch.mockRejectedValue(new TypeError('Failed to fetch'))
    render(<App />)

    expect((await screen.findByRole('alert')).textContent).toBe(
      'The backend cannot be reached. Try again later.',
    )
    expect(sessionStorage.getItem('token')).toBe('alice-token')
  })

  it('signs out with no call to the backend', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    routes['GET /api/conversations/c1/messages'] = () => jsonAnswer(200, { messages: [] })
    const user = userEvent.setup()
    render(<App />)

    await user.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDefined()
    expect(sessionStorage.getItem('token')).toBeNull()
    expect(window.location.hash).toBe('#/')
  })

  it('shows "Conversation not found" and no box for a message', async () => {
    signedInAsAlice([])
    window.location.hash = '#/conversations/of-bob'
    routes['GET /api/conversations/of-bob/messages'] = () =>
      jsonAnswer(404, { detail: 'Conversation not found' })
    render(<App />)

    expect((await screen.findByRole('alert')).textContent).toBe('Conversation not found')
    expect(screen.queryByRole('textbox', { name: 'Message' })).toBeNull()
  })

  it('shows the history: the user as written, the assistant as Markdown, no HTML', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    routes['GET /api/conversations/c1/messages'] = () =>
      jsonAnswer(200, {
        messages: [
          { role: 'user', text: 'Line one\n**not bold**' },
          { role: 'assistant', text: '## A heading\n\n<b>raw html</b> and **bold**' },
        ],
      })
    render(<App />)

    const question = await screen.findByRole('article', { name: 'Your message' })
    expect(question.textContent).toBe('Line one\n**not bold**')
    const answer = screen.getByRole('article', { name: 'Answer' })
    expect(within(answer).getByRole('heading', { name: 'A heading' })).toBeDefined()
    expect(answer.querySelector('strong')?.textContent).toBe('bold')
    expect(answer.querySelector('b')).toBeNull()
  })

  it('sends with Enter, shows the answer, and reads the list again', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    routes['GET /api/conversations/c1/messages'] = () => jsonAnswer(200, { messages: [] })
    routes['POST /api/conversations/c1/messages'] = () =>
      new Response(
        'data: {"type":"text","text":"Hello"}\n\ndata: {"type":"text","text":" **there**"}\n\ndata: {"type":"end"}\n\n',
        { status: 200, headers: { 'Content-Type': 'text/event-stream' } },
      )
    const user = userEvent.setup()
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })

    await user.type(box, 'Hi{Shift>}{Enter}{/Shift}there{Enter}')

    const answer = await screen.findByRole('article', { name: 'Answer' })
    expect(answer.textContent).toBe('Hello there')
    expect(screen.getByRole('article', { name: 'Your message' }).textContent).toBe('Hi\nthere')
    expect((box as HTMLTextAreaElement).value).toBe('')
    const sent = fakeFetch.mock.calls.find(([, init]) => init.method === 'POST')
    expect(sent?.[1].body).toBe('{"text":"Hi\\nthere"}')
    const listReads = fakeFetch.mock.calls.filter(
      ([input, init]) => input === '/api/conversations' && init.method === 'GET',
    )
    expect(listReads.length).toBe(2)
  })

  it('puts a refused message back into the box and shows the error', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    routes['GET /api/conversations/c1/messages'] = () => jsonAnswer(200, { messages: [] })
    routes['POST /api/conversations/c1/messages'] = () =>
      jsonAnswer(422, { detail: [{ loc: ['body', 'text'], msg: 'The message is too long.' }] })
    const user = userEvent.setup()
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })

    await user.type(box, 'Too long')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect((await screen.findByRole('alert')).textContent).toBe('The message is too long.')
    expect((box as HTMLTextAreaElement).value).toBe('Too long')
    expect(screen.queryByRole('article', { name: 'Your message' })).toBeNull()
  })

  it('cannot send a text that is only white space', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    routes['GET /api/conversations/c1/messages'] = () => jsonAnswer(200, { messages: [] })
    const user = userEvent.setup()
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })

    await user.type(box, '   {Enter}')

    expect((screen.getByRole('button', { name: 'Send' }) as HTMLButtonElement).disabled).toBe(true)
    expect(fakeFetch.mock.calls.some(([, init]) => init.method === 'POST')).toBe(false)
  })

  it('says that the connection was lost when the stream closes early, and reads the history', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    let historyReads = 0
    routes['GET /api/conversations/c1/messages'] = () => {
      historyReads += 1
      const messages = historyReads === 1 ? [] : [{ role: 'user', text: 'Hi' }]
      return jsonAnswer(200, { messages })
    }
    routes['POST /api/conversations/c1/messages'] = () =>
      new Response('data: {"type":"text","text":"Hal"}\n\n', { status: 200 })
    const user = userEvent.setup()
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })

    await user.type(box, 'Hi{Enter}')

    expect((await screen.findByRole('alert')).textContent).toBe(
      'The connection was lost before the answer ended.',
    )
    await screen.findByRole('button', { name: 'Send' })
    expect(historyReads).toBe(2)
    expect(screen.queryByRole('article', { name: 'Answer' })).toBeNull()
    expect(screen.getByRole('article', { name: 'Your message' }).textContent).toBe('Hi')
  })

  it('shows the message of an "error" ending and then what the history holds', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    let historyReads = 0
    routes['GET /api/conversations/c1/messages'] = () => {
      historyReads += 1
      const messages = historyReads === 1 ? [] : [{ role: 'user', text: 'Hi' }]
      return jsonAnswer(200, { messages })
    }
    routes['POST /api/conversations/c1/messages'] = () =>
      new Response(
        'data: {"type":"text","text":"Part"}\n\ndata: {"type":"error","message":"The answer could not be completed."}\n\n',
        { status: 200 },
      )
    const user = userEvent.setup()
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })

    await user.type(box, 'Hi{Enter}')

    expect((await screen.findByRole('alert')).textContent).toBe('The answer could not be completed.')
    await vi.waitFor(() => expect(screen.queryByRole('article', { name: 'Answer' })).toBeNull())
    expect(historyReads).toBe(2)
  })

  it('stops an answer: closes the connection, says so, and reads the history', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    let historyReads = 0
    routes['GET /api/conversations/c1/messages'] = () => {
      historyReads += 1
      const messages = historyReads === 1 ? [] : [{ role: 'user', text: 'Hi' }]
      return jsonAnswer(200, { messages })
    }
    let closedByPage = false
    routes['POST /api/conversations/c1/messages'] = (init) => {
      // One piece, then the stream stays open until the page closes it, and
      // fails then as a fetch body does.
      const body = new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('data: {"type":"text","text":"Part"}\n\n'))
          init.signal?.addEventListener('abort', () => {
            closedByPage = true
            controller.error(new DOMException('The operation was aborted.', 'AbortError'))
          })
        },
      })
      return new Response(body, { status: 200 })
    }
    const user = userEvent.setup()
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })
    await user.type(box, 'Hi{Enter}')
    await screen.findByRole('article', { name: 'Answer' })

    await user.click(screen.getByRole('button', { name: 'Stop' }))

    expect(await screen.findByText('The answer was stopped.')).toBeDefined()
    expect(closedByPage).toBe(true)
    await vi.waitFor(() => expect(screen.queryByRole('article', { name: 'Answer' })).toBeNull())
    expect(historyReads).toBe(2)
    expect(screen.getByRole('article', { name: 'Your message' }).textContent).toBe('Hi')
  })

  it('does not send on Enter while an input method composes a text', async () => {
    signedInAsAlice([NO_TITLE])
    window.location.hash = '#/conversations/c1'
    routes['GET /api/conversations/c1/messages'] = () => jsonAnswer(200, { messages: [] })
    render(<App />)
    const box = await screen.findByRole('textbox', { name: 'Message' })
    await screen.findByRole('button', { name: 'Send' })
    fireEvent.change(box, { target: { value: 'ni hao' } })

    fireEvent.keyDown(box, { key: 'Enter', isComposing: true })
    fireEvent.keyDown(box, { key: 'Enter', keyCode: 229 })

    expect(fakeFetch.mock.calls.some(([, init]) => init.method === 'POST')).toBe(false)
    expect((box as HTMLTextAreaElement).value).toBe('ni hao')
  })
})
