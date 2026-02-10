import { useState, useEffect, useRef } from 'react'
import './LogViewer.css'

function LogViewer({ deploymentId, deploymentName, namespace, customer }) {
  const [pods, setPods] = useState([])
  const [selectedPod, setSelectedPod] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterLevel, setFilterLevel] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [followMode, setFollowMode] = useState(false)
  const [lines, setLines] = useState(500)
  const logsEndRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    fetchPods()
  }, [deploymentId])

  useEffect(() => {
    if (selectedPod) {
      fetchLogs()
    }
  }, [selectedPod, lines])

  useEffect(() => {
    if (autoRefresh && selectedPod) {
      intervalRef.current = setInterval(fetchLogs, 5000)
      return () => clearInterval(intervalRef.current)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [autoRefresh, selectedPod])

  useEffect(() => {
    if (followMode) {
      scrollToBottom()
    }
  }, [logs, followMode])

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchPods = async () => {
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/details-v2`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setPods(data.pods || [])
      if (data.pods && data.pods.length > 0) {
        setSelectedPod(data.pods[0].name)
      }
    } catch (error) {
      console.error('Error fetching pods:', error)
    }
  }

  const fetchLogs = async () => {
    if (!selectedPod) return
    
    setLoading(true)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/pods/${selectedPod}/logs?lines=${lines}`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      
      // Parse logs into structured format
      const parsedLogs = data.logs.split('\n').map((line, idx) => {
        const logObj = {
          id: idx,
          raw: line,
          timestamp: null,
          level: 'INFO',
          message: line
        }

        // Try to parse common log formats
        // ISO timestamp at start: 2026-02-10T12:34:56.789Z
        const isoMatch = line.match(/^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:?\d{2})?)/)
        if (isoMatch) {
          logObj.timestamp = isoMatch[1]
          logObj.message = line.substring(isoMatch[0].length).trim()
        }

        // Detect log level
        if (/\b(ERROR|ERR|FATAL|CRITICAL)\b/i.test(line)) {
          logObj.level = 'ERROR'
        } else if (/\b(WARN|WARNING)\b/i.test(line)) {
          logObj.level = 'WARN'
        } else if (/\b(DEBUG|TRACE)\b/i.test(line)) {
          logObj.level = 'DEBUG'
        } else if (/\b(INFO)\b/i.test(line)) {
          logObj.level = 'INFO'
        }

        return logObj
      }).filter(log => log.raw.trim())

      setLogs(parsedLogs)
    } catch (error) {
      console.error('Error fetching logs:', error)
      setLogs([{ id: 0, raw: 'Error loading logs', level: 'ERROR', message: 'Error loading logs' }])
    } finally {
      setLoading(false)
    }
  }

  const downloadLogs = () => {
    const content = logs.map(log => log.raw).join('\n')
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${deploymentName}-${selectedPod}-logs.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const copyToClipboard = () => {
    const content = logs.map(log => log.raw).join('\n')
    navigator.clipboard.writeText(content).then(() => {
      alert('Logs copied to clipboard!')
    })
  }

  const filteredLogs = logs.filter(log => {
    if (filterLevel !== 'all' && log.level !== filterLevel) return false
    if (searchTerm && !log.raw.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  return (
    <div className="log-viewer">
      <div className="log-viewer-header">
        <div className="log-context">
          <div className="context-item">
            <span className="context-label">Customer:</span>
            <span className="context-value">{customer}</span>
          </div>
          <div className="context-item">
            <span className="context-label">Deployment:</span>
            <span className="context-value">{deploymentName}</span>
          </div>
          <div className="context-item">
            <span className="context-label">Namespace:</span>
            <span className="context-value">{namespace}</span>
          </div>
        </div>
      </div>

      <div className="log-controls">
        <div className="controls-left">
          <div className="control-group">
            <label>Pod:</label>
            <select 
              value={selectedPod || ''}
              onChange={(e) => setSelectedPod(e.target.value)}
              disabled={pods.length === 0}
            >
              {pods.map(pod => (
                <option key={pod.name} value={pod.name}>
                  {pod.name} ({pod.status})
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Lines:</label>
            <select value={lines} onChange={(e) => setLines(Number(e.target.value))}>
              <option value="100">100</option>
              <option value="500">500</option>
              <option value="1000">1000</option>
              <option value="5000">5000</option>
            </select>
          </div>

          <div className="control-group">
            <label>Level:</label>
            <select value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)}>
              <option value="all">All</option>
              <option value="ERROR">ERROR</option>
              <option value="WARN">WARN</option>
              <option value="INFO">INFO</option>
              <option value="DEBUG">DEBUG</option>
            </select>
          </div>

          <div className="control-group search-group">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        <div className="controls-right">
          <button
            className={`btn-toggle ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title="Auto-refresh every 5s"
          >
            🔄 {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </button>
          <button
            className={`btn-toggle ${followMode ? 'active' : ''}`}
            onClick={() => setFollowMode(!followMode)}
            title="Auto-scroll to bottom"
          >
            ⬇️ {followMode ? 'Follow ON' : 'Follow OFF'}
          </button>
          <button
            className="btn-action"
            onClick={fetchLogs}
            disabled={loading || !selectedPod}
          >
            🔄 Refresh
          </button>
          <button
            className="btn-action"
            onClick={downloadLogs}
            disabled={logs.length === 0}
          >
            💾 Download
          </button>
          <button
            className="btn-action"
            onClick={copyToClipboard}
            disabled={logs.length === 0}
          >
            📋 Copy
          </button>
        </div>
      </div>

      <div className="log-stats">
        <span className="stat-item">
          <strong>{filteredLogs.length}</strong> / {logs.length} lines
        </span>
        <span className="stat-item">
          <span className="level-badge level-error">
            {logs.filter(l => l.level === 'ERROR').length} errors
          </span>
        </span>
        <span className="stat-item">
          <span className="level-badge level-warn">
            {logs.filter(l => l.level === 'WARN').length} warnings
          </span>
        </span>
      </div>

      {loading && logs.length === 0 ? (
        <div className="log-loading">Loading logs...</div>
      ) : (
        <div className="log-content">
          <div className="log-lines">
            {filteredLogs.map(log => (
              <div key={log.id} className={`log-line log-level-${log.level.toLowerCase()}`}>
                <span className="log-line-number">{log.id + 1}</span>
                {log.timestamp && (
                  <span className="log-timestamp">{log.timestamp}</span>
                )}
                <span className={`log-level-badge badge-${log.level.toLowerCase()}`}>
                  {log.level}
                </span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}

      {!selectedPod && (
        <div className="no-pod-selected">
          Select a pod to view logs
        </div>
      )}

      {filteredLogs.length === 0 && logs.length > 0 && (
        <div className="no-logs-match">
          No logs match the current filters
        </div>
      )}
    </div>
  )
}

export default LogViewer
