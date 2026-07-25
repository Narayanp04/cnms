import { useState, useEffect } from 'react'
import { slaAPI } from '../services/api'
import { HiOutlineShieldCheck, HiOutlineDownload } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function SLAReports() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ period: '', device_id: '' })

  useEffect(() => {
    fetchReports()
  }, [filter])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filter.period) params.period = filter.period
      if (filter.device_id) params.device_id = filter.device_id
      const { data } = await slaAPI.getReports(params)
      setReports(data.items || [])
    } catch (err) {
      toast.error('Failed to load SLA reports')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">SLA Reports</h1>
          <p className="text-sm text-gray-500">Service Level Agreement reports and analysis</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {['daily', 'weekly', 'monthly', 'yearly'].map(period => (
          <div key={period} className="card p-6 text-center hover:shadow-md transition-shadow">
            <HiOutlineShieldCheck className="w-8 h-8 mx-auto mb-3 text-primary-600" />
            <h3 className="font-semibold text-gray-900 dark:text-white capitalize">{period} SLA</h3>
            <p className="text-2xl font-bold text-success-600 mt-2">
              {reports.filter(r => r.period === period).length || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">reports available</p>
          </div>
        ))}
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Device</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Period</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Availability</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Uptime</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Downtime</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Avg Latency</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">SLA Met</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {reports.map(report => (
                <tr key={report.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                  <td className="px-4 py-3 text-sm font-medium">{report.device_id}</td>
                  <td className="px-4 py-3 text-sm capitalize">{report.period}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={report.availability_percent >= 99.9 ? 'text-success-600 font-medium' : 'text-danger-600 font-medium'}>
                      {report.availability_percent?.toFixed(3)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-sm">{report.uptime_seconds}s</td>
                  <td className="px-4 py-3 text-right text-sm">{report.downtime_seconds}s</td>
                  <td className="px-4 py-3 text-right text-sm">{report.avg_latency_ms?.toFixed(1) || 'N/A'}ms</td>
                  <td className="px-4 py-3 text-center">
                    <span className={report.sla_met ? 'badge-up' : 'badge-down'}>
                      {report.sla_met ? 'YES' : 'NO'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="p-1 text-gray-400 hover:text-primary-600">
                      <HiOutlineDownload className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
