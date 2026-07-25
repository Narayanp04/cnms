import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import DeviceList from './pages/DeviceList'
import DeviceDetail from './pages/DeviceDetail'
import Monitoring from './pages/Monitoring'
import Alerts from './pages/Alerts'
import SLAReports from './pages/SLAReports'
import Reports from './pages/Reports'
import EventLogs from './pages/EventLogs'
import AIAnalytics from './pages/AIAnalytics'
import Maps from './pages/Maps'
import Settings from './pages/Settings'
import Customers from './pages/Customers'
import NotificationHistory from './pages/NotificationHistory'
import Backup from './pages/Backup'
import Help from './pages/Help'

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen"><LoadingSpinner /></div>
  return isAuthenticated ? children : <Navigate to="/login" />
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-32">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
    </div>
  )
}

export default function App() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-500 dark:text-gray-400">Loading ConnectXperts NMS...</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" /> : <LoginPage />} />
      
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="devices" element={<DeviceList />} />
        <Route path="devices/:id" element={<DeviceDetail />} />
        <Route path="monitoring" element={<Monitoring />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="sla" element={<SLAReports />} />
        <Route path="reports" element={<Reports />} />
        <Route path="events" element={<EventLogs />} />
        <Route path="ai" element={<AIAnalytics />} />
        <Route path="maps" element={<Maps />} />
        <Route path="customers" element={<Customers />} />
        <Route path="notifications" element={<NotificationHistory />} />
        <Route path="backup" element={<Backup />} />
        <Route path="settings" element={<Settings />} />
        <Route path="help" element={<Help />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
