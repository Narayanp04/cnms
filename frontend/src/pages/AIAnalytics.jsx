import { useState, useEffect } from 'react'
import { aiAPI } from '../services/api'
import { HiOutlineLightBulb, HiOutlineChartBar, HiOutlineShieldCheck } from 'react-icons/hi'

export default function AIAnalytics() {
  const [summaries, setSummaries] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDevice, setSelectedDevice] = useState(null)
  const [analysis, setAnalysis] = useState(null)

  useEffect(() => {
    fetchSummaries()
  }, [])

  const fetchSummaries = async () => {
    try {
      const { data } = await aiAPI.getSummary()
      setSummaries(data.summaries || [])
    } catch (err) {
      console.error('Failed to load AI summaries')
    } finally {
      setLoading(false)
    }
  }

  const analyzeDevice = async (deviceId) => {
    setSelectedDevice(deviceId)
    try {
      const { data } = await aiAPI.analyzeDevice(deviceId)
      setAnalysis(data)
    } catch (err) {
      console.error('Failed to analyze device')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Analytics</h1>
        <p className="text-sm text-gray-500">AI-powered network analysis and predictions</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Device list */}
        <div className="lg:col-span-1 card p-4">
          <h3 className="font-semibold mb-3">Devices</h3>
          <div className="space-y-2">
            {summaries.map(s => (
              <button
                key={s.device_id}
                onClick={() => analyzeDevice(s.device_id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedDevice === s.device_id ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
              >
                <p className="font-medium text-sm">{s.hostname}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                  <span className={`px-1.5 py-0.5 rounded ${
                    s.health_score === 'excellent' ? 'bg-success-100 text-success-700' :
                    s.health_score === 'good' ? 'bg-primary-100 text-primary-700' :
                    s.health_score === 'fair' ? 'bg-warning-100 text-warning-700' :
                    'bg-danger-100 text-danger-700'
                  }`}>{s.health_score}</span>
                  <span>ISP: {s.isp_grade}</span>
                  <span className={`${s.failure_risk === 'critical' ? 'text-danger-600' : s.failure_risk === 'high' ? 'text-warning-600' : 'text-success-600'}`}>
                    Risk: {s.failure_risk}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Analysis detail */}
        <div className="lg:col-span-2 space-y-4">
          {selectedDevice && analysis ? (
            <>
              <div className="card p-6">
                <h3 className="font-semibold mb-3">AI Summary</h3>
                <div className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {analysis.ai_summary || 'No AI summary available'}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="card p-4 text-center">
                  <HiOutlineShieldCheck className="w-6 h-6 mx-auto mb-2 text-primary-600" />
                  <p className="text-2xl font-bold">{analysis.health_scores?.device_health_score || 'N/A'}</p>
                  <p className="text-xs text-gray-500">Device Health</p>
                </div>
                <div className="card p-4 text-center">
                  <HiOutlineChartBar className="w-6 h-6 mx-auto mb-2 text-success-600" />
                  <p className="text-2xl font-bold">{analysis.health_scores?.network_stability_score || 'N/A'}</p>
                  <p className="text-xs text-gray-500">Stability</p>
                </div>
                <div className="card p-4 text-center">
                  <HiOutlineLightBulb className="w-6 h-6 mx-auto mb-2 text-warning-600" />
                  <p className="text-2xl font-bold">{analysis.isp_quality_score?.grade || 'N/A'}</p>
                  <p className="text-xs text-gray-500">ISP Grade</p>
                </div>
              </div>
            </>
          ) : (
            <div className="card p-12 text-center text-gray-500">
              <HiOutlineLightBulb className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium mb-2">AI Analysis</p>
              <p className="text-sm">Select a device to view AI-powered analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
