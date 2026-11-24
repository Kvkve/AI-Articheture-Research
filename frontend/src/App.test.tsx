import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App.tsx'

describe('App', () => {
  it('shows the page heading', () => {
    render(<App />)

    const heading = screen.getByRole('heading', { name: 'AI Agent Platform' })

    expect(heading).toBeDefined()
  })
})
