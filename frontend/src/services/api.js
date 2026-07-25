import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          const { data } = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken
          })
          localStorage.setItem('accessToken', data.access_token)
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Handle common errors
    if (error.response?.status === 403) {
      toast.error('You do not have permission to perform this action')
    } else if (error.response?.status === 429) {
      toast.error('Too many requests. Please wait a moment.')
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    }

    return Promise.reject(error)
  }
)

// API service functions
export const dashboardAPI = {
  getDashboard: () => api.get('/api/v1/dashboard/'),
  getStats: () => api.get('/api/v1/dashboard/stats'),
  getRegions: () => api.get('/api/v1/dashboard/regions'),
}

export const deviceAPI = {
  list: (params) => api.get('/api/v1/devices', { params }),
  get: (id) => api.get(`/api/v1/devices/${id}`),
  create: (data) => api.post('/api/v1/devices', data),
  update: (id, data) => api.put(`/api/v1/devices/${id}`, data),
  delete: (id) => api.delete(`/api/v1/devices/${id}`),
  bulkImport: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/v1/devices/bulk-import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  exportCSV: () => api.get('/api/v1/devices/export/csv', { responseType: 'blob' }),
  getMapData: () => api.get('/api/v1/devices/map/data'),
  listTags: () => api.get('/api/v1/devices/tags/list'),
}

export const monitoringAPI = {
  getDeviceStatus: () => api.get('/api/v1/monitoring/devices/status'),
  getHistory: (deviceId, period) => 
    api.get(`/api/v1/monitoring/device/${deviceId}/history`, { params: { period } }),
  getStats: (deviceId, period) => 
    api.get(`/api/v1/monitoring/device/${deviceId}/stats`, { params: { period } }),
  getLiveStatus: (deviceId) => 
    api.get(`/api/v1/monitoring/device/${deviceId}/live`),
}

export const alertAPI = {
  list: (params) => api.get('/api/v1/alerts', { params }),
  getUnresolved: () => api.get('/api/v1/alerts/unresolved'),
  acknowledge: (id) => api.post(`/api/v1/alerts/${id}/acknowledge`),
  resolve: (id) => api.post(`/api/v1/alerts/${id}/resolve`),
  getGroups: () => api.get('/api/v1/alerts/groups'),
  createGroup: (data) => api.post('/api/v1/alerts/groups', data),
  createRecipient: (data) => api.post('/api/v1/alerts/recipients', data),
}

export const slaAPI = {
  getReports: (params) => api.get('/api/v1/sla/reports', { params }),
  generate: (deviceId, period) => 
    api.post(`/api/v1/sla/reports/generate?device_id=${deviceId}&period=${period}`),
  getDeviceSLA: (deviceId) => api.get(`/api/v1/sla/device/${deviceId}`),
}

export const reportAPI = {
  daily: (format) => api.get(`/api/v1/reports/daily`, { params: { format } }),
  weekly: (format) => api.get(`/api/v1/reports/weekly`, { params: { format } }),
  monthly: (format) => api.get(`/api/v1/reports/monthly`, { params: { format } }),
  yearly: (format) => api.get(`/api/v1/reports/yearly`, { params: { format } }),
}

export const eventAPI = {
  list: (params) => api.get('/api/v1/events', { params }),
  recent: (params) => api.get('/api/v1/events/recent', { params }),
}

export const aiAPI = {
  analyzeDevice: (deviceId) => api.get(`/api/v1/ai/device/${deviceId}`),
  getSummary: () => api.get('/api/v1/ai/summary'),
  getISPQuality: (deviceId) => api.get(`/api/v1/ai/isp-quality/${deviceId}`),
  getHealthScore: (deviceId) => api.get(`/api/v1/ai/health-score/${deviceId}`),
}

export const mapsAPI = {
  getDevices: () => api.get('/api/v1/maps/devices'),
  getHeatmap: () => api.get('/api/v1/maps/heatmap'),
}

export const backupAPI = {
  create: () => api.post('/api/v1/backup/create'),
  list: () => api.get('/api/v1/backup/list'),
  restore: (filepath) => api.post('/api/v1/backup/restore', null, { params: { filepath } }),
  delete: (filepath) => api.delete('/api/v1/backup/delete', { params: { filepath } }),
}

export const notificationAPI = {
  getHistory: (params) => api.get('/api/v1/notifications/history', { params }),
  getStats: () => api.get('/api/v1/notifications/stats'),
  testWhatsApp: (data) => api.post('/api/v1/notifications/whatsapp/test', data),
}

export const settingsAPI = {
  getSystem: () => api.get('/api/v1/settings/system'),
  getNotifications: () => api.get('/api/v1/settings/notifications'),
  testWhatsApp: () => api.post('/api/v1/settings/notifications/whatsapp/test'),
}
