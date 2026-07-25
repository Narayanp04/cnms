import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { HiOutlineUsers, HiOutlinePlus } from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Customers() {
  const { isAdmin } = useAuth()
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [formData, setFormData] = useState({
    name: '', code: '', email: '', phone: '', contact_person: '', contact_email: '', notes: ''
  })

  useEffect(() => {
    fetchCustomers()
  }, [])

  const fetchCustomers = async () => {
    try {
      const { data } = await api.get('/api/v1/customers')
      setCustomers(data || [])
    } catch (err) {
      toast.error('Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/v1/customers', formData)
      toast.success('Customer created')
      setShowAdd(false)
      setFormData({ name: '', code: '', email: '', phone: '', contact_person: '', contact_email: '', notes: '' })
      fetchCustomers()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create customer')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Customers</h1>
          <p className="text-sm text-gray-500">{customers.length} total customers</p>
        </div>
        {isAdmin && (
          <button onClick={() => setShowAdd(true)} className="btn-primary text-sm">
            <HiOutlinePlus className="w-4 h-4 inline mr-1" />
            Add Customer
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {customers.map(customer => (
          <div key={customer.id} className="card-hover p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                <HiOutlineUsers className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">{customer.name}</h3>
                <p className="text-xs text-gray-500">{customer.code}</p>
              </div>
            </div>
            <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              {customer.email && <p>✉ {customer.email}</p>}
              {customer.phone && <p>📞 {customer.phone}</p>}
              {customer.contact_person && <p>👤 {customer.contact_person}</p>}
              <p className="font-medium text-primary-600 mt-2">
                {customer.device_count || 0} devices
              </p>
            </div>
          </div>
        ))}
      </div>

      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="card p-6 max-w-lg w-full">
            <h3 className="text-lg font-semibold mb-4">Add Customer</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Name *</label>
                  <input className="input-field" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Code *</label>
                  <input className="input-field" value={formData.code} onChange={e => setFormData({...formData, code: e.target.value})} required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <input className="input-field" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone</label>
                  <input className="input-field" value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Contact Person</label>
                  <input className="input-field" value={formData.contact_person} onChange={e => setFormData({...formData, contact_person: e.target.value})} />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Notes</label>
                  <textarea className="input-field" rows={2} value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
