import { useState, useEffect } from 'react'
import { alertAPI } from '../services/api'
import { HiOutlineBell, HiOutlineCheck, HiOutlineExclamation, HiOutlineFilter } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [statistics, setStatistics] = useState({ total: 0, critical: 0, high: 0, medium: 0 })

  useEffect(() => {
    fetchAlerts()
  }, [filter])

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filter === 'unresolved') params.status = 'triggered,acknowledged'
      if (filter === 'resolved') params.status = 'resolved'
      
      const { data } = await alertAPI.list(params)
      setAlerts(data || [])
      
      // Calculate stats
      const stats = { total: 0, critical: 0, high: 0, medium: 0 }
      data.forEach(a => {
        stats.total++
        if (a.severity === 'critical') stats.critical++
        else if (a.severity === 'high') stats.high++
        else if (a.severity === 'medium') stats.medium++
      })
      setStatistics(stats)
    } catch (err) {
      toast.error('Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  const handleAcknowledge = async (alertId) => {
    try {
      await alertAPI.acknowledge(alertId)
      toast.success('Alert acknowledged')
      fetchAlerts()
    } catch (err) {
      toast.error('Failed to acknowledge alert')
    }
  }

  const handleResolve = async (alertId) => {
    try {
      await alertAPI.resolve(alertId)
      toast.success('Alert resolved')
      fetchAlerts()
    } catch (err) {
      toast.error('Failed to resolve alert')
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-danger-500'
      case 'high': return 'bg-warning-500'
      case 'medium': return 'bg-primary-500'
      default: return 'bg-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Alerts</h1>
          <p className="text-sm text-gray-500">{statistics.total} total alerts</p>
        </div>
        <button onClick={fetchAlerts} className="btn-secondary text-sm">Refresh</button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: statistics.total, color: 'bg-gray-500' },
          { label: 'Critical', value: statistics.critical, color: 'bg-danger-500' },
          { label: 'High', value: statistics.high, color: 'bg-warning-500' },
          { label: 'Medium', value: statistics.medium, color: 'bg-primary-500' },
        ].map(stat => (
          <div key={stat.label} className="card p-4 text-center">
            <div className={`w-3 h-3 rounded-full ${stat.color} mx-auto mb-2`}></div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
            <p className="text-xs text-gray-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'unresolved', 'resolved'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 text-sm font-medium rounded-lg capitalize ${
              filter === f ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="text-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div></div>
      ) : (
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <div className="card p-8 text-center text-gray-500">
              <HiOutlineBell className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>No alerts found</p>
            </div>
          ) : (
            alerts.map(alert => (
              <div key={alert.id} className={`card p-4 border-l-4 ${getSeverityColor(alert.severity)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full uppercase ${
                        alert.severity === 'critical' ? 'bg-danger-100 text-danger-700' :
                        alert.severity === 'high' ? 'bg-warning-100 text-warning-700' :
                        'bg-primary-100 text-primary-700'
                      }`}>
                        {alert.severity}
                      </span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        alert.status === 'triggered' ? 'bg-danger-100 text-danger-700' :
                        alert.status === 'acknowledged' ? 'bg-warning-100 text-warning-700' :
                        'bg-success-100 text-success-700'
                      }`}>
                        {alert.status}
                      </span>
                    </div>
                    <h3 className="font-medium text-gray-900 dark:text-white">{alert.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{alert.message}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span>{alert.device_hostname || 'Unknown'}</span>
                      <span suppressHydrationWarning>{new Date(alert.triggered_at).toLocaleString()}</span>
                      {alert.latency_ms && <span>{alert.latency_ms}ms latency</span>}
                      {alert.packet_loss_percent && <span>{alert.packet_loss_percent}% loss</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    {alert.status === 'triggered' && (
                      <button onClick={() => handleAcknowledge(alert.id)} className="btn-secondary text-xs py-1.5">
                        <HiOutlineCheck className="w-3 h-3 mr-1 inline" />
                        Acknowledge
                      </button>
                    )}
                    {(alert.status === 'triggered' || alert.status === 'acknowledged') && (
                      <button onClick={() => handleResolve(alert.id)} className="btn-danger text-xs py-1.5">
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
