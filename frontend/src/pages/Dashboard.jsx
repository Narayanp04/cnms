import { useState, useEffect } from 'react'
import { dashboardAPI, monitoringAPI, alertAPI } from '../services/api'
import { useTheme } from '../context/ThemeContext'
import { 
  HiOutlineServer, HiOutlineArrowUp, HiOutlineArrowDown,
  HiOutlineExclamation, HiOutlineClock, HiOutlineChartBar,
  HiOutlineShieldCheck
} from 'react-icons/hi'
import ReactEChartsCore from 'echarts-for-react'

function StatCard({ icon: Icon, label, value, subtext, color, trend }) {
  return (
    <div className="card p-6 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{label}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          {subtext && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtext}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`mt-3 text-xs font-medium ${trend >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
          {trend >= 0 ? '+' : ''}{trend}% from last month
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [topLatency, setTopLatency] = useState([])
  const [topLoss, setTopLoss] = useState([])
  const [recentAlerts, setRecentAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchDashboard = async () => {
    try {
      const [statsRes, monitoringRes, alertsRes] = await Promise.all([
        dashboardAPI.getDashboard(),
        monitoringAPI.getDeviceStatus(),
        alertAPI.list({ limit: 10 }),
      ])
      
      setStats(statsRes.data.stats)
      setTopLatency(statsRes.data.top_high_latency || [])
      setTopLoss(statsRes.data.top_packet_loss || [])
      setRecentAlerts(alertsRes.data || [])
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
    const interval = setInterval(fetchDashboard, refreshInterval * 1000)
    return () => clearInterval(interval)
  }, [refreshInterval])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const availabilityChartOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['50%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: [
        { value: stats?.up_devices || 0, name: 'UP', itemStyle: { color: '#22c55e' } },
        { value: stats?.down_devices || 0, name: 'DOWN', itemStyle: { color: '#ef4444' } },
        { value: stats?.warning_devices || 0, name: 'Warning', itemStyle: { color: '#eab308' } },
        { value: stats?.disabled_devices || 0, name: 'Disabled', itemStyle: { color: '#9ca3af' } },
      ]
    }]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Network Status Overview
            {lastUpdated && (
              <span className="ml-2">• Updated {lastUpdated.toLocaleTimeString()}</span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select 
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="input-field text-sm py-1.5 w-auto"
          >
            <option value={5}>5s</option>
            <option value={10}>10s</option>
            <option value={30}>30s</option>
            <option value={60}>60s</option>
          </select>
          <button onClick={fetchDashboard} className="btn-secondary text-sm py-1.5">
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          icon={HiOutlineServer}
          label="Total Devices"
          value={stats?.total_devices || 0}
          subtext={`${stats?.monitored_devices || 0} monitored`}
          color="bg-primary-100 dark:bg-primary-900/20 text-primary-600"
        />
        <StatCard 
          icon={HiOutlineArrowUp}
          label="UP Devices"
          value={stats?.up_devices || 0}
          subtext={`${((stats?.up_devices / stats?.total_devices) * 100 || 0).toFixed(1)}% of total`}
          color="bg-success-100 dark:bg-success-900/20 text-success-600"
        />
        <StatCard 
          icon={HiOutlineArrowDown}
          label="DOWN Devices"
          value={stats?.down_devices || 0}
          subtext={`${stats?.unresolved_alerts || 0} active alerts`}
          color="bg-danger-100 dark:bg-danger-900/20 text-danger-600"
        />
        <StatCard 
          icon={HiOutlineShieldCheck}
          label="Avg SLA"
          value={`${stats?.average_sla_percent?.toFixed(2) || '100.00'}%`}
          subtext={`${stats?.average_latency ? `${stats.average_latency.toFixed(1)}ms avg latency` : 'No data'}`}
          color="bg-warning-100 dark:bg-warning-900/20 text-warning-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Charts Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Device Availability Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Device Availability
            </h3>
            <ReactEChartsCore 
              option={availabilityChartOption}
              style={{ height: '250px' }}
              notMerge={true}
            />
            <div className="grid grid-cols-4 gap-2 mt-4 text-center text-sm">
              <div>
                <div className="w-3 h-3 rounded-full bg-success-500 mx-auto mb-1"></div>
                <p className="font-medium text-success-600">{stats?.up_devices || 0}</p>
                <p className="text-gray-500 text-xs">UP</p>
              </div>
              <div>
                <div className="w-3 h-3 rounded-full bg-danger-500 mx-auto mb-1"></div>
                <p className="font-medium text-danger-600">{stats?.down_devices || 0}</p>
                <p className="text-gray-500 text-xs">DOWN</p>
              </div>
              <div>
                <div className="w-3 h-3 rounded-full bg-warning-500 mx-auto mb-1"></div>
                <p className="font-medium text-warning-600">{stats?.warning_devices || 0}</p>
                <p className="text-gray-500 text-xs">Warning</p>
              </div>
              <div>
                <div className="w-3 h-3 rounded-full bg-gray-400 mx-auto mb-1"></div>
                <p className="font-medium text-gray-600">{stats?.disabled_devices || 0}</p>
                <p className="text-gray-500 text-xs">Disabled</p>
              </div>
            </div>
          </div>

          {/* Top High Latency */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Top High Latency Devices
            </h3>
            <div className="space-y-3">
              {topLatency.slice(0, 5).map((device, i) => (
                <div key={device.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-500 w-6">{i + 1}.</span>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{device.hostname}</p>
                      <p className="text-xs text-gray-500">{device.ip_address} • {device.customer_name || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-danger-600">{device.current_latency?.toFixed(1)}ms</p>
                    <p className="text-xs text-gray-500">latency</p>
                  </div>
                </div>
              ))}
              {topLatency.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">No high latency devices</p>
              )}
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-6">
          {/* Recent Alerts */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Recent Alerts
            </h3>
            <div className="space-y-3">
              {recentAlerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-start gap-3 p-2">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    alert.severity === 'critical' ? 'bg-danger-500' :
                    alert.severity === 'high' ? 'bg-warning-500' : 'bg-primary-500'
                  }`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {alert.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {alert.device_hostname || 'Unknown'} • {new Date(alert.triggered_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
              {recentAlerts.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">No recent alerts</p>
              )}
            </div>
          </div>

          {/* Top Packet Loss */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Top Packet Loss
            </h3>
            <div className="space-y-3">
              {topLoss.slice(0, 5).map((device, i) => (
                <div key={device.id} className="flex items-center justify-between p-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {device.hostname}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{device.ip_address}</p>
                  </div>
                  <p className="font-bold text-danger-600 ml-2">
                    {device.packet_loss?.toFixed(1)}%
                  </p>
                </div>
              ))}
              {topLoss.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">No packet loss detected</p>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Quick Stats
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Customers</span>
                <span className="font-medium">{stats?.total_customers || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Alerts (24h)</span>
                <span className="font-medium">{stats?.new_alerts_24h || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Unresolved</span>
                <span className="font-medium">{stats?.unresolved_alerts || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Avg Latency</span>
                <span className="font-medium">{stats?.average_latency?.toFixed(1) || 'N/A'}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Avg Packet Loss</span>
                <span className="font-medium">{stats?.average_packet_loss?.toFixed(2) || '0'}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
