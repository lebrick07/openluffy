import { useState, useEffect, useRef } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './AIChatPanel.css'

function AIChatPanel({ isOpen }) {
  const { activeCustomer } = useCustomer()
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Build context for Luffy
      const context = {
        customer: activeCustomer ? activeCustomer.id : null,
        environment: 'all', // TODO: Get from global state
        resource_type: null,
        resource_name: null
      }

      // Send to Luffy
      const response = await fetch('/api/luffy/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputValue,
          context: context,
          history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })

      if (!response.ok) throw new Error('Luffy request failed')

      const data = await response.json()

      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.content,
        timestamp: new Date(),
        actions: data.actions || []
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('AI request failed:', error)
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'error',
        content: 'Failed to get AI response. Please try again.',
        timestamp: new Date()
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleAction = async (action) => {
    console.log('Action triggered:', action)
    
    // Build context
    const context = {
      customer: activeCustomer ? activeCustomer.id : null,
      environment: 'all',
      resource_type: null,
      resource_name: null
    }

    try {
      const response = await fetch('/api/luffy/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, context })
      })

      if (!response.ok) throw new Error('Action failed')

      const result = await response.json()

      // Add action result to messages
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'system',
        content: result.success 
          ? `✓ ${result.message}` 
          : `✗ ${result.message}`,
        timestamp: new Date()
      }])
    } catch (error) {
      console.error('Action failed:', error)
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'error',
        content: 'Action execution failed. Please try again.',
        timestamp: new Date()
      }])
    }
  }

  const getContextString = () => {
    const parts = []
    if (activeCustomer) parts.push(`Customer: ${activeCustomer.name}`)
    parts.push('All Environments')
    return parts.join(' | ')
  }

  return (
    <div className="ai-chat-panel split-panel">
      <div className="ai-chat-header">
        <div className="ai-header-left">
          <span className="ai-icon">⚔️</span>
          <div>
            <h3>Luffy – Captain's Deck</h3>
            <span className="ai-context">{getContextString()}</span>
          </div>
        </div>
      </div>

      <div className="ai-chat-messages">
        {messages.length === 0 && (
          <div className="ai-welcome">
            <span className="welcome-icon">👋</span>
            <h4>How can I help?</h4>
            <p>Ask me to:</p>
            <ul>
              <li>Explain failures</li>
              <li>Fix pipelines</li>
              <li>Deploy to production</li>
              <li>Rollback deployments</li>
              <li>Optimize costs</li>
            </ul>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`ai-message ai-message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : msg.role === 'error' ? '⚠️' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              {msg.actions && (
                <div className="message-actions">
                  {msg.actions.map((action, idx) => (
                    <button
                      key={idx}
                      className="action-btn"
                      onClick={() => handleAction(action.action)}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
              <span className="message-time">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="ai-message ai-message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="message-loading">
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="ai-chat-input">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Ask AI to troubleshoot, fix, or deploy..."
          rows={2}
          disabled={isLoading}
        />
        <button 
          className="send-btn"
          onClick={handleSend}
          disabled={!inputValue.trim() || isLoading}
        >
          {isLoading ? '...' : '↑'}
        </button>
      </div>
    </div>
  )
}

export default AIChatPanel
