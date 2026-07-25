import { useState, useEffect } from 'react'
import { eventAPI } from '../services/api'
import { HiOutlineSearch, HiOutlineFilter, HiOutlineClock } from 'react-icons/hi'

export default function EventLogs() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState('')
  const pageSize = 50

  useEffect(() => {
    fetchEvents()
  }, [page, search, severity])

  const fetchEvents = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: pageSize }
      if (search) params.search = search
      if (severity) params.severity = severity
      const { data } = await eventAPI.list(params)
      setEvents(data.items || [])
      setTotalPages(data.total_pages)
    } catch (err) {
      console.error('Failed to load events')
    } finally {
      setLoading(false)
    }
  }

  const getSeverityDot = (sev) => {
    switch (sev) {
      case 'critical': return 'bg-danger-500'
      case 'error': return 'bg-danger-400'
      case 'warning': return 'bg-warning-500'
      default: return 'bg-primary-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Event Logs</h1>
          <p className="text-sm text-gray-500">Audit trail and system events</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <HiOutlineSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search events..."
            className="input-field pl-10 text-sm"
          />
        </div>
        <select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1) }} className="input-field text-sm py-2 w-auto">
          <option value="">All Severity</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
          <option value="critical">Critical</option>
        </select>
        <button onClick={fetchEvents} className="btn-secondary text-sm py-2">Refresh</button>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Time</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Title</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">User</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Device</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {events.map(event => (
                <tr key={event.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap" suppressHydrationWarning>
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {event.event_type?.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                    {event.title}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">{event.username || 'system'}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{event.device_name || '-'}</td>
                  <td className="px-4 py-3 text-center">
                    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
                      event.severity === 'critical' ? 'bg-danger-100 text-danger-700' :
                      event.severity === 'error' ? 'bg-danger-50 text-danger-600' :
                      event.severity === 'warning' ? 'bg-warning-100 text-warning-700' :
                      'bg-primary-100 text-primary-700'
                    }`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${getSeverityDot(event.severity)}`}></div>
                      {event.severity}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="flex items-center justify-between px-4 py-3 border-t">
          <p className="text-sm text-gray-500">Page {page} of {totalPages}</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-sm py-1.5">Previous</button>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary text-sm py-1.5">Next</button>
          </div>
        </div>
      </div>
    </div>
  )
}
