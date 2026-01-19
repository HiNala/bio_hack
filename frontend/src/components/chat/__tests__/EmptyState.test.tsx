import { render, screen, fireEvent } from '@testing-library/react'
import { EmptyState } from '../EmptyState'

describe('EmptyState', () => {
  const mockOnExampleClick = jest.fn()

  beforeEach(() => {
    mockOnExampleClick.mockClear()
  })

  it('renders the empty state with title and description', () => {
    render(<EmptyState onExampleClick={mockOnExampleClick} />)

    expect(screen.getByText('Scientific Literature Intelligence')).toBeInTheDocument()
    expect(screen.getByText(/State a research question/)).toBeInTheDocument()
  })

  it('renders example queries', () => {
    render(<EmptyState onExampleClick={mockOnExampleClick} />)

    expect(screen.getByText(/What is experimentally verified/)).toBeInTheDocument()
    expect(screen.getByText(/What disagreements exist/)).toBeInTheDocument()
  })

  it('calls onExampleClick when an example is clicked', () => {
    render(<EmptyState onExampleClick={mockOnExampleClick} />)

    const firstExample = screen.getByText(/What is experimentally verified/)
    fireEvent.click(firstExample)

    expect(mockOnExampleClick).toHaveBeenCalledWith(
      "What is experimentally verified vs theoretical in quantum decoherence?"
    )
  })

  it('renders method badges', () => {
    render(<EmptyState onExampleClick={mockOnExampleClick} />)

    expect(screen.getByText('Multi-source search')).toBeInTheDocument()
    expect(screen.getByText('Evidence ranking')).toBeInTheDocument()
    expect(screen.getByText('Citation linking')).toBeInTheDocument()
  })
})