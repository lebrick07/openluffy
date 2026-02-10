import { useState, useEffect } from 'react'
import './CostWidget.css'

function CostWidget() {
  const [costs, setCosts] = useState({
    today: 4.73,
    week: 28.45,
    month: 142.35,
    trend: '+12%',
    budget: 500,
    alert: false
  })

  const budgetPercent = (costs.month / costs.budget) * 100
  const isWarning = budgetPercent > 70
  const isDanger = budgetPercent > 90

  return (
    <div className={`cost-widget ${isDanger ? 'danger' : isWarning ? 'warning' : ''}`}>
      <div className="cost-header">
        <h4>💰 Cost Tracking</h4>
        {(isWarning || isDanger) && (
          <span className="cost-alert">⚠️ {budgetPercent.toFixed(0)}% of budget</span>
        )}
      </div>
      
      <div className="cost-main">
        <div className="cost-amount">
          <span className="currency">$</span>
          <span className="value">{costs.month.toFixed(2)}</span>
          <span className="period">this month</span>
        </div>
        <div className="cost-trend">
          <span className={costs.trend.startsWith('+') ? 'trend-up' : 'trend-down'}>
            {costs.trend} vs last month
          </span>
        </div>
      </div>

      <div className="cost-breakdown">
        <div className="cost-item">
          <span className="label">Today</span>
          <span className="value">${costs.today}</span>
        </div>
        <div className="cost-item">
          <span className="label">This Week</span>
          <span className="value">${costs.week}</span>
        </div>
      </div>

      <div className="cost-budget">
        <div className="budget-bar">
          <div 
            className={`budget-fill ${isDanger ? 'danger' : isWarning ? 'warning' : ''}`}
            style={{ width: `${Math.min(budgetPercent, 100)}%` }}
          />
        </div>
        <div className="budget-text">
          ${costs.month} / ${costs.budget} monthly budget
        </div>
      </div>
    </div>
  )
}

export default CostWidget
