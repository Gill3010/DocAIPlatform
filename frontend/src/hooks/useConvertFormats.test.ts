import { describe, it, expect } from 'vitest'
import { extensionMatchesUrlFrom, getAcceptForUrlFrom } from './useConvertFormats'

describe('useConvertFormats', () => {
  describe('extensionMatchesUrlFrom', () => {
    it('returns true when urlFrom is png and ext is png, jpg or jpeg', () => {
      expect(extensionMatchesUrlFrom('png', 'png')).toBe(true)
      expect(extensionMatchesUrlFrom('jpg', 'png')).toBe(true)
      expect(extensionMatchesUrlFrom('jpeg', 'png')).toBe(true)
    })

    it('returns false when urlFrom is png and ext is not image', () => {
      expect(extensionMatchesUrlFrom('pdf', 'png')).toBe(false)
      expect(extensionMatchesUrlFrom('docx', 'png')).toBe(false)
    })

    it('returns true when ext equals urlFrom for non-png', () => {
      expect(extensionMatchesUrlFrom('pdf', 'pdf')).toBe(true)
      expect(extensionMatchesUrlFrom('docx', 'docx')).toBe(true)
    })

    it('returns false when ext does not equal urlFrom', () => {
      expect(extensionMatchesUrlFrom('pdf', 'docx')).toBe(false)
    })
  })

  describe('getAcceptForUrlFrom', () => {
    it('returns empty string for empty urlFrom', () => {
      expect(getAcceptForUrlFrom('')).toBe('')
    })

    it('returns .png,.jpg,.jpeg for png, jpg or jpeg', () => {
      expect(getAcceptForUrlFrom('png')).toBe('.png,.jpg,.jpeg')
      expect(getAcceptForUrlFrom('jpg')).toBe('.png,.jpg,.jpeg')
      expect(getAcceptForUrlFrom('jpeg')).toBe('.png,.jpg,.jpeg')
    })

    it('returns .htm,.html for htm', () => {
      expect(getAcceptForUrlFrom('htm')).toBe('.htm,.html')
    })

    it('returns .html,.htm for html', () => {
      expect(getAcceptForUrlFrom('html')).toBe('.html,.htm')
    })

    it('returns single extension with dot for other formats', () => {
      expect(getAcceptForUrlFrom('pdf')).toBe('.pdf')
      expect(getAcceptForUrlFrom('docx')).toBe('.docx')
    })
  })
})
