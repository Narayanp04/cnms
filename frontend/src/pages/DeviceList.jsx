import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { deviceAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { 
  HiOutlinePlus, HiOutlineSearch, HiOutlineDownload, HiOutlineUpload,
  HiOutlineFilter, HiOutlineChevronDown, HiOutlinePencil, HiOutlineTrash,
  HiOutlineDotsVertical
} from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function DeviceList() {
  const navigate = useNavigate()
  const { isAdmin, isOperator } = useAuth()
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showBulkModal, setShowBulkModal] = useState(false)
  const pageSize = 20

  const fetchDevices = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await deviceAPI.list({ 
        page, 
        page_size: pageSize, 
        search: search || undefined,
        status: status || undefined,
      })
      setDevices(data.items || [])
      setTotalPages(data.total_pages)
      setTotal(data.total)
    } catch (err) {
      toast.error('Failed to load devices')
    } finally {
      setLoading(false)
    }
  }, [page, search, status])

  useEffect(() => {
    fetchDevices()
  }, [fetchDevices])

  const handleDelete = async (device) => {
    if (!confirm(`Are you sure you want to delete ${device.hostname}?`)) return
    try {
      await deviceAPI.delete(device.id)
      toast.success('Device deleted')
      fetchDevices()
    } catch (err) {
      toast.error('Failed to delete device')
    }
  }

  const handleBulkImport = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      const { data } = await deviceAPI.bulkImport(file)
      toast.success(`Imported ${data.success} devices (${data.failed} failed)`)
      fetchDevices()
      setShowBulkModal(false)
    } catch (err) {
      toast.error('Import failed')
    }
  }

  const handleExportCSV = async () => {
    try {
      const response = await deviceAPI.exportCSV()
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'devices_export.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('Devices exported')
    } catch (err) {
      toast.error('Export failed')
    }
  }

  const getStatusBadge = (status) => {
    const statusClasses = {
      'up': 'badge-up',
      'down': 'badge-down',
      'warning': 'badge-warning',
      'unknown': 'badge bg-gray-100 text-gray-700',
      'disabled': 'badge bg-gray-100 text-gray-500',
    }
    return (
      <span className={statusClasses[status] || statusClasses.unknown}>
        {status?.toUpperCase() || 'UNKNOWN'}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Devices</h1>
          <p className="text-sm text-gray-500">Manage your monitored devices ({total} total)</p>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && (
            <>
              <button onClick={() => setShowBulkModal(true)} className="btn-secondary text-sm">
                <HiOutlineUpload className="w-4 h-4 inline mr-1" />
                Bulk Import
              </button>
              <button onClick={handleExportCSV} className="btn-secondary text-sm">
                <HiOutlineDownload className="w-4 h-4 inline mr-1" />
                Export
              </button>
            </>
          )}
          {(isAdmin || isOperator) && (
            <button onClick={() => setShowAddModal(true)} className="btn-primary text-sm">
              <HiOutlinePlus className="w-4 h-4 inline mr-1" />
              Add Device
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <HiOutlineSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search by hostname, IP, customer..."
            className="input-field pl-10 text-sm"
          />
        </div>
        <select 
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
          className="input-field text-sm py-2 w-auto"
        >
          <option value="">All Status</option>
          <option value="up">UP</option>
          <option value="down">DOWN</option>
          <option value="warning">Warning</option>
          <option value="disabled">Disabled</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Hostname</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">IP Address</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Customer</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Site</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Region</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Latency</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">SLA 24h</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr><td colSpan={9} className="text-center py-8 text-gray-500">Loading...</td></tr>
              ) : devices.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-8 text-gray-500">No devices found</td></tr>
              ) : (
                devices.map((device) => (
                  <tr 
                    key={device.id}
                    onClick={() => navigate(`/devices/${device.id}`)}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900 dark:text-white">{device.hostname}</p>
                      <p className="text-xs text-gray-500">{device.display_name || ''}</p>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 font-mono">{device.ip_address}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{device.customer_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{device.site_name || '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{device.region || '-'}</td>
                    <td className="px-4 py-3 text-center">{getStatusBadge(device.status)}</td>
                    <td className="px-4 py-3 text-right text-sm">
                      <span className={device.current_latency > 150 ? 'text-danger-600 font-medium' : 'text-gray-600 dark:text-gray-400'}>
                        {device.current_latency ? `${device.current_latency.toFixed(1)}ms` : '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-sm">
                      <span className={device.sla_24h < 99 ? 'text-danger-600 font-medium' : 'text-gray-600 dark:text-gray-400'}>
                        {device.sla_24h?.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {(isAdmin || isOperator) && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(device) }}
                          className="p-1 text-gray-400 hover:text-danger-600 transition-colors"
                        >
                          <HiOutlineTrash className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages} ({total} total)
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary text-sm py-1.5 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="btn-secondary text-sm py-1.5 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Add Device Modal */}
      {showAddModal && (
        <AddDeviceModal onClose={() => setShowAddModal(false)} onSuccess={fetchDevices} />
      )}

      {/* Bulk Import Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="card p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Bulk Import Devices</h3>
            <p className="text-sm text-gray-500 mb-4">
              Upload a CSV file with columns: hostname, ip_address, customer_name, site_name, region, circuit_id, provider
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={handleBulkImport}
              className="w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setShowBulkModal(false)} className="btn-secondary text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AddDeviceModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    hostname: '', ip_address: '', customer_name: '', site_name: '',
    region: '', circuit_id: '', bandwidth: '', provider: '',
    category: '', polling_interval: '30s'
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await deviceAPI.create(formData)
      toast.success('Device added successfully')
      onSuccess()
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add device')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="card p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">Add New Device</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Hostname *</label>
              <input className="input-field" value={formData.hostname} onChange={e => setFormData({...formData, hostname: e.target.value})} required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">IP Address *</label>
              <input className="input-field" value={formData.ip_address} onChange={e => setFormData({...formData, ip_address: e.target.value})} required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Customer Name</label>
              <input className="input-field" value={formData.customer_name} onChange={e => setFormData({...formData, customer_name: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Site Name</label>
              <input className="input-field" value={formData.site_name} onChange={e => setFormData({...formData, site_name: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Region</label>
              <input className="input-field" value={formData.region} onChange={e => setFormData({...formData, region: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Circuit ID</label>
              <input className="input-field" value={formData.circuit_id} onChange={e => setFormData({...formData, circuit_id: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Provider</label>
              <input className="input-field" value={formData.provider} onChange={e => setFormData({...formData, provider: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Bandwidth</label>
              <input className="input-field" value={formData.bandwidth} onChange={e => setFormData({...formData, bandwidth: e.target.value})} />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Adding...' : 'Add Device'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
