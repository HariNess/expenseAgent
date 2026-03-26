import React, { useRef, useState } from 'react'

export default function FileUpload({ onFileSelect, disabled, onFeedback }) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFile = (file) => {
    if (!file) return
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
    if (!allowed.includes(file.type)) {
      onFeedback?.('Please upload a JPG, PNG, WEBP, or PDF file.', 'warning')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      onFeedback?.('File size must be under 10MB.', 'warning')
      return
    }
    onFeedback?.(`Selected ${file.name}.`, 'info')
    onFileSelect(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/*,.pdf"
        style={{ display: 'none' }}
        onChange={(e) => handleFile(e.target.files[0])}
      />
      <button
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        disabled={disabled}
        title="Upload invoice"
        style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          border: `1.5px solid ${dragOver ? 'var(--accent)' : 'var(--border)'}`,
          background: dragOver ? 'var(--accent-glow)' : 'var(--bg-input)',
          color: disabled ? 'var(--text-muted)' : 'var(--text-secondary)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s',
          flexShrink: 0,
          fontSize: 16,
        }}
      >
        📎
      </button>
    </>
  )
}
