import React, { useState, useEffect } from 'react'
import { getPendingApprovals, takeApprovalAction } from '../utils/api'

export default function ApprovalPanel({ approverEmail, stage, onActionFeedback }) {
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(null)
  const [comments, setComments] = useState({})
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    fetchPending(true)
  }, [approverEmail, stage])

  const fetchPending = async (silent = false) => {
    setLoading(true)
    try {
      const data = await getPendingApprovals(approverEmail, stage)
      setPending(data.pending || [])
      if (!silent) {
        onActionFeedback?.('Approval queue refreshed.', 'info')
      }
    } catch (e) {
      console.error(e)
      if (!silent) {
        onActionFeedback?.('Could not refresh the approval queue.', 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (expenseId, action) => {
    if (action === 'reject' && !comments[expenseId]?.trim()) {
      onActionFeedback?.('Please provide a reason before rejecting this expense.', 'warning')
      return
    }
    setProcessing(expenseId)
    try {
      const result = await takeApprovalAction(
        expenseId,
        action,
        comments[expenseId] || '',
        approverEmail,
        stage
      )
      setPending(prev => prev.filter(e => e.expense_id !== expenseId))
      setExpanded((current) => (current === expenseId ? null : current))
      onActionFeedback?.(
        result.message || `Expense ${expenseId} ${action === 'approve' ? 'approved' : 'rejected'}.`,
        action === 'approve' ? 'success' : 'warning'
      )
    } catch (e) {
      onActionFeedback?.('Action failed. Please try again.', 'error')
    } finally {
      setProcessing(null)
    }
  }

  if (loading) return (
    <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
      <div style={{
        width: 24, height: 24, border: '2px solid var(--border)',
        borderTopColor: 'var(--accent)', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite', margin: '0 auto 12px'
      }} />
      Loading pending approvals...
    </div>
  )

  return (
    <div style={{ padding: '20px', maxWidth: 800, margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 20,
      }}>
        <div>
          <h2 style={{
            fontFamily: 'var(--font-display)', fontWeight: 800,
            fontSize: 20, color: 'var(--text-primary)',
          }}>
            {stage === 'manager' ? 'Manager Approval Queue' : 'HR Approval Queue'}
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
            {pending.length} pending {pending.length === 1 ? 'request' : 'requests'}
          </p>
        </div>
        <button
          onClick={() => fetchPending(false)}
          style={{
            padding: '8px 14px', borderRadius: 8,
            border: '1px solid var(--border)', background: 'rgba(255,255,255,0.45)',
            color: 'var(--text-secondary)', cursor: 'pointer',
            fontSize: 12, fontFamily: 'var(--font-display)', fontWeight: 600,
          }}
        >
          Refresh
        </button>
      </div>

      {pending.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: 60,
          background: 'var(--bg-card)', borderRadius: 'var(--radius)',
          border: '1px solid var(--border)',
        }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--text-primary)', fontSize: 16 }}>
            All caught up
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            No pending approvals at this time.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {pending.map((expense) => (
            <ExpenseCard
              key={expense.expense_id}
              expense={expense}
              expanded={expanded === expense.expense_id}
              onToggle={() => setExpanded(
                expanded === expense.expense_id ? null : expense.expense_id
              )}
              comment={comments[expense.expense_id] || ''}
              onCommentChange={(val) => setComments(prev => ({ ...prev, [expense.expense_id]: val }))}
              onApprove={() => handleAction(expense.expense_id, 'approve')}
              onReject={() => handleAction(expense.expense_id, 'reject')}
              processing={processing === expense.expense_id}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ExpenseCard({ expense, expanded, onToggle, comment, onCommentChange, onApprove, onReject, processing }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}>
      {/* Card header */}
      <div
        onClick={onToggle}
        style={{
          padding: '14px 18px',
          display: 'flex', alignItems: 'center', gap: 14,
          cursor: 'pointer',
        }}
      >
        <div style={{
          width: 42, height: 42, borderRadius: 10,
          background: 'var(--accent-glow)',
          border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, flexShrink: 0, fontWeight: 700, color: 'var(--text-secondary)',
        }}>
          EXP
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontFamily: 'var(--font-display)', fontWeight: 700,
            fontSize: 14, color: 'var(--text-primary)',
          }}>
            {expense.vendor_name}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
            {expense.employee_email} · {expense.expense_category}
          </div>
        </div>

        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{
            fontFamily: 'var(--font-display)', fontWeight: 800,
            fontSize: 16, color: 'var(--accent-green)',
          }}>
            {expense.bill_amount}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            {expense.expense_id}
          </div>
        </div>

        <div style={{
          fontSize: 12, color: 'var(--text-muted)',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s',
        }}>▼</div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div style={{
          borderTop: '1px solid var(--border)',
          padding: '16px 18px',
          animation: 'fadeInUp 0.2s ease',
        }}>
          {/* Details grid */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr',
            gap: 10, marginBottom: 16,
          }}>
            {[
              ['Invoice No.', expense.invoice_number],
              ['Invoice Date', expense.invoice_date],
              ['GST Number', expense.gst_number || '—'],
              ['Submitted', expense.submission_date],
            ].map(([label, value]) => (
              <div key={label} style={{
                background: 'var(--bg-input)', padding: '8px 12px',
                borderRadius: 8, border: '1px solid var(--border)',
              }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-display)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                  {label}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)', marginTop: 3 }}>
                  {value}
                </div>
              </div>
            ))}
          </div>

          {/* Comments */}
          <textarea
            value={comment}
            onChange={e => onCommentChange(e.target.value)}
            placeholder="Add comments (required if rejecting)..."
            rows={2}
            style={{
              width: '100%', background: 'var(--bg-input)',
              border: '1px solid var(--border)', borderRadius: 8,
              color: 'var(--text-primary)', padding: '10px 12px',
              fontSize: 13, resize: 'none', outline: 'none',
              fontFamily: 'var(--font-body)',
              marginBottom: 12,
            }}
          />

          {/* Actions */}
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={onApprove}
              disabled={processing}
              style={{
                flex: 1, padding: '10px',
                background: 'linear-gradient(135deg, var(--accent), var(--accent-soft))',
                border: 'none', borderRadius: 10, color: '#fff',
                fontFamily: 'var(--font-display)', fontWeight: 700,
                fontSize: 13, cursor: processing ? 'not-allowed' : 'pointer',
                opacity: processing ? 0.6 : 1,
                boxShadow: '0 8px 18px rgba(3,38,71,0.18)',
              }}
            >
              {processing ? '...' : 'Approve'}
            </button>
            <button
              onClick={onReject}
              disabled={processing}
              style={{
                flex: 1, padding: '10px',
                background: 'transparent',
                border: '1px solid var(--accent-red)', borderRadius: 10,
                color: 'var(--accent-red)',
                fontFamily: 'var(--font-display)', fontWeight: 700,
                fontSize: 13, cursor: processing ? 'not-allowed' : 'pointer',
                opacity: processing ? 0.6 : 1,
              }}
            >
              {processing ? '...' : 'Reject'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
