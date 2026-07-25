import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { monitoringAPI } from '../services/api'
import { HiOutlineRefresh, HiOutlineSearch } from 'react-icons/hi'

export default function Monitoring() {
  const navigate = useNavigate()
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchStatus = useCallback(async () => {
    try {
      const { data } = await monitoringAPI.getDeviceStatus()
      setDevices(data || [])
    } catch (err) {
      console.error('Failed to fetch status:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    let interval
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 10000)
    }
    return () => clearInterval(interval)
  }, [fetchStatus, autoRefresh])

  const filteredDevices = devices.filter(d => {
    if (filter !== 'all' && d.status !== filter) return false
    if (search && !d.hostname.toLowerCase().includes(search.toLowerCase()) && 
        !d.ip_address.includes(search)) return false
    return true
  })

  const getStatusColor = (status) => {
    switch (status) {
      case 'up': return 'bg-success-500'
      case 'down': return 'bg-danger-500 animate-pulse'
      case 'warning': return 'bg-warning-500'
      default: return 'bg-gray-400'
    }
  }

  const getLatencyColor = (latency) => {
    if (!latency) return 'text-gray-400'
    if (latency > 300) return 'text-danger-600 font-bold'
    if (latency > 150) return 'text-warning-600 font-medium'
    return 'text-success-600'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Real-time Monitoring</h1>
          <p className="text-sm text-gray-500">{devices.length} devices • Auto-refresh {autoRefresh ? 'ON' : 'OFF'}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`text-sm py-1.5 px-3 rounded-lg font-medium transition-colors ${
              autoRefresh ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-500'
            }`}
          >
            Auto Refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button onClick={fetchStatus} className="btn-secondary text-sm py-1.5">
            <HiOutlineRefresh className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <HiOutlineSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by hostname or IP..."
            className="input-field pl-10 text-sm"
          />
        </div>
        {['all', 'up', 'down', 'warning'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg capitalize transition-colors ${
              filter === f ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
            }`}
          >
            {f}
            {f === 'all' ? ` (${devices.length})` : ` (${devices.filter(d => d.status === f).length})`}
          </button>
        ))}
      </div>

      {/* Devices Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredDevices.map(device => (
            <div
              key={device.id}
              onClick={() => navigate(`/devices/${device.id}`)}
              className={`card-hover p-4 cursor-pointer border-l-4 ${
                device.status === 'up' ? 'border-l-success-500' :
                device.status === 'down' ? 'border-l-danger-500' :
                device.status === 'warning' ? 'border-l-warning-500' :
                'border-l-gray-400'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(device.status)}`}></div>
                  <span className="text-xs font-medium uppercase text-gray-500">{device.status}</span>
                </div>
                <span className="text-xs text-gray-400" suppressHydrationWarning>
                  {device.last_response ? new Date(device.last_response).toLocaleString() : 'N/A'}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white truncate">{device.hostname}</h3>
              <p className="text-sm text-gray-500 font-mono">{device.ip_address}</p>
              <p className="text-xs text-gray-400 mt-1">{device.customer_name} • {device.site_name || 'N/A'}</p>
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <div>
                  <p className="text-xs text-gray-500">Latency</p>
                  <p className={`text-sm font-medium ${getLatencyColor(device.current_latency)}`}>
                    {device.current_latency ? `${device.current_latency.toFixed(1)}ms` : 'N/A'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Packet Loss</p>
                  <p className={`text-sm font-medium ${device.current_packet_loss > 5 ? 'text-danger-600' : 'text-gray-600 dark:text-gray-400'}`}>
                    {device.current_packet_loss ? `${device.current_packet_loss.toFixed(1)}%` : '0%'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">SLA 24h</p>
                  <p className={`text-sm font-medium ${device.sla_24h < 99 ? 'text-danger-600' : 'text-success-600'}`}>
                    {device.sla_24h?.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          ))}
          {filteredDevices.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">No devices found</div>
          )}
        </div>
      )}
    </div>
  )
}
