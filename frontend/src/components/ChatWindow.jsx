import React, { useState, useRef, useEffect } from 'react'
import MessageBubble, { TypingIndicator } from './MessageBubble'
import FileUpload from './FileUpload'
import ExpenseTable from './ExpenseTable'
import { sendMessage, uploadInvoice, submitExpense, editField } from '../utils/api'

const QUICK_ACTIONS = [
  { label: 'Upload Invoice', action: 'upload' },
  { label: 'Show My Expenses', action: 'my expenses' },
  { label: 'Get Help', action: 'help' },
]

export default function ChatWindow({ employeeEmail, onActionFeedback }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Welcome to **NessExpense**.\n\nUpload a tax invoice or bill and I will extract the details, validate the submission, and route it through the correct approval path.\n\nStart with a document when you're ready.`,
      timestamp: now(),
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [pendingExpense, setPendingExpense] = useState(null)
  const [sessionId] = useState(() => `${employeeEmail}-${Date.now()}`)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping, pendingExpense])

  const addMessage = (role, content, extra = {}) => {
    setMessages(prev => [...prev, { role, content, timestamp: now(), ...extra }])
  }

  const handleSend = async (text = input) => {
    if (!text.trim()) return
    setInput('')
    addMessage('user', text)
    setIsTyping(true)

    try {
      const data = await sendMessage(text, employeeEmail, [], sessionId)
      addMessage('assistant', data.message)
    } catch (e) {
      addMessage('assistant', "I'm having trouble connecting right now. Please try again in a moment.")
    } finally {
      setIsTyping(false)
    }
  }

  const handleFileUpload = async (file) => {
    addMessage('user', file.name, { type: 'file' })
    onActionFeedback?.(`Uploading ${file.name}...`, 'info')
    setIsTyping(true)

    try {
      const data = await uploadInvoice(file, employeeEmail, sessionId)

      if (data.status === 'fraud_detected') {
        addMessage('assistant', data.message)
        setPendingExpense(null)
        onActionFeedback?.('Invoice flagged for review. Please check the guidance in chat.', 'warning')
      } else if (data.status === 'extracted') {
        addMessage('assistant', data.message)
        setPendingExpense(data.extracted_data)
        onActionFeedback?.('Invoice details extracted. Review the fields before submitting.', 'success')
      } else {
        addMessage('assistant', data.message || "Something went wrong processing your document.")
        onActionFeedback?.(data.message || 'Document processing did not complete.', 'warning')
      }
    } catch (e) {
      addMessage('assistant', "I had trouble reading that document. Please try uploading a clearer image.")
      onActionFeedback?.('Upload failed. Please try a clearer invoice image or PDF.', 'error')
    } finally {
      setIsTyping(false)
    }
  }

  const handleExpenseUpdate = async (field, newValue) => {
    try {
      const data = await editField(employeeEmail, sessionId, field, newValue)
      if (data.extracted_data) {
        setPendingExpense(data.extracted_data)
      }
      onActionFeedback?.(`${field.replace(/_/g, ' ')} updated.`, 'success')
    } catch (e) {
      console.error(e)
      onActionFeedback?.('Could not update that field right now.', 'error')
    }
  }

  const handleExpenseSubmit = async () => {
    setIsTyping(true)
    setPendingExpense(null)
    try {
      const data = await submitExpense(employeeEmail, sessionId)
      const assistantMessages = Array.isArray(data.messages) && data.messages.length
        ? data.messages
        : [data.message]

      assistantMessages.forEach(message => addMessage('assistant', message))
      onActionFeedback?.(`Expense ${data.expense_id} submitted successfully.`, 'success')
    } catch (e) {
      addMessage('assistant', "There was an issue submitting your expense. Please try again.")
      onActionFeedback?.('Expense submission failed. Please try again.', 'error')
    } finally {
      setIsTyping(false)
    }
  }

  const handleExpenseCancel = () => {
    setPendingExpense(null)
    addMessage('assistant', "No problem! The expense has been cancelled. Upload a new document whenever you're ready.")
    onActionFeedback?.('Draft expense cancelled.', 'info')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      minHeight: 0,
      position: 'relative',
    }}>
      {/* Messages area */}
      <div style={{
        flex: 1,
        minHeight: 0,
        overflowY: 'auto',
        padding: '26px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        background:
          'linear-gradient(180deg, rgba(251, 253, 255, 0.74), rgba(237, 244, 252, 0.78))',
      }}>
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            isLatest={i === messages.length - 1}
          />
        ))}

        {/* Inline expense table */}
        {pendingExpense && !isTyping && (
          <div style={{ animation: 'fadeInUp 0.3s ease' }}>
            <ExpenseTable
              data={pendingExpense}
              onUpdate={handleExpenseUpdate}
              onSubmit={handleExpenseSubmit}
              onCancel={handleExpenseCancel}
            />
          </div>
        )}

        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Quick actions */}
      {messages.length <= 1 && (
        <div style={{
          padding: '0 28px 14px',
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
        }}>
          {QUICK_ACTIONS.map(({ label, action }) => (
            <button
              key={action}
              onClick={() => action === 'upload' ? null : handleSend(action)}
              style={{
                padding: '6px 14px',
                borderRadius: 999,
                border: '1px solid var(--border)',
                background: 'rgba(255, 255, 255, 0.92)',
                color: 'var(--text-secondary)',
                fontSize: 12,
                cursor: 'pointer',
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = 'var(--accent)'
                e.currentTarget.style.color = 'var(--text-primary)'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.color = 'var(--text-secondary)'
              }}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div style={{
        padding: '16px 22px 22px',
        borderTop: '1px solid var(--border)',
        background: 'rgba(237, 244, 252, 0.92)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          marginBottom: 12,
        }}>
          <div>
            <div style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 16,
              color: 'var(--text-primary)',
            }}>
              Submission Workspace
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Message the assistant or attach an invoice to begin extraction.
            </div>
          </div>
          <div style={{
            fontSize: 11,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            fontWeight: 700,
          }}>
            Ness Workflow
          </div>
        </div>
        <div style={{
          display: 'flex',
          gap: 10,
          alignItems: 'flex-end',
          background: 'rgba(255, 255, 255, 0.92)',
          border: '1px solid var(--border)',
          borderRadius: 22,
          padding: '10px 10px 10px 16px',
          transition: 'border-color 0.2s',
        }}
          onFocus={() => {}}
          onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
          onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
        >
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message NessExpense..."
            rows={1}
            disabled={isTyping}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: 14,
              fontFamily: 'var(--font-body)',
              resize: 'none',
              lineHeight: 1.5,
              maxHeight: 120,
              overflowY: 'auto',
              paddingTop: 4,
            }}
          />

          <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', paddingBottom: 2 }}>
            <FileUpload
              onFileSelect={handleFileUpload}
              disabled={isTyping}
              onFeedback={onActionFeedback}
            />

            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                border: 'none',
              background: input.trim() && !isTyping
                  ? 'linear-gradient(135deg, var(--accent), var(--accent-soft))'
                  : 'var(--bg-hover)',
                color: input.trim() && !isTyping ? '#fff' : 'var(--text-muted)',
                cursor: input.trim() && !isTyping ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s',
                flexShrink: 0,
                boxShadow: input.trim() && !isTyping
                  ? '0 10px 18px rgba(3,38,71,0.22)'
                  : 'none',
                fontSize: 16,
              }}
            >
              ➤
            </button>
          </div>
        </div>

        <div style={{
          textAlign: 'center',
          fontSize: 11,
          color: 'var(--text-muted)',
          marginTop: 8,
        }}>
          NessExpense workflow console
        </div>
      </div>
    </div>
  )
}

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
