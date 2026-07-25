import { useState, useEffect } from 'react'
import { notificationAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function NotificationHistory() {
  const [notifications, setNotifications] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [historyRes, statsRes] = await Promise.all([
        notificationAPI.getHistory({ limit: 100 }),
        notificationAPI.getStats()
      ])
      setNotifications(historyRes.data || [])
      setStats(statsRes.data || {})
    } catch (err) {
      toast.error('Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Notification History</h1>
          <p className="text-sm text-gray-500">Delivery status of all notifications</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Object.entries(stats).map(([channel, data]) => (
          <div key={channel} className="card p-4 text-center">
            <p className="text-sm text-gray-500 capitalize">{channel}</p>
            <p className="text-2xl font-bold mt-1">{data.total || 0}</p>
            <div className="flex justify-center gap-2 mt-1 text-xs">
              <span className="text-success-600">Sent: {data.sent || 0}</span>
              <span className="text-danger-600">Failed: {data.failed || 0}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Time</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Channel</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Recipient</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Message</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Retries</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {notifications.map(n => (
                <tr key={n.id}>
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap" suppressHydrationWarning>
                    {new Date(n.sent_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm capitalize">{n.channel}</td>
                  <td className="px-4 py-3 text-sm">{n.recipient}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">{n.message_title}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                      n.status === 'sent' || n.status === 'delivered' ? 'bg-success-100 text-success-700' :
                      n.status === 'failed' ? 'bg-danger-100 text-danger-700' :
                      'bg-warning-100 text-warning-700'
                    }`}>{n.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right text-sm">{n.retry_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
