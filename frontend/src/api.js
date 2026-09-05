import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export const getProducts = (params) => api.get('/catalog/products', { params })
export const searchProducts = (body) => api.post('/catalog/search', body)
export const getUpsell = (body) => api.post('/catalog/upsell', body)
export const getMerchant = () => api.get('/merchant/')
export const getPolicy = () => api.get('/merchant/policy')
export const evaluatePolicy = (body) => api.post('/policy/evaluate', body)
export const runPurchase = (body) => api.post('/agent/purchase', body)
export const getPending = () => api.get('/approvals/pending')
export const approveTransaction = (id) => api.post(`/approvals/${id}/approve`)
export const rejectTransaction = (id) => api.post(`/approvals/${id}/reject`)
export const getAuditTrail = (id) => api.get(`/audit/${id}`)
export const getAllTransactions = () => api.get('/audit/transactions/all')
export const getRecentEvents = () => api.get('/audit/recent/all')
