import React, { useEffect, useState } from 'react'
import ChatWindow from './components/ChatWindow'
import ApprovalPanel from './components/ApprovalPanel'
import nessLogo from './assets/ness.png'

const DEMO_USERS = [
  {
    email: 'atharva.bhagat@ness.com',
    name: 'Atharva Bhagat',
    role: 'employee',
    avatar: 'AB',
    department: 'Engineering',
  },
  {
    email: 'vignesh.jayakumar@ness.com',
    name: 'Vignesh Jayakumar',
    role: 'manager',
    avatar: 'VJ',
    department: 'Engineering',
  },
  {
    email: 'hariharasudan.venkatasalam@ness.com',
    name: 'Hariharasudan Venkatasalam',
    role: 'hr',
    avatar: 'HV',
    department: 'People Operations',
  },
]

const NAV_ITEMS = [
  { id: 'chat', label: 'Workspace', caption: 'Submit and review expenses' },
  { id: 'approvals', label: 'Queue', caption: 'Approvals and routing' },
  { id: 'history', label: 'Archive', caption: 'Recent submissions' },
]

const ROLE_COPY = {
  employee: '',
  manager: 'Manager',
  hr: 'HR',
}

function getRoleDepartmentText(user) {
  const roleLabel = ROLE_COPY[user.role]
  return roleLabel ? `${roleLabel} · ${user.department}` : user.department
}

const DEFAULT_USER = DEMO_USERS[0]
const LOGIN_STORAGE_KEY = 'ness-expense-user'

export default function App() {
  const [activeUser, setActiveUser] = useState(DEFAULT_USER)
  const [activeTab, setActiveTab] = useState('chat')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedEmail, setSelectedEmail] = useState(DEFAULT_USER.email)

  useEffect(() => {
    const storedEmail = window.localStorage.getItem(LOGIN_STORAGE_KEY)
    const matchedUser = DEMO_USERS.find((user) => user.email === storedEmail)

    if (matchedUser) {
      setActiveUser(matchedUser)
      setSelectedEmail(matchedUser.email)
      setIsAuthenticated(true)
    }
  }, [])

  const handleLogin = () => {
    const matchedUser =
      DEMO_USERS.find((user) => user.email === selectedEmail) || DEFAULT_USER

    setActiveUser(matchedUser)
    setSelectedEmail(matchedUser.email)
    setActiveTab('chat')
    setIsAuthenticated(true)
    window.localStorage.setItem(LOGIN_STORAGE_KEY, matchedUser.email)
  }

  const handleSwitchUser = (user) => {
    setActiveUser(user)
    setSelectedEmail(user.email)
    setActiveTab('chat')
    window.localStorage.setItem(LOGIN_STORAGE_KEY, user.email)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setSelectedEmail(activeUser.email)
    setActiveTab('chat')
    window.localStorage.removeItem(LOGIN_STORAGE_KEY)
  }

  if (!isAuthenticated) {
    return (
      <LoginScreen
        selectedEmail={selectedEmail}
        setSelectedEmail={setSelectedEmail}
        onLogin={handleLogin}
      />
    )
  }

  const approvalStage = activeUser.role === 'hr' ? 'hr' : 'manager'

  return (
    <div
      style={{
        minHeight: '100vh',
        background:
          'radial-gradient(circle at top left, rgba(0, 141, 230, 0.18), transparent 26%), radial-gradient(circle at bottom right, rgba(1, 81, 133, 0.1), transparent 30%), var(--bg-canvas)',
        color: 'var(--text-primary)',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '320px minmax(0, 1fr)',
          minHeight: '100vh',
          gap: 0,
        }}
      >
        <aside
          style={{
            position: 'relative',
            padding: '28px 24px',
            background:
              'linear-gradient(180deg, rgba(246, 250, 255, 0.97), rgba(236, 243, 250, 0.99))',
            borderRight: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            gap: 24,
          }}
        >
          <BrandBlock />

          <nav style={{ display: 'grid', gap: 10 }}>
            {NAV_ITEMS.map((item) => {
              const isActive = activeTab === item.id

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    width: '100%',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--border-strong)' : 'transparent',
                    background: isActive ? 'var(--surface-raised)' : 'transparent',
                    borderRadius: 22,
                    padding: '14px 16px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    boxShadow: isActive ? '0 16px 30px rgba(3, 38, 71, 0.08)' : 'none',
                    transition: 'all 0.18s ease',
                  }}
                >
                  <div
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontWeight: 700,
                      fontSize: 16,
                      color: 'var(--text-primary)',
                    }}
                  >
                    {item.label}
                  </div>
                  <div
                    style={{
                      marginTop: 4,
                      fontSize: 12,
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {item.caption}
                  </div>
                </button>
              )
            })}
          </nav>

          <StatusPanel />

          <div
            style={{
              marginTop: 'auto',
              display: 'grid',
              gap: 12,
            }}
          >
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: 13,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  marginBottom: 10,
                }}
              >
                Active Profiles
              </div>
              <div style={{ display: 'grid', gap: 10 }}>
                {DEMO_USERS.map((user) => {
                  const isActive = activeUser.email === user.email

                  return (
                    <button
                      key={user.email}
                      onClick={() => handleSwitchUser(user)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                        width: '100%',
                        padding: '13px 14px',
                        borderRadius: 20,
                        border: '1px solid',
                        borderColor: isActive ? 'var(--border-strong)' : 'var(--border-soft)',
                        background: isActive ? 'var(--surface-raised)' : 'rgba(255,255,255,0.62)',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'all 0.18s ease',
                      }}
                    >
                      <div
                        style={{
                          width: 42,
                          height: 42,
                          borderRadius: 14,
                          display: 'grid',
                          placeItems: 'center',
                          fontFamily: 'var(--font-display)',
                          fontWeight: 700,
                          fontSize: 13,
                          background: isActive ? 'var(--accent)' : 'var(--surface-muted)',
                          color: isActive ? '#fff' : 'var(--text-primary)',
                        }}
                      >
                        {user.avatar}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div
                          style={{
                            fontSize: 14,
                            fontWeight: 600,
                            color: 'var(--text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {user.name}
                        </div>
                        <div
                          style={{
                            fontSize: 12,
                            color: 'var(--text-secondary)',
                            marginTop: 2,
                          }}
                        >
                          {getRoleDepartmentText(user)}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </aside>

        <main
          style={{
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            padding: 18,
          }}
        >
          <header
            style={{
              background: 'rgba(255, 255, 255, 0.88)',
              border: '1px solid var(--border)',
              borderRadius: 28,
              padding: '18px 22px',
              display: 'flex',
              alignItems: 'center',
              gap: 18,
              boxShadow: 'var(--shadow-soft)',
              backdropFilter: 'blur(12px)',
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 18,
                background: 'linear-gradient(135deg, var(--accent), var(--accent-bright))',
                display: 'grid',
                placeItems: 'center',
                color: '#fff',
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
              }}
            >
              {activeUser.avatar}
            </div>

            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: 22,
                  color: 'var(--text-primary)',
                }}
              >
                {activeUser.name}
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: 'var(--text-secondary)',
                  marginTop: 2,
                }}
              >
                {activeUser.email}
              </div>
            </div>

            <div
              style={{
                marginLeft: 'auto',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: 999,
                background: 'rgba(1, 81, 133, 0.08)',
                border: '1px solid rgba(1, 81, 133, 0.18)',
              }}
            >
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: 'var(--accent-bright)',
                  boxShadow: '0 0 0 6px rgba(0, 141, 230, 0.08)',
                }}
              />
              <span
                style={{
                  fontSize: 12,
                  color: 'var(--accent)',
                  fontWeight: 700,
                }}
              >
                Workflow Active
              </span>
            </div>

            <button
              onClick={handleLogout}
              style={{
                border: '1px solid var(--border)',
                background: 'var(--surface-raised)',
                color: 'var(--text-secondary)',
                borderRadius: 999,
                padding: '10px 14px',
                cursor: 'pointer',
                fontWeight: 700,
                fontSize: 12,
              }}
            >
              Sign Out
            </button>
          </header>

          <section
            style={{
              marginTop: 18,
              flex: 1,
              minHeight: 0,
              border: '1px solid var(--border)',
              borderRadius: 30,
              background: 'rgba(255, 255, 255, 0.84)',
              boxShadow: 'var(--shadow-soft)',
              overflow: 'hidden',
            }}
          >
            {activeTab === 'chat' && (
              <ChatWindow key={activeUser.email} employeeEmail={activeUser.email} />
            )}
            {activeTab === 'approvals' && (
              <div style={{ height: '100%', overflowY: 'auto' }}>
                <ApprovalPanel approverEmail={activeUser.email} stage={approvalStage} />
              </div>
            )}
            {activeTab === 'history' && <HistoryTab email={activeUser.email} />}
          </section>
        </main>
      </div>
    </div>
  )
}

function LoginScreen({ selectedEmail, setSelectedEmail, onLogin }) {
  const selectedUser =
    DEMO_USERS.find((user) => user.email === selectedEmail) || DEFAULT_USER

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        padding: 24,
        background:
          'radial-gradient(circle at top left, rgba(0, 141, 230, 0.18), transparent 26%), radial-gradient(circle at bottom right, rgba(1, 81, 133, 0.1), transparent 30%), var(--bg-canvas)',
      }}
    >
      <div
        style={{
          width: 'min(1080px, 100%)',
          display: 'grid',
          gridTemplateColumns: '1.05fr 0.95fr',
          gap: 20,
        }}
      >
        <section
          style={{
            borderRadius: 36,
            padding: '42px 40px',
            background:
              'linear-gradient(180deg, rgba(3, 38, 71, 0.98), rgba(1, 81, 133, 0.98))',
            color: '#fff',
            boxShadow: '0 30px 80px rgba(3, 38, 71, 0.22)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            minHeight: 620,
          }}
        >
          <div>
            <div
              style={{
                width: 92,
                padding: 12,
                borderRadius: 26,
                background: 'rgba(255,255,255,0.12)',
                display: 'grid',
                placeItems: 'center',
                marginBottom: 28,
              }}
            >
              <img
                src={nessLogo}
                alt="Ness logo"
                style={{ width: '100%', height: 'auto', display: 'block' }}
              />
            </div>
            <div
              style={{
                fontSize: 14,
                fontWeight: 700,
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                opacity: 0.84,
              }}
            >
              NessExpense
            </div>
            <h1
              style={{
                marginTop: 16,
                fontFamily: 'var(--font-display)',
                fontSize: 44,
                lineHeight: 1.05,
              fontWeight: 800,
              maxWidth: 420,
            }}
          >
              Expense operations with consistent Ness branding.
            </h1>
            <p
              style={{
                marginTop: 18,
                maxWidth: 470,
                color: 'rgba(255,255,255,0.82)',
                fontSize: 15,
                lineHeight: 1.7,
              }}
            >
            Choose a profile to enter the workspace, review invoices, route approvals,
            and move through the same role-based experience from a proper, branded login flow.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
              gap: 12,
            }}
          >
            <LoginMetric label="Profiles" value="3" />
            <LoginMetric label="Workflow" value="Live" />
            <LoginMetric label="Mode" value="Demo" />
          </div>
        </section>

        <section
          style={{
            borderRadius: 36,
            padding: '34px 32px',
            background: 'rgba(255,255,255,0.9)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-soft)',
            minHeight: 620,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div>
            <div
              style={{
                fontSize: 13,
                color: 'var(--text-secondary)',
                fontWeight: 700,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}
            >
              Sign In
            </div>
            <div
              style={{
                marginTop: 10,
                fontFamily: 'var(--font-display)',
                fontWeight: 800,
                fontSize: 30,
                color: 'var(--text-primary)',
              }}
            >
              Select a Ness profile
            </div>
            <div
              style={{
                marginTop: 8,
                fontSize: 14,
                color: 'var(--text-secondary)',
              }}
            >
              Pick the user you want to enter with, then continue into the workspace.
            </div>
          </div>

          <div style={{ marginTop: 28, display: 'grid', gap: 12 }}>
            {DEMO_USERS.map((user) => {
              const isSelected = selectedEmail === user.email

              return (
                <button
                  key={user.email}
                  onClick={() => setSelectedEmail(user.email)}
                  style={{
                    width: '100%',
                    border: '1px solid',
                    borderColor: isSelected ? 'var(--border-strong)' : 'var(--border-soft)',
                    background: isSelected ? 'rgba(15, 143, 134, 0.08)' : 'var(--surface-raised)',
                    borderRadius: 24,
                    padding: '16px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.18s ease',
                  }}
                >
                  <div
                    style={{
                      width: 50,
                      height: 50,
                      borderRadius: 18,
                    background: isSelected ? 'var(--accent)' : 'var(--surface-muted)',
                      color: isSelected ? '#fff' : 'var(--text-primary)',
                      display: 'grid',
                      placeItems: 'center',
                      fontWeight: 800,
                    }}
                  >
                    {user.avatar}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                        fontSize: 15,
                      }}
                    >
                      {user.name}
                    </div>
                    <div
                      style={{
                        marginTop: 4,
                        color: 'var(--text-secondary)',
                        fontSize: 13,
                      }}
                    >
                      {user.email}
                    </div>
                    <div
                      style={{
                        marginTop: 6,
                        color: 'var(--text-muted)',
                        fontSize: 12,
                      }}
                    >
                      {getRoleDepartmentText(user)}
                    </div>
                  </div>
                </button>
              )
            })}
          </div>

          <div
            style={{
              marginTop: 22,
              padding: '18px 18px 20px',
              borderRadius: 24,
              background: 'var(--bg-input)',
              border: '1px solid var(--border-soft)',
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: 'var(--text-secondary)',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              Selected Profile
            </div>
            <div
              style={{
                marginTop: 10,
                fontFamily: 'var(--font-display)',
                fontWeight: 800,
                fontSize: 20,
                color: 'var(--text-primary)',
              }}
            >
              {selectedUser.name}
            </div>
            <div style={{ marginTop: 4, color: 'var(--text-secondary)', fontSize: 14 }}>
              {selectedUser.email}
            </div>
            <div style={{ marginTop: 6, color: 'var(--text-muted)', fontSize: 13 }}>
              {getRoleDepartmentText(selectedUser)}
            </div>
          </div>

          <button
            onClick={onLogin}
            style={{
              marginTop: 'auto',
              width: '100%',
              border: 'none',
              borderRadius: 24,
              padding: '16px 18px',
              background: 'linear-gradient(135deg, var(--accent), var(--accent-bright))',
              color: '#fff',
              fontWeight: 800,
              fontSize: 15,
              cursor: 'pointer',
              boxShadow: '0 18px 36px rgba(3, 38, 71, 0.18)',
            }}
          >
            Continue To Workspace
          </button>
        </section>
      </div>
    </div>
  )
}

function LoginMetric({ label, value }) {
  return (
    <div
      style={{
        borderRadius: 22,
        padding: '16px 14px',
        background: 'rgba(255,255,255,0.1)',
        border: '1px solid rgba(255,255,255,0.14)',
      }}
    >
      <div style={{ fontSize: 12, opacity: 0.78, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {label}
      </div>
      <div style={{ marginTop: 6, fontSize: 22, fontWeight: 800 }}>
        {value}
      </div>
    </div>
  )
}

function BrandBlock() {
  return (
    <div
      style={{
        padding: '6px 0 4px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <div
          style={{
            width: 74,
            padding: 10,
            borderRadius: 22,
            background: 'rgba(3, 38, 71, 0.06)',
            display: 'grid',
            placeItems: 'center',
            boxShadow: '0 16px 30px rgba(3, 38, 71, 0.08)',
          }}
        >
          <img
            src={nessLogo}
            alt="Ness logo"
            style={{ width: '100%', height: 'auto', display: 'block' }}
          />
        </div>
        <div>
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 29,
              lineHeight: 1,
              color: 'var(--text-primary)',
              fontWeight: 700,
            }}
          >
            NessExpense
          </div>
          <div
            style={{
              marginTop: 6,
              fontSize: 12,
              color: 'var(--text-secondary)',
              maxWidth: 220,
            }}
          >
            Expense operations across the Ness reimbursement workflow.
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusPanel() {
  const agents = ['Orchestrator', 'Extraction', 'Fraud Detection', 'Approvals']

  return (
    <div
      style={{
        border: '1px solid var(--border)',
        borderRadius: 24,
        padding: 18,
        background: 'rgba(255,255,255,0.58)',
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 700,
          fontSize: 13,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--text-secondary)',
          marginBottom: 12,
        }}
      >
        System Status
      </div>
      <div style={{ display: 'grid', gap: 10 }}>
        {agents.map((agent) => (
          <div
            key={agent}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10,
              padding: '10px 12px',
              borderRadius: 16,
              background: 'rgba(247, 252, 251, 0.9)',
              border: '1px solid var(--border-soft)',
            }}
          >
            <span style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600 }}>
              {agent}
            </span>
            <span
              style={{
                fontSize: 11,
                color: 'var(--accent-green)',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              Ready
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function HistoryTab({ email }) {
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    import('./utils/api').then(({ getMyExpenses }) => {
      getMyExpenses(email)
        .then((data) => setExpenses(data.expenses || []))
        .catch(() => {})
        .finally(() => setLoading(false))
    })
  }, [email])

  const statusColors = {
    'Self-Approved': '#2f735c',
    'Fully Approved': '#2f735c',
    'Awaiting Manager Approval': '#d18a26',
    'Awaiting HR Approval': '#d18a26',
    Rejected: '#c65151',
    Pending: '#77918e',
  }

  return (
    <div style={{ padding: 28, maxWidth: 860, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 700,
            fontSize: 28,
            color: 'var(--text-primary)',
          }}
        >
          Expense Archive
        </div>
        <div style={{ color: 'var(--text-secondary)', marginTop: 6, fontSize: 14 }}>
          Review the latest submissions and reimbursement outcomes for this profile.
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 50, color: 'var(--text-muted)' }}>
          Loading archive...
        </div>
      ) : expenses.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: 64,
            background: 'var(--surface-raised)',
            borderRadius: 28,
            border: '1px solid var(--border)',
          }}
        >
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              color: 'var(--text-primary)',
              fontSize: 22,
            }}
          >
            No archived expenses yet
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8 }}>
            Submit the first invoice from Workspace to start the record.
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {expenses.map((exp) => (
            <div
              key={exp.expense_id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '18px 20px',
                background: 'var(--surface-raised)',
                border: '1px solid var(--border)',
                borderRadius: 24,
              }}
            >
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 16,
                  background: 'var(--surface-muted)',
                  display: 'grid',
                  placeItems: 'center',
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  color: 'var(--text-secondary)',
                }}
              >
                EX
              </div>
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontWeight: 700,
                    fontSize: 17,
                    color: 'var(--text-primary)',
                  }}
                >
                  {exp.vendor_name}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                  {exp.expense_id} · Submitted {exp.submitted}
                </div>
              </div>
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: 18,
                  color: 'var(--text-primary)',
                }}
              >
                {exp.bill_amount}
              </div>
              <div
                style={{
                  padding: '7px 12px',
                  borderRadius: 999,
                  background: `${statusColors[exp.status] || '#77918e'}15`,
                  border: `1px solid ${statusColors[exp.status] || '#77918e'}35`,
                  color: statusColors[exp.status] || '#77918e',
                  fontSize: 11,
                  fontWeight: 700,
                  whiteSpace: 'nowrap',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                }}
              >
                {exp.status}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
