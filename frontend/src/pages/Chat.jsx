import { useState, useRef, useEffect } from 'react'
import api from '../api/client'
import RoleBadge from '../components/RoleBadge'
import './Chat.css'

function getUser() {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
}

function SourceCard({ source }) {
  return (
    <div className="source-card">
      <span className="source-title">{source.title}</span>
      <RoleBadge role={source.access_level} />
    </div>
  )
}

function Message({ msg }) {
  return (
    <div className={`message message-${msg.role}`}>
      <div className="message-bubble">
        <p className="message-text">{msg.content}</p>
        {msg.sources && msg.sources.length > 0 && (
          <div className="sources-section">
            <p className="sources-label">Sources used ({msg.sources.length})</p>
            <div className="sources-list">
              {msg.sources.map(s => <SourceCard key={s.doc_id} source={s} />)}
            </div>
          </div>
        )}
        {msg.sources && msg.sources.length === 0 && msg.role === 'assistant' && (
          <div className="sources-section">
            <p className="sources-label sources-empty">No documents retrieved (access restriction or no match)</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Chat() {
  const user = getUser()
  const [messages, setMessages] = useState([
    {
      id: 0,
      role: 'assistant',
      content: `Hello! I'm the University Document Assistant. Ask me anything about university policies, documents, or records. Your access level is "${user?.role || 'student'}".`,
      sources: null,
    }
  ])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSubmit(e) {
    e.preventDefault()
    const q = question.trim()
    if (!q || loading) return

    const userMsg = { id: Date.now(), role: 'user', content: q, sources: null }
    setMessages(prev => [...prev, userMsg])
    setQuestion('')
    setError('')
    setLoading(true)

    try {
      const res = await api.post('/chat/query', { question: q })
      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setError(err.response?.data?.detail || 'Request failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-container">
        <div className="messages-area">
          {messages.map(m => <Message key={m.id} msg={m} />)}
          {loading && (
            <div className="message message-assistant">
              <div className="message-bubble loading-bubble">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && <div className="chat-error error-msg">{error}</div>}

        <form className="chat-input-area" onSubmit={handleSubmit}>
          <textarea
            className="chat-input"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) } }}
            placeholder="Ask about university policies, records, or documents…"
            rows={2}
            disabled={loading}
          />
          <button className="btn btn-primary chat-send" type="submit" disabled={loading || !question.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}
