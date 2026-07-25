import { useState } from 'react'
import { reportAPI } from '../services/api'
import { HiOutlineDocumentText, HiOutlineDownload, HiOutlineCalendar } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Reports() {
  const [generating, setGenerating] = useState('')

  const generateReport = async (type, format) => {
    setGenerating(`${type}-${format}`)
    try {
      const response = await reportAPI[type](format)
      
      if (format === 'json') {
        toast.success('Report data ready')
        console.log(response.data)
        return
      }
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const extension = format === 'pdf' ? 'pdf' : format === 'excel' ? 'xlsx' : 'csv'
      a.download = `cnms_${type}_report.${extension}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      toast.success(`${type} report downloaded as ${format.toUpperCase()}`)
    } catch (err) {
      toast.error(`Failed to generate ${type} report`)
    } finally {
      setGenerating('')
    }
  }

  const reportTypes = [
    { id: 'daily', label: 'Daily Report', desc: 'Last 24 hours summary', icon: HiOutlineCalendar },
    { id: 'weekly', label: 'Weekly Report', desc: 'Last 7 days summary', icon: HiOutlineDocumentText },
    { id: 'monthly', label: 'Monthly Report', desc: 'Last 30 days summary', icon: HiOutlineDocumentText },
    { id: 'yearly', label: 'Yearly Report', desc: 'Last 365 days summary', icon: HiOutlineDocumentText },
  ]

  const formats = [
    { id: 'pdf', label: 'PDF', color: 'bg-danger-500' },
    { id: 'excel', label: 'Excel', color: 'bg-success-500' },
    { id: 'csv', label: 'CSV', color: 'bg-primary-500' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1>
        <p className="text-sm text-gray-500">Generate and download network monitoring reports</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {reportTypes.map(report => (
          <div key={report.id} className="card p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <report.icon className="w-5 h-5 text-primary-600" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{report.label}</h3>
                </div>
                <p className="text-sm text-gray-500">{report.desc}</p>
              </div>
            </div>
            <div className="flex gap-2">
              {formats.map(format => (
                <button
                  key={format.id}
                  onClick={() => generateReport(report.id, format.id)}
                  disabled={generating === `${report.id}-${format.id}`}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-white text-sm font-medium transition-all hover:opacity-90 disabled:opacity-50 ${format.color}`}
                >
                  {generating === `${report.id}-${format.id}` ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <HiOutlineDownload className="w-4 h-4" />
                  )}
                  {format.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
