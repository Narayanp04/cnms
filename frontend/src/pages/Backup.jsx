import { useState, useEffect } from 'react'
import { backupAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { HiOutlineDatabase, HiOutlineDownload, HiOutlineTrash, HiOutlineRefresh } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Backup() {
  const { isAdmin } = useAuth()
  const [backups, setBackups] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    fetchBackups()
  }, [])

  const fetchBackups = async () => {
    setLoading(true)
    try {
      const { data } = await backupAPI.list()
      setBackups(data.backups || [])
    } catch (err) {
      toast.error('Failed to load backups')
    } finally {
      setLoading(false)
    }
  }

  const createBackup = async () => {
    setCreating(true)
    try {
      const { data } = await backupAPI.create()
      toast.success(data.message)
      fetchBackups()
    } catch (err) {
      toast.error('Backup failed')
    } finally {
      setCreating(false)
    }
  }

  const restoreBackup = async (filepath) => {
    if (!confirm('Are you sure you want to restore this backup? This will overwrite current data.')) return
    try {
      const { data } = await backupAPI.restore(filepath)
      toast.success(data.message)
    } catch (err) {
      toast.error('Restore failed')
    }
  }

  const deleteBackup = async (filepath) => {
    if (!confirm('Delete this backup?')) return
    try {
      await backupAPI.delete(filepath)
      toast.success('Backup deleted')
      fetchBackups()
    } catch (err) {
      toast.error('Delete failed')
    }
  }

  if (!isAdmin) {
    return <div className="text-center py-12 text-gray-500">You need admin permissions to access this page.</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Database Backup</h1>
          <p className="text-sm text-gray-500">Manage database backups and restore</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchBackups} className="btn-secondary text-sm">
            <HiOutlineRefresh className="w-4 h-4 inline mr-1" />
            Refresh
          </button>
          <button onClick={createBackup} disabled={creating} className="btn-primary text-sm">
            {creating ? 'Creating...' : 'Create Backup'}
          </button>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-4 mb-4">
          <HiOutlineDatabase className="w-10 h-10 text-primary-600" />
          <div>
            <h3 className="font-semibold">Automatic Backups</h3>
            <p className="text-sm text-gray-500">Automatic backups are created every 24 hours. Backups are retained for 30 days.</p>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Backup File</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Size</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Created</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {backups.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-8 text-gray-500">No backups available</td></tr>
              ) : (
                backups.map(backup => (
                  <tr key={backup.filename} className="hover:bg-gray-50 dark:hover:bg-gray-700/30">
                    <td className="px-4 py-3 text-sm font-medium">{backup.filename}</td>
                    <td className="px-4 py-3 text-right text-sm">{backup.size_human}</td>
                    <td className="px-4 py-3 text-right text-sm text-gray-500" suppressHydrationWarning>
                      {new Date(backup.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button onClick={() => restoreBackup(backup.path)} className="p-1 text-primary-600 hover:text-primary-700" title="Restore">
                          <HiOutlineDownload className="w-4 h-4" />
                        </button>
                        <button onClick={() => deleteBackup(backup.path)} className="p-1 text-danger-600 hover:text-danger-700" title="Delete">
                          <HiOutlineTrash className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
