import { useEffect, useState } from 'react'
import {
  Alert, Avatar, Button, Card, Col, Descriptions, Form, Input,
  List, Modal, Row, Skeleton, Space, Tag, Typography, message,
} from 'antd'
import {
  ArrowLeftOutlined, SendOutlined, UserOutlined,
  ClockCircleOutlined, CheckCircleOutlined,
} from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { getTicket, changeTicketStatus, getTicketAttachments } from '../../../api/tickets'
import { getComments, createComment } from '../../../api/comments'
import type { Ticket, Comment, Attachment } from '../../../types/ticket'
import { STATUS_LABELS, PRIORITY_LABELS } from '../../../types/ticket'
import AttachmentList from '../../../components/tickets/AttachmentList'
import { useAuthStore } from '../../../store/authStore'
import { useTicketEventStore } from '../../../store/ticketEventStore'
import { getErrorMessage } from '../../../types/common'

const STATUS_COLOR: Record<string, string> = {
  new: 'blue', in_progress: 'cyan', waiting_info: 'gold',
  resolved: 'green', cancelled: 'default', merged: 'purple',
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function PortalTicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const currentUser = useAuthStore(s => s.user)
  const lastTicketEvent = useTicketEventStore(s => s.lastEvent)

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [loading, setLoading] = useState(true)
  const [commentBody, setCommentBody] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [cancelModal, setCancelModal] = useState(false)
  const [cancelReason, setCancelReason] = useState('')

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      getTicket(Number(id)),
      getComments(Number(id)),
      getTicketAttachments(Number(id)),
    ])
      .then(([t, cs, atts]) => { setTicket(t); setComments(cs); setAttachments(atts) })
      .catch(() => message.error('Ошибка загрузки инцидента'))
      .finally(() => setLoading(false))
  }, [id])

  // Real-time: SSE new_comment / attachment / status
  useEffect(() => {
    if (!lastTicketEvent || !ticket) return
    if (lastTicketEvent.ticketId !== ticket.id) return
    if (lastTicketEvent.type === 'new_comment' && lastTicketEvent.comment) {
      const incoming = lastTicketEvent.comment
      if (incoming.author_id === currentUser?.id) return
      setComments(prev => prev.some(c => c.id === incoming.id) ? prev : [...prev, incoming])
    } else if (lastTicketEvent.type === 'new_attachment') {
      getTicketAttachments(ticket.id).then(setAttachments).catch(() => {})
    } else if (lastTicketEvent.type === 'status_changed') {
      getTicket(ticket.id).then(setTicket).catch(() => {})
    }
  }, [lastTicketEvent]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSendComment() {
    if (!ticket || !commentBody.trim()) return
    setSubmitting(true)
    try {
      const c = await createComment(ticket.id, { body: commentBody.trim(), is_internal: false })
      setComments(prev => [...prev, c])
      setCommentBody('')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCancelConfirm() {
    if (!ticket || !cancelReason.trim()) return
    setCancelling(true)
    try {
      const updated = await changeTicketStatus(ticket.id, { status: 'cancelled', comment: cancelReason.trim() })
      setTicket(updated)
      message.success('Инцидент отменён')
      setCancelModal(false)
      setCancelReason('')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setCancelling(false)
    }
  }

  if (loading) return <Skeleton active paragraph={{ rows: 10 }} />
  if (!ticket) return <Typography.Text type="danger">Инцидент не найден</Typography.Text>

  return (
    <div>
      <Modal
        open={cancelModal}
        title="Причина отмены"
        onOk={handleCancelConfirm}
        onCancel={() => { setCancelModal(false); setCancelReason('') }}
        okText="Отменить инцидент"
        okButtonProps={{ danger: true, disabled: !cancelReason.trim(), loading: cancelling }}
        cancelText="Назад"
      >
        <Form layout="vertical" style={{ marginTop: 8 }}>
          <Form.Item label="Укажите причину отмены" required help="Обязательное поле">
            <Input.TextArea
              rows={4}
              placeholder="Опишите причину отмены..."
              value={cancelReason}
              onChange={e => setCancelReason(e.target.value)}
              autoFocus
            />
          </Form.Item>
        </Form>
      </Modal>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        style={{ paddingLeft: 0, marginBottom: 12 }}
        onClick={() => navigate('/portal/tickets')}
      >
        К списку инцидентов
      </Button>

      {ticket.status === 'merged' && ticket.merged_into_id && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message={
            <span>
              Этот инцидент объединён.{' '}
              <Button type="link" style={{ padding: 0 }}
                onClick={() => navigate(`/portal/tickets/${ticket.merged_into_id}`)}>
                Открыть основной инцидент
              </Button>
            </span>
          }
        />
      )}

      {/* Header card */}
      <Card style={{ marginBottom: 12 }}>
        <Row justify="space-between" align="top" gutter={[16, 8]}>
          <Col flex="auto">
            <Space direction="vertical" size={4}>
              <Typography.Text type="secondary">{ticket.number}</Typography.Text>
              <Typography.Title level={4} style={{ margin: 0 }}>{ticket.title}</Typography.Title>
            </Space>
          </Col>
          <Col>
            <Tag color={STATUS_COLOR[ticket.status] ?? 'default'} style={{ fontSize: 14, padding: '4px 10px' }}>
              {STATUS_LABELS[ticket.status] ?? ticket.status}
            </Tag>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col xs={24} md={16}>
          {/* Description */}
          <Card title="Описание обращения" style={{ marginBottom: 12 }}>
            <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
              {ticket.description || '—'}
            </Typography.Paragraph>
          </Card>

          {/* Attachments */}
          {attachments.length > 0 && (
            <Card title={`Вложения (${attachments.length})`} style={{ marginBottom: 12 }}>
              <AttachmentList attachments={attachments} canDelete={false} />
            </Card>
          )}

          {/* Comments as chat */}
          <Card
            title={`Переписка (${comments.length})`}
            style={{ marginBottom: 12 }}
            bodyStyle={{ padding: 0 }}
          >
            <List
              dataSource={comments}
              locale={{ emptyText: <div style={{ padding: 24, textAlign: 'center', color: '#bbb' }}>Нет сообщений</div> }}
              renderItem={c => {
                const isMe = c.author_id === currentUser?.id
                const isAgent = c.author_role === 'agent' || c.author_role === 'admin'
                return (
                  <List.Item
                    style={{
                      padding: '12px 16px',
                      background: isMe ? '#f0f7ff' : isAgent ? '#fafafa' : '#fff',
                      borderBottom: '1px solid #f0f0f0',
                      justifyContent: isMe ? 'flex-end' : 'flex-start',
                      display: 'flex',
                    }}
                  >
                    <div style={{ maxWidth: '80%' }}>
                      <Space size={8} style={{ marginBottom: 4 }}>
                        <Avatar
                          size={24}
                          style={{ backgroundColor: isAgent ? '#52c41a' : '#1677ff', fontSize: 11 }}
                          icon={<UserOutlined />}
                        >
                          {(c.author_name ?? '?').slice(0, 2).toUpperCase()}
                        </Avatar>
                        <Typography.Text strong style={{ fontSize: 13 }}>
                          {isMe ? 'Вы' : (c.author_name ?? (isAgent ? 'Поддержка' : 'Пользователь'))}
                        </Typography.Text>
                        {isAgent && !isMe && (
                          <Tag color="green" style={{ fontSize: 11, padding: '0 4px', lineHeight: '18px' }}>
                            Поддержка
                          </Tag>
                        )}
                        <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                          {formatDate(c.created_at)}
                        </Typography.Text>
                      </Space>
                      <div
                        style={{
                          background: '#fff',
                          border: '1px solid #e8e8e8',
                          borderRadius: 8,
                          padding: '8px 12px',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                        }}
                      >
                        {c.body}
                      </div>
                    </div>
                  </List.Item>
                )
              }}
            />

            {/* Input area — only for active tickets */}
            {!['resolved', 'cancelled', 'merged'].includes(ticket.status) && (
              <div style={{ padding: '12px 16px', borderTop: '1px solid #f0f0f0' }}>
                <Form.Item style={{ marginBottom: 8 }}>
                  <Input.TextArea
                    placeholder="Напишите сообщение..."
                    rows={3}
                    value={commentBody}
                    onChange={e => setCommentBody(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault()
                        handleSendComment()
                      }
                    }}
                  />
                </Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    loading={submitting}
                    disabled={!commentBody.trim()}
                    onClick={handleSendComment}
                  >
                    Отправить
                  </Button>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    Ctrl+Enter
                  </Typography.Text>
                </Space>
              </div>
            )}

            {ticket.status === 'resolved' && (
              <div style={{ padding: '12px 16px', textAlign: 'center', color: '#52c41a', borderTop: '1px solid #f0f0f0' }}>
                <CheckCircleOutlined /> Инцидент выполнен
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card>
            <Descriptions column={1} size="small" colon={false} labelStyle={{ color: '#888' }}>
              <Descriptions.Item label="Статус">
                <Tag color={STATUS_COLOR[ticket.status]}>{STATUS_LABELS[ticket.status]}</Tag>
              </Descriptions.Item>
              {ticket.ticket_type_name && (
                <Descriptions.Item label="Тема">{ticket.ticket_type_name}</Descriptions.Item>
              )}
              {ticket.department_name && (
                <Descriptions.Item label="Отдел">{ticket.department_name}</Descriptions.Item>
              )}
              {ticket.assignee_name && (
                <Descriptions.Item label="Исполнитель">{ticket.assignee_name}</Descriptions.Item>
              )}
              <Descriptions.Item label="Создана">{formatDate(ticket.created_at)}</Descriptions.Item>
              {ticket.closed_at && (
                <Descriptions.Item label="Закрыта">{formatDate(ticket.closed_at)}</Descriptions.Item>
              )}
            </Descriptions>

            {ticket.status === 'new' && (
              <Button
                danger
                block
                loading={cancelling}
                style={{ marginTop: 16 }}
                icon={<ClockCircleOutlined />}
                onClick={() => setCancelModal(true)}
              >
                Отменить инцидент
              </Button>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
