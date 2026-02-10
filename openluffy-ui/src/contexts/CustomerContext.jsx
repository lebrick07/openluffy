import { createContext, useContext, useState, useEffect } from 'react'

const CustomerContext = createContext()

export const useCustomer = () => {
  const context = useContext(CustomerContext)
  if (!context) {
    throw new Error('useCustomer must be used within CustomerProvider')
  }
  return context
}

export const CustomerProvider = ({ children }) => {
  const [customers, setCustomers] = useState([])
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCustomers()
  }, [])

  const fetchCustomers = async () => {
    try {
      const res = await fetch('/api/customers')
      const data = await res.json()
      setCustomers(data.customers || [])
    } catch (err) {
      console.error('Failed to fetch customers:', err)
    } finally {
      setLoading(false)
    }
  }

  const selectCustomer = (customerId) => {
    setSelectedCustomer(customerId)
  }

  const addCustomer = (customer) => {
    setCustomers(prev => [...prev, customer])
    setSelectedCustomer(customer.id)
  }

  const refreshCustomers = () => {
    fetchCustomers()
  }

  const value = {
    customers,
    selectedCustomer,
    loading,
    selectCustomer,
    addCustomer,
    refreshCustomers,
    // Computed values
    activeCustomer: customers.find(c => c.id === selectedCustomer) || null
  }

  return (
    <CustomerContext.Provider value={value}>
      {children}
    </CustomerContext.Provider>
  )
}
