import './ClientSelector.css'

function ClientSelector({ customers, selectedClient, setSelectedClient }) {
  return (
    <div className="client-selector">
      <label htmlFor="client-select">Customer:</label>
      <select
        id="client-select"
        value={selectedClient || 'all'}
        onChange={(e) => setSelectedClient(e.target.value === 'all' ? null : e.target.value)}
        className="client-dropdown"
      >
        <option value="all">All Customers ({customers.length})</option>
        {customers.map(customer => (
          <option key={customer.id} value={customer.id}>
            {customer.name} - {customer.status === 'running' ? '✓' : '✗'} {customer.stack}
          </option>
        ))}
      </select>
    </div>
  )
}

export default ClientSelector
