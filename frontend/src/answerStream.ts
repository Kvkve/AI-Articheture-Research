// Reads the stream of an answer: the Server-Sent Events that the backend
// sends after a message. This file makes no network call. It takes the body
// of a response as the browser gives it, a stream of byte chunks, so the unit
// tests can feed it chunks cut in any place.
//
// The format is the contract in SEND_MESSAGE_DESCRIPTION, in
// backend/app/protected.py.

export type StreamMessage =
  | { type: 'text'; text: string }
  | { type: 'end' }
  | { type: 'error'; message: string }

// The stream broke its own format. The text is for the user.
export class StreamFormatError extends Error {
  constructor() {
    super('The answer arrived in a form that the page cannot read.')
    this.name = 'StreamFormatError'
  }
}

// Gives the messages one by one, as they arrive. It returns when the stream
// closes. It does not stop at "end" or "error": the caller sees those as
// messages, and sees the close as the end of the loop. A stream that closes
// with neither was cut off.
export async function* readAnswerStream(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<StreamMessage> {
  const reader = body.getReader()
  // With "stream: true" the decoder keeps the first bytes of a character
  // that a chunk cuts in two, and finishes it with the next chunk.
  const decoder = new TextDecoder()
  // The text after the last line break: the start of a line not yet ended.
  let unfinishedLine = ''
  // The "data:" lines of the message being read, before its empty line.
  let dataLines: string[] = []

  try {
    while (true) {
      const { done, value } = await reader.read()
      const text = done ? decoder.decode() : decoder.decode(value, { stream: true })
      const lines = (unfinishedLine + text).split(/\r\n|\n/)
      // The last part has no line break after it yet. A carriage return at
      // the very end of a chunk stays here, so it meets its line feed.
      unfinishedLine = lines.pop() ?? ''

      for (const line of lines) {
        if (line === '') {
          // An empty line ends a message.
          if (dataLines.length > 0) {
            const message = parseMessage(dataLines.join('\n'))
            dataLines = []
            if (message !== null) {
              yield message
            }
          }
        } else if (line.startsWith('data:')) {
          dataLines.push(withoutOneLeadingSpace(line.slice('data:'.length)))
        }
        // Any other line is skipped: a comment, which begins with a colon,
        // or a field that this frontend does not use.
      }

      if (done) {
        // A message with no empty line after it was cut off. The format of
        // Server-Sent Events drops it, and so does this reader.
        return
      }
    }
  } finally {
    // Runs also when the caller stops reading early. Cancelling closes the
    // connection, which tells the backend to stop the model.
    await reader.cancel().catch(() => undefined)
  }
}

function withoutOneLeadingSpace(value: string): string {
  return value.startsWith(' ') ? value.slice(1) : value
}

// Returns null for a kind that this reader does not know: a later backend may
// send new kinds, and this frontend must still work.
function parseMessage(data: string): StreamMessage | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(data)
  } catch {
    throw new StreamFormatError()
  }
  if (!isRecord(parsed) || typeof parsed.type !== 'string') {
    throw new StreamFormatError()
  }

  switch (parsed.type) {
    case 'text':
      if (typeof parsed.text !== 'string') {
        throw new StreamFormatError()
      }
      return { type: 'text', text: parsed.text }
    case 'end':
      return { type: 'end' }
    case 'error':
      if (typeof parsed.message !== 'string') {
        throw new StreamFormatError()
      }
      return { type: 'error', message: parsed.message }
    default:
      return null
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
