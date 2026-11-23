import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px 20px',
          maxWidth: '600px',
          margin: '60px auto',
          background: '#1e1b2e',
          color: '#f87171',
          borderRadius: '16px',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          fontFamily: 'sans-serif'
        }}>
          <h2 style={{ color: '#ef4444', marginBottom: '16px' }}>⚠️ 렌더링 중 오류가 발생했습니다</h2>
          <p style={{ color: '#cbd5e1', marginBottom: '12px', fontSize: '14px' }}>
            {this.state.error?.message || '알 수 없는 오류가 발생했습니다.'}
          </p>
          <pre style={{
            background: 'rgba(0,0,0,0.4)',
            padding: '12px',
            borderRadius: '8px',
            color: '#fca5a5',
            fontSize: '12px',
            overflowX: 'auto'
          }}>
            {this.state.error?.stack}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: '#6366f1',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            새로고침
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
