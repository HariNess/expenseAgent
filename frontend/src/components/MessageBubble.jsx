import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const Avatar = ({ role }) => (
  <div style={{
    width: 32,
    height: 32,
    borderRadius: '50%',
    flexShrink: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 14,
    fontWeight: 700,
    fontFamily: 'var(--font-display)',
    background: role === 'user'
      ? 'linear-gradient(135deg, var(--accent), var(--accent-soft))'
      : 'linear-gradient(135deg, var(--accent-soft), var(--accent-bright))',
    color: '#fff',
    boxShadow: role === 'user'
      ? '0 10px 20px rgba(3,38,71,0.18)'
      : '0 10px 20px rgba(1,81,133,0.12)',
  }}>
    {role === 'user' ? 'U' : 'N'}
  </div>
)

export default function MessageBubble({ message, isLatest }) {
  const isUser = message.role === 'user'
  const isFile = message.type === 'file'

  return (
    <div style={{
      display: 'flex',
      flexDirection: isUser ? 'row-reverse' : 'row',
      gap: 10,
      alignItems: 'flex-start',
      animation: 'fadeInUp 0.3s ease',
      marginBottom: 4,
    }}>
      <Avatar role={message.role} />

      <div style={{
        maxWidth: '78%',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        alignItems: isUser ? 'flex-end' : 'flex-start',
      }}>
        {/* Role label */}
        <span style={{
          fontSize: 11,
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-display)',
          fontWeight: 600,
          letterSpacing: '0.5px',
          textTransform: 'uppercase',
          paddingLeft: isUser ? 0 : 4,
          paddingRight: isUser ? 4 : 0,
        }}>
          {isUser ? 'You' : 'NessExpense'}
        </span>

        {/* Bubble */}
        <div style={{
          background: isUser
            ? 'linear-gradient(135deg, var(--accent), var(--accent-soft))'
            : 'var(--bg-card)',
          color: isUser ? '#fff' : 'var(--text-primary)',
          padding: '14px 16px',
          borderRadius: isUser
            ? '22px 8px 22px 22px'
            : '8px 22px 22px 22px',
          border: isUser ? 'none' : '1px solid var(--border)',
          boxShadow: isUser
            ? '0 14px 28px rgba(3, 38, 71, 0.16)'
            : '0 10px 24px rgba(3, 38, 71, 0.06)',
          fontSize: 14,
          lineHeight: 1.6,
        }}>
          {isFile ? (
            <FileMessage filename={message.content} />
          ) : (
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        {message.timestamp && (
          <span style={{
            fontSize: 10,
            color: 'var(--text-muted)',
            paddingLeft: isUser ? 0 : 4,
            paddingRight: isUser ? 4 : 0,
          }}>
            {message.timestamp}
          </span>
        )}
      </div>
    </div>
  )
}

function FileMessage({ filename }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      color: 'var(--text-secondary)',
    }}>
      <span style={{ fontSize: 20 }}>📎</span>
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
          {filename}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Invoice uploaded
        </div>
      </div>
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div style={{
      display: 'flex',
      gap: 10,
      alignItems: 'flex-start',
      animation: 'fadeInUp 0.2s ease',
    }}>
      <Avatar role="agent" />
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '8px 22px 22px 22px',
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: 'var(--accent)',
            animation: 'pulse 1.2s ease infinite',
            animationDelay: `${i * 0.2}s`,
          }} />
        ))}
      </div>
    </div>
  )
}
