import { describe, expect, it } from 'vitest'
import { readAnswerStream, StreamFormatError, type StreamMessage } from './answerStream.ts'

const encoder = new TextEncoder()

// A body that gives these chunks, in this order, then closes. A string is
// sent as its UTF-8 bytes.
function bodyOf(chunks: (string | Uint8Array)[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk)
      }
      controller.close()
    },
  })
}

async function readAll(chunks: (string | Uint8Array)[]): Promise<StreamMessage[]> {
  const messages: StreamMessage[] = []
  for await (const message of readAnswerStream(bodyOf(chunks))) {
    messages.push(message)
  }
  return messages
}

// A whole stream as the backend sends it: two pieces of text and the end.
const WHOLE_STREAM =
  'data: {"type":"text","text":"Hello"}\n\n' +
  'data: {"type":"text","text":", 世界"}\n\n' +
  'data: {"type":"end"}\n\n'

const WHOLE_STREAM_MESSAGES: StreamMessage[] = [
  { type: 'text', text: 'Hello' },
  { type: 'text', text: ', 世界' },
  { type: 'end' },
]

describe('readAnswerStream', () => {
  it('reads the three kinds of message', async () => {
    const messages = await readAll([
      'data: {"type":"text","text":"a\\nb"}\n\n',
      'data: {"type":"error","message":"The answer failed."}\n\n',
    ])

    expect(messages).toEqual([
      { type: 'text', text: 'a\nb' },
      { type: 'error', message: 'The answer failed.' },
    ])
  })

  it('reads a message cut in two chunks', async () => {
    const messages = await readAll(['data: {"type":"te', 'xt","text":"Hello"}\n\n'])

    expect(messages).toEqual([{ type: 'text', text: 'Hello' }])
  })

  it('reads a message whose empty line comes in the next chunk', async () => {
    const messages = await readAll(['data: {"type":"end"}\n', '\n'])

    expect(messages).toEqual([{ type: 'end' }])
  })

  it('reads two messages in one chunk', async () => {
    const messages = await readAll([
      'data: {"type":"text","text":"one"}\n\ndata: {"type":"text","text":"two"}\n\n',
    ])

    expect(messages).toEqual([
      { type: 'text', text: 'one' },
      { type: 'text', text: 'two' },
    ])
  })

  it('reads a character of several bytes cut between two chunks', async () => {
    const bytes = encoder.encode('data: {"type":"text","text":"中文"}\n\n')
    // "中" takes three bytes in UTF-8. Cut after the first of them.
    const cut = bytes.indexOf(0xe4) + 1

    const messages = await readAll([bytes.slice(0, cut), bytes.slice(cut)])

    expect(messages).toEqual([{ type: 'text', text: '中文' }])
  })

  it('gives the same messages however the bytes are cut', async () => {
    const bytes = encoder.encode(WHOLE_STREAM)

    for (let cut = 1; cut < bytes.length; cut++) {
      const messages = await readAll([bytes.slice(0, cut), bytes.slice(cut)])
      expect(messages, `cut after byte ${cut}`).toEqual(WHOLE_STREAM_MESSAGES)
    }
    const oneByteAtATime = Array.from(bytes, (byte) => Uint8Array.of(byte))
    expect(await readAll(oneByteAtATime)).toEqual(WHOLE_STREAM_MESSAGES)
  })

  it('skips a comment line', async () => {
    const messages = await readAll([': ping\n\n', 'data: {"type":"end"}\n\n'])

    expect(messages).toEqual([{ type: 'end' }])
  })

  it('ignores a line of another field', async () => {
    const messages = await readAll(['event: something\nid: 7\ndata: {"type":"end"}\n\n'])

    expect(messages).toEqual([{ type: 'end' }])
  })

  it('skips a kind that it does not know', async () => {
    const messages = await readAll([
      'data: {"type":"reasoning","text":"thinking"}\n\n',
      'data: {"type":"text","text":"Hello"}\n\n',
      'data: {"type":"end"}\n\n',
    ])

    expect(messages).toEqual([{ type: 'text', text: 'Hello' }, { type: 'end' }])
  })

  it('reads lines that end with a carriage return and a line feed', async () => {
    const messages = await readAll([
      'data: {"type":"text","text":"Hello"}\r\n\r\n: ping\r\n\r\ndata: {"type":"end"}\r\n\r\n',
    ])

    expect(messages).toEqual([{ type: 'text', text: 'Hello' }, { type: 'end' }])
  })

  it('reads a carriage return and its line feed cut between two chunks', async () => {
    const messages = await readAll(['data: {"type":"end"}\r', '\n\r', '\n'])

    expect(messages).toEqual([{ type: 'end' }])
  })

  it('reads "data:" with and without the space after the colon', async () => {
    const messages = await readAll([
      'data: {"type":"text","text":"with"}\n\n',
      'data:{"type":"text","text":"without"}\n\n',
    ])

    expect(messages).toEqual([
      { type: 'text', text: 'with' },
      { type: 'text', text: 'without' },
    ])
  })

  it('ends with no "end" and no "error" when the stream closes early', async () => {
    const messages = await readAll(['data: {"type":"text","text":"Hel"}\n\n', 'data: {"type":"te'])

    // The loop simply ends: the caller sees that neither ending came.
    expect(messages).toEqual([{ type: 'text', text: 'Hel' }])
  })

  it('ends with no messages when the stream is empty', async () => {
    expect(await readAll([])).toEqual([])
  })

  it('reports a "data:" line that is not JSON as an error of its own', async () => {
    const reading = readAll(['data: {"type":"text","text":"ok"}\n\n', 'data: not json\n\n'])

    await expect(reading).rejects.toBeInstanceOf(StreamFormatError)
  })

  it('reports a known kind that lacks its field', async () => {
    await expect(readAll(['data: {"type":"text"}\n\n'])).rejects.toBeInstanceOf(StreamFormatError)
    await expect(readAll(['data: {"type":"error"}\n\n'])).rejects.toBeInstanceOf(StreamFormatError)
  })

  it('reports JSON that is not an object with a type', async () => {
    await expect(readAll(['data: [1, 2]\n\n'])).rejects.toBeInstanceOf(StreamFormatError)
    await expect(readAll(['data: {"text":"no type"}\n\n'])).rejects.toBeInstanceOf(StreamFormatError)
  })

  it('cancels the body when the caller stops reading early', async () => {
    let cancelled = false
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"type":"text","text":"one"}\n\n'))
        // The stream stays open, as an answer that is still arriving.
      },
      cancel() {
        cancelled = true
      },
    })

    for await (const message of readAnswerStream(body)) {
      expect(message).toEqual({ type: 'text', text: 'one' })
      break
    }

    expect(cancelled).toBe(true)
  })
})
