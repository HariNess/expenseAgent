import React from 'react'

const TONE_STYLES = {
  success: {
    background: 'linear-gradient(135deg, rgba(38, 120, 91, 0.96), rgba(53, 148, 114, 0.94))',
    shadow: '0 18px 34px rgba(38, 120, 91, 0.24)',
  },
  error: {
    background: 'linear-gradient(135deg, rgba(176, 64, 64, 0.96), rgba(205, 90, 90, 0.94))',
    shadow: '0 18px 34px rgba(176, 64, 64, 0.22)',
  },
  warning: {
    background: 'linear-gradient(135deg, rgba(189, 119, 32, 0.96), rgba(217, 154, 63, 0.94))',
    shadow: '0 18px 34px rgba(189, 119, 32, 0.24)',
  },
  info: {
    background: 'linear-gradient(135deg, rgba(3, 38, 71, 0.96), rgba(0, 141, 230, 0.92))',
    shadow: '0 18px 34px rgba(3, 38, 71, 0.24)',
  },
}

export default function FeedbackToast({ toast, onDismiss }) {
  const styles = TONE_STYLES[toast.tone] || TONE_STYLES.info

  return (
    <div
      style={{
        minWidth: 280,
        maxWidth: 380,
        borderRadius: 18,
        padding: '14px 16px',
        color: '#fff',
        background: styles.background,
        boxShadow: styles.shadow,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 12,
      }}
    >
      <div
        style={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.92)',
          marginTop: 6,
          flexShrink: 0,
        }}
      />
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: 14,
            lineHeight: 1.35,
          }}
        >
          {toast.message}
        </div>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        style={{
          border: 'none',
          background: 'rgba(255,255,255,0.14)',
          color: '#fff',
          borderRadius: 999,
          padding: '6px 10px',
          cursor: 'pointer',
          fontSize: 11,
          fontWeight: 700,
          flexShrink: 0,
        }}
      >
        Dismiss
      </button>
    </div>
  )
}
