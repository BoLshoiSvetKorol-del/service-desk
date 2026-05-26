import { useState, useEffect } from 'react'
import { Rate, Input, Button, Space, Typography, Card, Alert } from 'antd'
import { SmileOutlined } from '@ant-design/icons'
import { submitRating, getRating, type RatingData } from '../../../api/ratings'
import { getErrorMessage } from '../../../types/common'

const RATING_LABELS = ['Очень плохо', 'Плохо', 'Нормально', 'Хорошо', 'Отлично']

interface Props {
  ticketId: number
  readOnly?: boolean
}

export default function SatisfactionRating({ ticketId, readOnly = false }: Props) {
  const [existing, setExisting] = useState<RatingData | null>(null)
  const [value, setValue] = useState(0)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getRating(ticketId)
      .then(r => {
        if (r) {
          setExisting(r)
          setValue(r.rating)
          setComment(r.comment ?? '')
          setSubmitted(true)
        }
      })
      .catch(() => {})
  }, [ticketId])

  async function handleSubmit() {
    if (!value) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await submitRating(ticketId, value, comment || undefined)
      setExisting(result)
      setSubmitted(true)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setSubmitting(false)
    }
  }

  if (readOnly) {
    if (!existing) return null
    return (
      <div>
        <Rate disabled value={existing.rating} />
        <Typography.Text type="secondary" style={{ marginLeft: 8, fontSize: 13 }}>
          {RATING_LABELS[existing.rating - 1]}
        </Typography.Text>
        {existing.comment && (
          <Typography.Paragraph
            style={{ marginTop: 6, fontSize: 13, color: '#555', fontStyle: 'italic', marginBottom: 0 }}
          >
            «{existing.comment}»
          </Typography.Paragraph>
        )}
      </div>
    )
  }

  if (submitted && existing) {
    return (
      <Alert
        type="success"
        showIcon
        icon={<SmileOutlined />}
        message={
          <Space direction="vertical" size={2}>
            <span>Спасибо за оценку!</span>
            <Rate disabled value={existing.rating} style={{ fontSize: 16 }} />
            {existing.comment && (
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                «{existing.comment}»
              </Typography.Text>
            )}
          </Space>
        }
      />
    )
  }

  return (
    <Card
      style={{ borderColor: '#d9f7be', background: '#f6ffed' }}
      bodyStyle={{ padding: '16px 20px' }}
    >
      <Typography.Title level={5} style={{ margin: '0 0 12px 0', color: '#389e0d' }}>
        <SmileOutlined style={{ marginRight: 8 }} />
        Оцените качество обслуживания
      </Typography.Title>

      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 12 }} />}

      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        <div>
          <Rate
            value={value}
            onChange={setValue}
            style={{ fontSize: 28 }}
          />
          {value > 0 && (
            <Typography.Text style={{ marginLeft: 10, color: '#595959' }}>
              {RATING_LABELS[value - 1]}
            </Typography.Text>
          )}
        </div>

        <Input.TextArea
          rows={2}
          placeholder="Оставьте комментарий (необязательно)..."
          value={comment}
          onChange={e => setComment(e.target.value)}
          maxLength={500}
        />

        <Button
          type="primary"
          onClick={handleSubmit}
          loading={submitting}
          disabled={!value}
        >
          Отправить оценку
        </Button>
      </Space>
    </Card>
  )
}
