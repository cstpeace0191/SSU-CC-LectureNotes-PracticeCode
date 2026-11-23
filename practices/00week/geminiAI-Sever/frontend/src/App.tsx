import { useState, useEffect, useRef } from 'react'
import type { KeyboardEvent, JSX } from 'react'
import './App.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatResponse {
  response: string
  session_id: string
}

export default function App(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [sessionId, setSessionId] = useState<string>(() => `session-${Math.random().toString(36).substring(2, 9)}`)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  // 메시지 추가 시 자동 하단 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  // 질문 전송
  const handleSend = async (): Promise<void> => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMessage: Message = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // 텍스트 영역 높이 초기화
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      let res: Response

      try {
        res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
          }),
        })
      } catch {
        // 프록시 실패 시 직접 백엔드 주소로 호출
        res = await fetch('http://127.0.0.1:8000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
          }),
        })
      }

      if (!res.ok) {
        const errData = (await res.json().catch(() => ({}))) as { detail?: string }
        throw new Error(errData.detail || `서버 오류 (${res.status})`)
      }

      const data = (await res.json()) as ChatResponse
      const assistantMessage: Message = {
        id: `msg-${Date.now()}-bot`,
        role: 'assistant',
        content: data.response || '(응답이 없습니다.)',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '서버와 통신할 수 없습니다.'
      const errorMessage: Message = {
        id: `msg-${Date.now()}-err`,
        role: 'assistant',
        content: `⚠️ 오류가 발생했습니다: ${errorMsg}\n(백엔드 서버가 실행 중인지 확인해 주세요.)`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // 키보드 엔터 처리 (Shift+Enter는 줄바꿈)
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // 텍스트 영역 자동 높이 조절
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
    setInput(e.target.value)
    const target = e.target
    target.style.height = 'auto'
    target.style.height = `${Math.min(target.scrollHeight, 140)}px`
  }

  // 새 대화 시작 (타임라인 초기화)
  const handleNewChat = async (): Promise<void> => {
    if (isLoading) return
    try {
      await fetch('/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      }).catch(() => {
        fetch('http://127.0.0.1:8000/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
        })
      })
    } catch {
      // ignore
    }

    setMessages([])
    setInput('')
    setSessionId(`session-${Math.random().toString(36).substring(2, 9)}`)
  }

  // 클립보드 복사
  const handleCopy = (content: string, id: string): void => {
    navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="gemini-app">
      {/* Top Header */}
      <header className="gemini-header">
        <div className="gemini-brand">
          <div className="gemini-sparkle-icon">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M12 2L14.85 8.15L21 11L14.85 13.85L12 20L9.15 13.85L3 11L9.15 8.15L12 2Z" />
            </svg>
          </div>
          <span className="gemini-title">Gemini</span>
        </div>

        <div className="header-right">
          <button className="btn-new-chat" onClick={handleNewChat} title="새 대화 시작">
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span>새 대화</span>
          </button>
        </div>
      </header>

      {/* Timeline Chat Stream */}
      <main className="timeline-container">
        <div className="timeline-inner">
          {messages.length === 0 ? (
            <div className="welcome-container">
              <div className="welcome-sparkle">
                <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M12 2L14.85 8.15L21 11L14.85 13.85L12 20L9.15 13.85L3 11L9.15 8.15L12 2Z" />
                </svg>
              </div>
              <h1 className="welcome-title">무엇을 도와드릴까요?</h1>
              <p className="welcome-desc">
                질문이나 요청사항을 입력하세요. 실시간 날씨, 시각 정보 및 다양한 질문에 답변해 드립니다.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="assistant-avatar">
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                      <path d="M12 2L14.85 8.15L21 11L14.85 13.85L12 20L9.15 13.85L3 11L9.15 8.15L12 2Z" />
                    </svg>
                  </div>
                )}

                {msg.role === 'user' ? (
                  <div className="user-bubble">{msg.content}</div>
                ) : (
                  <div className="assistant-content-wrapper">
                    <div className="assistant-bubble">{msg.content}</div>
                    <div className="assistant-meta">
                      <button
                        className="btn-copy"
                        onClick={() => handleCopy(msg.content, msg.id)}
                        title="답변 복사"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            <span>복사됨</span>
                          </>
                        ) : (
                          <>
                            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2">
                              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                            <span>복사</span>
                          </>
                        )}
                      </button>
                      <span className="msg-time">{msg.timestamp}</span>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="message-row assistant">
              <div className="assistant-avatar">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M12 2L14.85 8.15L21 11L14.85 13.85L12 20L9.15 13.85L3 11L9.15 8.15L12 2Z" />
                </svg>
              </div>
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Floating Bottom Input Bar */}
      <footer className="bottom-input-container">
        <div className="input-capsule">
          <textarea
            ref={textareaRef}
            className="input-textarea"
            placeholder="Gemini에게 질문하기..."
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button
            className="btn-send"
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            title="보내기 (Enter)"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </footer>
    </div>
  )
}
