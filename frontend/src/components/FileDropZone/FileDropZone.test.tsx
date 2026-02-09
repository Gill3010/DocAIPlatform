import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FileDropZone } from './FileDropZone'

const noop = () => {}

describe('FileDropZone', () => {
  const defaultProps = {
    onDragEnter: noop,
    onDragLeave: noop,
    onDragOver: noop,
    onDrop: noop,
    onFileChange: noop,
    isDragActive: false,
  }

  it('renders label "Seleccionar Archivo" and file input', () => {
    render(<FileDropZone {...defaultProps} />)
    expect(screen.getByText('Seleccionar Archivo')).toBeInTheDocument()
    expect(screen.getByLabelText('Seleccionar archivo')).toBeInTheDocument()
    expect(screen.getByLabelText('Seleccionar archivo')).toHaveAttribute('type', 'file')
  })

  it('renders main heading and format hints', () => {
    render(<FileDropZone {...defaultProps} />)
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent(/clic o arrastra/)
    expect(screen.getByText(/PNG, JPG, PDF/)).toBeInTheDocument()
  })

  it('uses custom inputId for input and label', () => {
    render(<FileDropZone {...defaultProps} inputId="convert-file" />)
    const input = screen.getByLabelText('Seleccionar archivo')
    expect(input).toHaveAttribute('id', 'convert-file')
    const label = screen.getByText('Seleccionar Archivo')
    expect(label).toHaveAttribute('for', 'convert-file')
  })

  it('renders hintText when provided', () => {
    render(<FileDropZone {...defaultProps} hintText="Convierte PDF a DOCX" />)
    expect(screen.getByText('Convierte PDF a DOCX')).toBeInTheDocument()
  })

  it('applies active class when isDragActive is true', () => {
    const { container } = render(<FileDropZone {...defaultProps} isDragActive />)
    const zone = container.querySelector('.file-drop-zone')
    expect(zone).toHaveClass('file-drop-zone--active')
  })
})
