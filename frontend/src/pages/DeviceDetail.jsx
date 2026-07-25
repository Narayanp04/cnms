import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { monitoringAPI, deviceAPI, slaAPI, aiAPI } from '../services/api'
import ReactEChartsCore from 'echarts-for-react'
import { 
  HiOutlineArrowLeft, HiOutlineChartBar, HiOutlineClock, 
  HiOutlineShieldCheck, HiOutlineLightBulb
} from 'react-icons/hi'
import toast from 'react-hot-toast'

const TIME_PERIODS = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '12h', label: '12 Hours' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: '180d', label: '180 Days' },
  { value: '365d', label: '365 Days' },
]

export default function DeviceDetail() {
  const { id } = useParams()
  const [device, setDevice] = useState(null)
  const [history, setHistory] = useState(null)
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [selectedPeriod, setSelectedPeriod] = useState('24h')
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchData()
  }, [id, selectedPeriod])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [deviceRes, historyRes] = await Promise.all([
        deviceAPI.get(id),
        monitoringAPI.getHistory(id, selectedPeriod),
      ])
      setDevice(deviceRes.data)
      setHistory(historyRes.data)
      
      // Fetch AI analysis
      try {
        const aiRes = await aiAPI.analyzeDevice(id)
        setAiAnalysis(aiRes.data)
      } catch (e) {
        console.log('AI analysis not available')
      }
    } catch (err) {
      toast.error('Failed to load device details')
    } finally {
      setLoading(false)
    }
  }

  const latencyChartOption = history ? {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: history.timestamps?.map(t => new Date(t).toLocaleTimeString()) || [],
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', name: 'Latency (ms)' },
    series: [{
      name: 'Latency',
      type: 'line',
      data: history.latency || [],
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#4c6ef5', width: 2 },
      areaStyle: { color: 'rgba(76, 110, 245, 0.1)' },
    }]
  } : null

  const packetLossChartOption = history ? {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: history.timestamps?.map(t => new Date(t).toLocaleTimeString()) || [],
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', name: 'Packet Loss %', max: 100 },
    series: [{
      name: 'Packet Loss',
      type: 'bar',
      data: history.packet_loss || [],
      itemStyle: { 
        color: (params) => params.value > 5 ? '#ef4444' : params.value > 0 ? '#eab308' : '#22c55e'
      },
    }]
  } : null

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>
  }

  if (!device) {
    return <div className="text-center py-12 text-gray-500">Device not found</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => window.history.back()} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
          <HiOutlineArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{device.hostname}</h1>
          <p className="text-sm text-gray-500">{device.ip_address} • {device.customer_name || 'N/A'}</p>
        </div>
        <div className="ml-auto">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            device.status === 'up' ? 'bg-success-100 text-success-700' :
            device.status === 'down' ? 'bg-danger-100 text-danger-700' :
            device.status === 'warning' ? 'bg-warning-100 text-warning-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {device.status?.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-sm text-gray-500">Latency</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {device.current_latency ? `${device.current_latency.toFixed(1)}ms` : 'N/A'}
          </p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-sm text-gray-500">Packet Loss</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">
            {device.current_packet_loss ? `${device.current_packet_loss.toFixed(1)}%` : '0%'}
          </p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-sm text-gray-500">SLA 24h</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">{device.sla_24h?.toFixed(2)}%</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-sm text-gray-500">SLA 30d</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">{device.sla_30d?.toFixed(2)}%</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
        {[
          { id: 'overview', label: 'Overview', icon: HiOutlineChartBar },
          { id: 'ai', label: 'AI Analysis', icon: HiOutlineLightBulb },
          { id: 'sla', label: 'SLA', icon: HiOutlineShieldCheck },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === tab.id ? 'bg-white dark:bg-gray-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Period selector */}
          <div className="flex flex-wrap gap-2">
            {TIME_PERIODS.map(p => (
              <button
                key={p.value}
                onClick={() => setSelectedPeriod(p.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                  selectedPeriod === p.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Latency Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Latency History</h3>
            {latencyChartOption && (
              <ReactEChartsCore option={latencyChartOption} style={{ height: '350px' }} notMerge />
            )}
          </div>

          {/* Packet Loss Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold mb-4">Packet Loss History</h3>
            {packetLossChartOption && (
              <ReactEChartsCore option={packetLossChartOption} style={{ height: '250px' }} notMerge />
            )}
          </div>
        </div>
      )}

      {/* AI Analysis Tab */}
      {activeTab === 'ai' && (
        <div className="space-y-6">
          {aiAnalysis ? (
            <>
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-4">AI Analysis Summary</h3>
                <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300 leading-relaxed">
                  {aiAnalysis.ai_summary || 'No analysis available'}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card p-6 text-center">
                  <p className="text-sm text-gray-500">Device Health</p>
                  <p className="text-3xl font-bold mt-2">{aiAnalysis.health_scores?.device_health_score || 'N/A'}</p>
                  <p className="text-sm text-gray-500 mt-1">/ 100</p>
                </div>
                <div className="card p-6 text-center">
                  <p className="text-sm text-gray-500">Network Stability</p>
                  <p className="text-3xl font-bold mt-2">{aiAnalysis.health_scores?.network_stability_score || 'N/A'}</p>
                  <p className="text-sm text-gray-500 mt-1">/ 100</p>
                </div>
                <div className="card p-6 text-center">
                  <p className="text-sm text-gray-500">ISP Quality</p>
                  <p className="text-3xl font-bold mt-2">{aiAnalysis.isp_quality_score?.grade || 'N/A'}</p>
                  <p className="text-sm text-gray-500 mt-1">{aiAnalysis.isp_quality_score?.score || 'N/A'}/100</p>
                </div>
              </div>

              {/* Recommendations */}
              {aiAnalysis.recommendations?.length > 0 && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
                  <div className="space-y-3">
                    {aiAnalysis.recommendations.map((rec, i) => (
                      <div key={i} className={`p-4 rounded-lg border ${
                        rec.priority === 'critical' ? 'border-danger-200 bg-danger-50 dark:bg-danger-900/20' :
                        rec.priority === 'high' ? 'border-warning-200 bg-warning-50 dark:bg-warning-900/20' :
                        'border-gray-200 bg-gray-50 dark:bg-gray-700/50'
                      }`}>
                        <p className="font-medium text-sm mb-2">{rec.message}</p>
                        <ul className="space-y-1">
                          {rec.actions?.map((action, j) => (
                            <li key={j} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                              <span className="text-primary-500 mt-0.5">•</span>
                              {action}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Patterns */}
              {aiAnalysis.patterns?.patterns_found && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold mb-4">Detected Patterns</h3>
                  <ul className="space-y-2">
                    {aiAnalysis.patterns.details?.map((detail, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-warning-500 mt-0.5">⚠</span>
                        <span className="text-gray-700 dark:text-gray-300">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div className="card p-6 text-center text-gray-500">
              AI analysis not available. Ensure the device has sufficient ping history.
            </div>
          )}
        </div>
      )}

      {/* SLA Tab */}
      {activeTab === 'sla' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: '24 Hours', value: device.sla_24h },
              { label: '7 Days', value: device.sla_7d },
              { label: '30 Days', value: device.sla_30d },
              { label: '365 Days', value: device.sla_365d },
            ].map(item => (
              <div key={item.label} className="card p-6 text-center">
                <p className="text-sm text-gray-500">{item.label}</p>
                <p className="text-2xl font-bold mt-2 text-gray-900 dark:text-white">
                  {item.value?.toFixed(3)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
