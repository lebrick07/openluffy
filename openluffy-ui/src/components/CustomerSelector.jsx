import { useState, useEffect } from 'react'
import './CustomerSelector.css'

function CustomerSelector({ selectedCustomer, onCustomerChange }) {
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCustomers()
  }, [])

  const fetchCustomers = async () => {
    try {
      const response = await fetch('/api/customers')
      const data = await response.json()
      setCustomers(data.customers || [])
    } catch (error) {
      console.error('Error fetching customers:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="customer-selector loading">Loading...</div>
  }

  return (
    <div className="customer-selector">
      <label>Customer:</label>
      <select
        value={selectedCustomer || 'all'}
        onChange={(e) => onCustomerChange(e.target.value === 'all' ? null : e.target.value)}
      >
        <option value="all">All Customers</option>
        {customers.map(c => (
          <option key={c.id} value={c.id}>
            {c.name} ({c.stack})
          </option>
        ))}
      </select>
      {selectedCustomer && (
        <button 
          className="btn-clear-filter"
          onClick={() => onCustomerChange(null)}
          title="Clear filter"
        >
          ✕
        </button>
      )}
    </div>
  )
}

export default CustomerSelector
