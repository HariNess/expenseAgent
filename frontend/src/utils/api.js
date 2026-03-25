import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const sendMessage = async (message, employeeEmail, conversationHistory = [], sessionId = null) => {
  const { data } = await api.post('/chat/message', {
    message,
    employee_email: employeeEmail,
    conversation_history: conversationHistory,
    session_id: sessionId,
  })
  return data
}

export const uploadInvoice = async (file, employeeEmail, sessionId = null) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('employee_email', employeeEmail)
  if (sessionId) formData.append('session_id', sessionId)

  const { data } = await api.post('/chat/upload-invoice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const submitExpense = async (employeeEmail, sessionId) => {
  const { data } = await api.post('/chat/submit-expense', null, {
    params: { employee_email: employeeEmail, session_id: sessionId }
  })
  return data
}

export const editField = async (employeeEmail, sessionId, field, newValue) => {
  const { data } = await api.post('/chat/edit-field', null, {
    params: { employee_email: employeeEmail, session_id: sessionId, field, new_value: newValue }
  })
  return data
}

export const getExpenseStatus = async (expenseId) => {
  const { data } = await api.get(`/chat/status/${expenseId}`)
  return data
}

export const getMyExpenses = async (employeeEmail) => {
  const { data } = await api.get(`/chat/my-expenses/${employeeEmail}`)
  return data
}

export const getPendingApprovals = async (approverEmail, stage = 'manager') => {
  const { data } = await api.get(`/approvals/pending/${approverEmail}`, {
    params: { stage }
  })
  return data
}

export const takeApprovalAction = async (expenseId, action, comments, approverEmail, stage) => {
  const { data } = await api.post('/approvals/action', {
    expense_id: expenseId,
    action,
    comments,
    approver_email: approverEmail,
    stage,
  })
  return data
}

export const getAllExpenses = async () => {
  const { data } = await api.get('/approvals/all-expenses')
  return data
}
