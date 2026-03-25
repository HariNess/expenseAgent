import React, { useState } from 'react'

const CATEGORIES = [
  'Travel Reimbursement',
  'Internet Bill',
  'Fuel Reimbursement',
  'Hotel & Accommodation',
  'Food & Meals',
  'Office Supplies',
  'Client Entertainment',
  'Medical Reimbursement',
  'Training & Courses',
  'Miscellaneous',
]

const EDITABLE_FIELDS = [
  'vendor_name',
  'invoice_number',
  'invoice_date',
  'gst_number',
  'gst_amount',
  'expense_category',
]

const FIELD_LABELS = {
  vendor_name: 'Vendor Name',
  invoice_number: 'Invoice Number',
  invoice_date: 'Invoice Date',
  bill_amount: 'Bill Amount',
  gst_number: 'GST Number',
  gst_amount: 'GST Amount',
  expense_category: 'Category',
}

export default function ExpenseTable({ data, onUpdate, onSubmit, onCancel }) {
  const [editing, setEditing] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [localData, setLocalData] = useState(data)

  const startEdit = (field) => {
    if (!EDITABLE_FIELDS.includes(field)) return
    setEditing(field)
    setEditValue(localData[field] || '')
  }

  const saveEdit = (field) => {
    const updated = { ...localData, [field]: editValue }
    setLocalData(updated)
    onUpdate && onUpdate(field, editValue)
    setEditing(null)
  }

  const formatValue = (field, value) => {
    if (field === 'bill_amount' || field === 'gst_amount') {
      const num = parseFloat(value)
      return isNaN(num) ? value : `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
    }
    return value || '—'
  }

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
      marginTop: 8,
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px',
        background: 'var(--bg-input)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{ fontSize: 14 }}>🧾</span>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: 13,
          color: 'var(--text-primary)',
          letterSpacing: '0.3px',
        }}>
          Extracted Invoice Details
        </span>
        <span style={{
          marginLeft: 'auto',
          fontSize: 11,
          color: 'var(--text-muted)',
          fontStyle: 'italic',
        }}>
          Click a field to edit
        </span>
      </div>

      {/* Table rows */}
      <div>
        {Object.entries(FIELD_LABELS).map(([field, label]) => {
          const isEditable = EDITABLE_FIELDS.includes(field)
          const isEditingThis = editing === field
          const value = localData[field]

          return (
            <div
              key={field}
              onClick={() => isEditable && !isEditingThis && startEdit(field)}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px 16px',
                borderBottom: '1px solid var(--border)',
                cursor: isEditable ? 'pointer' : 'default',
                transition: 'background 0.15s',
                background: isEditingThis ? 'rgba(108,99,255,0.08)' : 'transparent',
              }}
              onMouseEnter={e => {
                if (isEditable && !isEditingThis)
                  e.currentTarget.style.background = 'var(--bg-hover)'
              }}
              onMouseLeave={e => {
                if (!isEditingThis)
                  e.currentTarget.style.background = 'transparent'
              }}
            >
              {/* Label */}
              <div style={{
                width: 140,
                flexShrink: 0,
                fontSize: 12,
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-display)',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.4px',
              }}>
                {label}
              </div>

              {/* Value or edit input */}
              <div style={{ flex: 1 }}>
                {isEditingThis ? (
                  <EditInput
                    field={field}
                    value={editValue}
                    onChange={setEditValue}
                    onSave={() => saveEdit(field)}
                    onCancel={() => setEditing(null)}
                  />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                      fontSize: 13,
                      color: field === 'bill_amount' ? 'var(--accent-green)' : 'var(--text-primary)',
                      fontWeight: field === 'bill_amount' ? 600 : 400,
                    }}>
                      {formatValue(field, value)}
                    </span>
                    {field === 'bill_amount' && (
                      <span style={{
                        fontSize: 10,
                        color: 'var(--text-muted)',
                        background: 'var(--bg-input)',
                        padding: '1px 6px',
                        borderRadius: 4,
                        fontFamily: 'var(--font-display)',
                      }}>
                        locked
                      </span>
                    )}
                    {isEditable && (
                      <span style={{
                        fontSize: 11,
                        color: 'var(--accent)',
                        opacity: 0.6,
                        marginLeft: 'auto',
                      }}>
                        ✏️
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Action buttons */}
      <div style={{
        padding: '12px 16px',
        display: 'flex',
        gap: 10,
        borderTop: '1px solid var(--border)',
        background: 'var(--bg-input)',
      }}>
        <button
          onClick={onSubmit}
          style={{
            flex: 1,
            padding: '10px 16px',
            borderRadius: 10,
            border: 'none',
            background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
            color: '#fff',
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: 13,
            cursor: 'pointer',
            letterSpacing: '0.3px',
            boxShadow: '0 4px 16px rgba(108,99,255,0.3)',
            transition: 'all 0.2s',
          }}
        >
          ✅ Submit Expense
        </button>
        <button
          onClick={onCancel}
          style={{
            padding: '10px 16px',
            borderRadius: 10,
            border: '1px solid var(--border)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-display)',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

function EditInput({ field, value, onChange, onSave, onCancel }) {
  const isCategory = field === 'expense_category'

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      {isCategory ? (
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          autoFocus
          style={{
            flex: 1,
            background: 'var(--bg-input)',
            border: '1px solid var(--accent)',
            borderRadius: 6,
            color: 'var(--text-primary)',
            padding: '4px 8px',
            fontSize: 13,
            outline: 'none',
          }}
        >
          {CATEGORIES.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      ) : (
        <input
          type={field === 'gst_amount' ? 'number' : 'text'}
          value={value}
          onChange={e => onChange(e.target.value)}
          autoFocus
          onKeyDown={e => {
            if (e.key === 'Enter') onSave()
            if (e.key === 'Escape') onCancel()
          }}
          style={{
            flex: 1,
            background: 'var(--bg-input)',
            border: '1px solid var(--accent)',
            borderRadius: 6,
            color: 'var(--text-primary)',
            padding: '4px 8px',
            fontSize: 13,
            outline: 'none',
          }}
        />
      )}
      <button
        onClick={onSave}
        style={{
          padding: '4px 10px',
          background: 'var(--accent)',
          color: '#fff',
          border: 'none',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        Save
      </button>
      <button
        onClick={onCancel}
        style={{
          padding: '4px 10px',
          background: 'transparent',
          color: 'var(--text-muted)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: 12,
        }}
      >
        ✕
      </button>
    </div>
  )
}
