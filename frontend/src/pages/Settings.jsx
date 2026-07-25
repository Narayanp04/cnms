import { useState, useEffect } from 'react'
import { settingsAPI } from '../services/api'
import { HiOutlineCog, HiOutlineBell, HiOutlineShieldCheck } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Settings() {
  const [systemSettings, setSystemSettings] = useState(null)
  const [notificationSettings, setNotificationSettings] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const [systemRes, notificationRes] = await Promise.all([
        settingsAPI.getSystem(),
        settingsAPI.getNotifications()
      ])
      setSystemSettings(systemRes.data)
      setNotificationSettings(notificationRes.data)
    } catch (err) {
      toast.error('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  const testWhatsApp = async () => {
    try {
      const { data } = await settingsAPI.testWhatsApp()
      toast.success(data.message)
    } catch (err) {
      toast.error('WhatsApp test failed')
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-sm text-gray-500">System configuration</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Settings */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <HiOutlineCog className="w-5 h-5 text-gray-400" />
            System Configuration
          </h3>
          <div className="space-y-3">
            {[
              { label: 'App Name', value: systemSettings?.app_name },
              { label: 'Version', value: systemSettings?.app_version },
              { label: 'SLA Target', value: `${systemSettings?.sla_target}%` },
              { label: 'High Latency Threshold', value: `${systemSettings?.high_latency_threshold}ms` },
              { label: 'Critical Latency', value: `${systemSettings?.critical_latency_threshold}ms` },
              { label: 'Ping Timeout', value: `${systemSettings?.ping_timeout}s` },
              { label: 'Ping Count', value: systemSettings?.ping_count },
              { label: 'Ping Threads', value: systemSettings?.ping_threads },
              { label: 'History Retention', value: `${systemSettings?.history_retention_days} days` },
              { label: 'Alert Cooldown', value: `${systemSettings?.alert_cooldown_seconds}s` },
            ].map(item => (
              <div key={item.label} className="flex justify-between text-sm">
                <span className="text-gray-500">{item.label}</span>
                <span className="font-medium text-gray-900 dark:text-white">{item.value || 'N/A'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Notification Settings */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <HiOutlineBell className="w-5 h-5 text-gray-400" />
            Notification Channels
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div>
                <p className="font-medium text-sm">WhatsApp</p>
                <p className="text-xs text-gray-500">
                  {notificationSettings?.whatsapp_configured ? 'Configured' : 'Not configured'}
                </p>
              </div>
              <button onClick={testWhatsApp} className="btn-secondary text-xs py-1.5">
                Test
              </button>
            </div>

            <div className={`flex items-center justify-between p-3 rounded-lg ${
              notificationSettings?.email_configured ? 'bg-gray-50 dark:bg-gray-700/50' : 'bg-gray-100 dark:bg-gray-800/50'
            }`}>
              <div>
                <p className="font-medium text-sm">Email</p>
                <p className="text-xs text-gray-500">
                  {notificationSettings?.email_configured ? 'Configured' : 'Not configured'}
                </p>
              </div>
            </div>

            <div className={`flex items-center justify-between p-3 rounded-lg ${
              notificationSettings?.telegram_configured ? 'bg-gray-50 dark:bg-gray-700/50' : 'bg-gray-100 dark:bg-gray-800/50'
            }`}>
              <div>
                <p className="font-medium text-sm">Telegram</p>
                <p className="text-xs text-gray-500">
                  {notificationSettings?.telegram_configured ? 'Configured' : 'Not configured'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Monitoring Settings */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <HiOutlineShieldCheck className="w-5 h-5 text-gray-400" />
            Monitoring Configuration
          </h3>
          <div className="space-y-3">
            {[
              { label: 'Packet Loss Warning', value: `${systemSettings?.high_packet_loss_threshold}%` },
              { label: 'Packet Loss Critical', value: `${systemSettings?.critical_packet_loss_threshold}%` },
              { label: 'Auto Backup', value: systemSettings?.auto_backup_enabled ? 'Enabled' : 'Disabled' },
              { label: 'Backup Interval', value: `${systemSettings?.auto_backup_interval_hours} hours` },
              { label: 'Backup Retention', value: `${systemSettings?.backup_retention_days} days` },
            ].map(item => (
              <div key={item.label} className="flex justify-between text-sm">
                <span className="text-gray-500">{item.label}</span>
                <span className="font-medium text-gray-900 dark:text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
