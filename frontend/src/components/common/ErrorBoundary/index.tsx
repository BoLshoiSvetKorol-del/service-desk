import { Component, ErrorInfo, ReactNode } from 'react'
import { Button, Result } from 'antd'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Что-то пошло не так"
          subTitle={this.state.error?.message ?? 'Неизвестная ошибка'}
          extra={
            <Button type="primary" onClick={() => {
              this.setState({ hasError: false, error: null })
              window.location.href = '/'
            }}>
              На главную
            </Button>
          }
        />
      )
    }
    return this.props.children
  }
}
