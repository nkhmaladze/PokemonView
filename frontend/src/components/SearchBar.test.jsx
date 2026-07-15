import { describe, expect, it, vi } from 'vitest'
import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBar from './SearchBar'

/** Stateful wrapper so userEvent.type can drive a genuinely controlled
 * input (a fixed-value/no-op-onChange input would revert every
 * keystroke) while still letting the test assert exactly what
 * onChange received. */
function ControlledSearchBar({ onChange }) {
  const [value, setValue] = useState('')
  return (
    <SearchBar
      value={value}
      onChange={(next) => {
        setValue(next)
        onChange(next)
      }}
    />
  )
}

describe('SearchBar', () => {
  it('renders a controlled text input bound to the value prop with the locked placeholder', () => {
    render(<SearchBar value="Pitch" onChange={() => {}} />)
    const input = screen.getByPlaceholderText('Search by product name or set…')
    expect(input).toHaveValue('Pitch')
  })

  it('has an accessible name so it is queryable by role', () => {
    render(<SearchBar value="" onChange={() => {}} />)
    expect(screen.getByRole('textbox', { name: /search/i })).toBeInTheDocument()
  })

  it('fires onChange with each typed character immediately, no submit/debounce', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<ControlledSearchBar onChange={onChange} />)

    const input = screen.getByRole('textbox', { name: /search/i })
    await user.type(input, 'Box')

    expect(onChange).toHaveBeenCalledTimes(3)
    expect(onChange).toHaveBeenNthCalledWith(1, 'B')
    expect(onChange).toHaveBeenNthCalledWith(2, 'Bo')
    expect(onChange).toHaveBeenNthCalledWith(3, 'Box')
    expect(input).toHaveValue('Box')
  })
})
