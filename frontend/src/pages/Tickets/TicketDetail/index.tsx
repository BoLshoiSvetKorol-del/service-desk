import { useEffect, useState } from 'react'
import {
  Alert, Button, Card, Col, Descriptions, Divider, Dropdown, Form, Input, Modal, Row,
  Select, Skeleton, Space, Tabs, Tag, Typography, message,
} from 'antd'
import { ArrowLeftOutlined, DownOutlined, MergeCellsOutlined } from '@ant-design/icons'
import { useNavigate, useParams } from 'react-router-dom'
import { useTicketEventStore } from '../../../store/ticketEventStore'
import {
  getTicket, changeTicketStatus, assignTicket, changeTicketPriority,
  getTicketHistory, deleteAttachment, getTicketAttachments,
} from '../../../api/tickets'
import { getPriorities } from '../../../api/priorities'
import { getDepartments } from '../../../api/departments'
import { getUsers } from '../../../api/users'
import { getComments } from '../../../api/comments'
import type { Ticket, TicketStatus, Priority, Comment, TicketHistory } from '../../../types/ticket'
import { STATUS_TRANSITIONS, STATUS_LABELS, PRIORITY_LABELS } from '../../../types/ticket'

function getAllowedTransitions(status: TicketStatus, role: string | undefined): TicketStatus[] {
  const all = STATUS_TRANSITIONS[status] ?? []
  if (status === 'resolved' && role === 'agent') return []
  return all
}
import type { Department, User } from '../../../types/user'
import { useAuthStore } from '../../../store/authStore'
import StatusBadge from '../../../components/common/StatusBadge'
import PriorityBadge from '../../../components/common/PriorityBadge'
import SLACountdown from '../../../components/common/SLACountdown'
import CommentList from '../../../components/tickets/CommentList'
import CommentForm from '../../../components/tickets/CommentForm'
import AttachmentList from '../../../components/tickets/AttachmentList'
import ActivityTimeline from '../../../components/tickets/ActivityTimeline'
import MergeModal from '../../../components/tickets/MergeModal'
import TagSelector from '../../../components/tickets/TagSelector'
import NotesTab from '../../../components/tickets/NotesTab'
import { getErrorMessage } from '../../../types/common'

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const currentUser = useAuthStore(s => s.user)
  const canEdit = currentUser?.role === 'admin' || currentUser?.role === 'agent' || currentUser?.role === 'department_head'
  const canAssign = currentUser?.role === 'admin' || currentUser?.role === 'department_head'

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [history, setHistory] = useState<TicketHistory[]>([])
  const [attachments, setAttachments] = useState<import('../../../types/ticket').Attachment[]>([])
  const [loading, setLoading] = useState(true)
  const [priorities, setPriorities] = useState<Priority[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [agents, setAgents] = useState<User[]>([])
  const [actionLoading, setActionLoading] = useState(false)
  const [showMergeModal, setShowMergeModal] = useState(false)
  const [cancelModal, setCancelModal] = useState(false)
  const [cancelReason, setCancelReason] = useState('')
  const lastTicketEvent = useTicketEventStore(s => s.lastEvent)

  // Real-time: react to SSE events for this ticket
  useEffect(() => {
    if (!lastTicketEvent || !ticket) return
    if (lastTicketEvent.ticketId !== ticket.id) return

    if (lastTicketEvent.type === 'new_comment' && lastTicketEvent.comment) {
      const incoming = lastTicketEvent.comment
      if (incoming.author_id === currentUser?.id) return
      setComments(prev => {
        if (prev.some(c => c.id === incoming.id)) return prev
        return [...prev, incoming]
      })
    } else if (lastTicketEvent.type === 'new_attachment') {
      getTicketAttachments(ticket.id).then(setAttachments).catch(() => {})
    } else if (
      lastTicketEvent.type === 'status_changed' ||
      lastTicketEvent.type === 'assigned' ||
      lastTicketEvent.type === 'priority_changed'
    ) {
      getTicket(ticket.id).then(setTicket).catch(() => {})
      getTicketHistory(ticket.id).then(setHistory).catch(() => {})
    }
  }, [lastTicketEvent]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      getTicket(Number(id)),
      getPriorities(),
      getDepartments(),
      getUsers({ page_size: 100 }),
      getComments(Number(id)),
      getTicketHistory(Number(id)),
      getTicketAttachments(Number(id)),
    ])
      .then(([t, ps, ds, us, cs, hist, atts]) => {
        setTicket(t)
        setPriorities(ps)
        setDepartments(ds)
        setAgents(us.items.filter(u => u.role !== 'user'))
        setComments(cs)
        setHistory(hist)
        setAttachments(atts)
      })
      .catch((e) => message.error('Ошибка загрузки заявки: ' + (e?.response?.data?.detail ?? e?.message ?? 'неизвестная ошибка')))
      .finally(() => setLoading(false))
  }, [id])

  async function handleStatusChange(newStatus: TicketStatus) {
    if (!ticket) return
    // Cancellation requires a reason
    if (newStatus === 'cancelled') {
      setCancelModal(true)
      return
    }
    setActionLoading(true)
    try {
      const updated = await changeTicketStatus(ticket.id, { status: newStatus })
      setTicket(updated)
      message.success(`Статус изменён: ${STATUS_LABELS[newStatus]}`)
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  async function handleConfirmCancel() {
    if (!ticket || !cancelReason.trim()) return
    setActionLoading(true)
    try {
      const updated = await changeTicketStatus(ticket.id, { status: 'cancelled', comment: cancelReason.trim() })
      setTicket(updated)
      message.success('Заявка отменена')
      setCancelModal(false)
      setCancelReason('')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  async function handleAssigneeChange(assigneeId: number | undefined) {
    if (!ticket) return
    setActionLoading(true)
    try {
      const updated = await assignTicket(ticket.id, { assignee_id: assigneeId ?? null })
      setTicket(updated)
      message.success('Исполнитель обновлён')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  async function handleDepartmentChange(deptId: number | undefined) {
    if (!ticket) return
    setActionLoading(true)
    try {
      const updated = await assignTicket(ticket.id, { department_id: deptId ?? null, assignee_id: null })
      setTicket(updated)
      message.success('Отдел обновлён')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  async function handlePriorityChange(priorityId: number) {
    if (!ticket) return
    setActionLoading(true)
    try {
      const updated = await changeTicketPriority(ticket.id, priorityId)
      setTicket(updated)
      message.success('Приоритет обновлён')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setActionLoading(false)
    }
  }

  async function handleDeleteAttachment(attachmentId: number) {
    try {
      await deleteAttachment(attachmentId)
      setAttachments(prev => prev.filter(a => a.id !== attachmentId))
      message.success('Файл удалён')
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  // Can this user write comments?
  const canComment = (() => {
    if (!ticket || !currentUser) return false
    if (currentUser.role === 'admin') return true
    if (currentUser.role === 'department_head') return true
    if (currentUser.role === 'agent') {
      return ticket.assignee_id === currentUser.id || ticket.creator_id === currentUser.id
    }
    return true // user role — portal handles it separately
  })()

  if (loading) return <Skeleton active paragraph={{ rows: 12 }} />
  if (!ticket) return <Typography.Text type="danger">Заявка не найдена</Typography.Text>

  const nextStatuses = getAllowedTransitions(ticket.status, currentUser?.role)
  const canMerge = canEdit && !['merged', 'resolved', 'cancelled'].includes(ticket.status)

  // For dept_head: only show agents from their own department
  const assignableAgents = currentUser?.role === 'department_head'
    ? agents.filter(u => u.department_id === currentUser.department_id)
    : ticket.department_id
      ? agents.filter(u => u.department_id === ticket.department_id)
      : agents

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        style={{ paddingLeft: 0, marginBottom: 8 }}
        onClick={() => navigate('/tickets')}
      >
        К списку заявок
      </Button>

      {ticket.status === 'merged' && ticket.merged_into_id && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message={
            <span>
              Эта заявка объединена с&nbsp;
              <Button
                type="link"
                style={{ padding: 0, height: 'auto' }}
                onClick={() => navigate(`/tickets/${ticket.merged_into_id}`)}
              >
                #{ticket.merged_into_id}
              </Button>
            </span>
          }
        />
      )}

      {showMergeModal && (
        <MergeModal
          ticketId={ticket.id}
          onMerged={() => {
            setShowMergeModal(false)
            getTicket(ticket.id).then(setTicket).catch(() => {})
          }}
          onClose={() => setShowMergeModal(false)}
        />
      )}

      {/* Cancellation reason modal */}
      <Modal
        open={cancelModal}
        title="Причина отмены"
        onOk={handleConfirmCancel}
        onCancel={() => { setCancelModal(false); setCancelReason('') }}
        okText="Отменить заявку"
        okButtonProps={{ danger: true, disabled: !cancelReason.trim(), loading: actionLoading }}
        cancelText="Назад"
      >
        <Form layout="vertical" style={{ marginTop: 8 }}>
          <Form.Item
            label="Укажите причину отмены"
            required
            help="Это поле обязательно для заполнения"
          >
            <Input.TextArea
              rows={4}
              placeholder="Опишите причину отмены заявки..."
              value={cancelReason}
              onChange={e => setCancelReason(e.target.value)}
              autoFocus
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Header */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="top" gutter={[16, 8]}>
          <Col flex="auto">
            <Space direction="vertical" size={4}>
              <Typography.Text type="secondary" style={{ fontSize: 13 }}>{ticket.number}</Typography.Text>
              <Typography.Title level={4} style={{ margin: 0 }}>{ticket.title}</Typography.Title>
            </Space>
          </Col>
          <Col>
            <Space>
              <SLACountdown
                slaDeadline={ticket.sla_deadline}
                slaViolated={ticket.sla_violated}
                createdAt={ticket.created_at}
              />
              {canMerge && (
                <Button
                  icon={<MergeCellsOutlined />}
                  onClick={() => setShowMergeModal(true)}
                  disabled={actionLoading}
                >
                  Объединить
                </Button>
              )}
              {nextStatuses.length > 0 ? (
                <Dropdown
                  menu={{
                    items: nextStatuses.map(s => ({
                      key: s,
                      label: STATUS_LABELS[s],
                      onClick: () => handleStatusChange(s),
                    })),
                  }}
                  disabled={actionLoading}
                >
                  <Button loading={actionLoading}>
                    <Space>
                      <StatusBadge status={ticket.status} />
                      <DownOutlined style={{ fontSize: 11 }} />
                    </Space>
                  </Button>
                </Dropdown>
              ) : (
                <StatusBadge status={ticket.status} />
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* Main content */}
        <Col xs={24} md={16}>
          <Card title="Описание" style={{ marginBottom: 16 }}>
            <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
              {ticket.description}
            </Typography.Paragraph>
          </Card>

          <Tabs
            defaultActiveKey="comments"
            items={[
              {
                key: 'comments',
                label: `Комментарии (${comments.length})`,
                children: (
                  <div>
                    <CommentList
                      comments={comments}
                      ticketId={ticket.id}
                      onCommentUpdated={updated =>
                        setComments(prev => prev.map(c => c.id === updated.id ? updated : c))
                      }
                      onCommentDeleted={cid =>
                        setComments(prev => prev.filter(c => c.id !== cid))
                      }
                    />
                    {canComment ? (
                      <CommentForm
                        ticketId={ticket.id}
                        onCommentCreated={c => setComments(prev => [...prev, c])}
                      />
                    ) : (
                      <div style={{ padding: '12px 0', color: '#999', fontSize: 13 }}>
                        Писать комментарии может только исполнитель или руководитель отдела.
                      </div>
                    )}
                  </div>
                ),
              },
              {
                key: 'attachments',
                label: `Вложения (${attachments.length})`,
                children: (
                  <AttachmentList
                    attachments={attachments}
                    canDelete={canEdit}
                    onDelete={handleDeleteAttachment}
                  />
                ),
              },
              {
                key: 'history',
                label: 'История',
                children: <ActivityTimeline history={history} />,
              },
              ...(canEdit ? [{
                key: 'notes',
                label: 'Заметки',
                children: <NotesTab ticketId={ticket.id} />,
              }] : []),
            ]}
          />
        </Col>

        {/* Sidebar meta */}
        <Col xs={24} md={8}>
          <Card>
            <Descriptions column={1} size="small" colon={false} labelStyle={{ color: '#888', width: 120 }}>
              <Descriptions.Item label="Заявитель">
                {ticket.creator_name}
              </Descriptions.Item>

              <Descriptions.Item label="Приоритет">
                {canEdit ? (
                  <Select
                    size="small"
                    value={ticket.priority.id}
                    onChange={handlePriorityChange}
                    loading={actionLoading}
                    style={{ width: '100%' }}
                    options={priorities.map(p => ({ value: p.id, label: PRIORITY_LABELS[p.name] }))}
                  />
                ) : (
                  <PriorityBadge name={ticket.priority.name} />
                )}
              </Descriptions.Item>

              <Descriptions.Item label="Отдел">
                {canAssign ? (
                  <Select
                    size="small"
                    value={ticket.department_id ?? undefined}
                    onChange={handleDepartmentChange}
                    loading={actionLoading}
                    allowClear
                    style={{ width: '100%' }}
                    options={departments.map(d => ({ value: d.id, label: d.name }))}
                    placeholder="Не указан"
                  />
                ) : (
                  <span>{ticket.department_name ?? '—'}</span>
                )}
              </Descriptions.Item>

              <Descriptions.Item label="Исполнитель">
                {canAssign ? (
                  <Select
                    size="small"
                    value={ticket.assignee_id ?? undefined}
                    onChange={handleAssigneeChange}
                    loading={actionLoading}
                    allowClear
                    style={{ width: '100%' }}
                    options={assignableAgents.map(u => ({ value: u.id, label: u.full_name || u.username }))}
                    placeholder="Не назначен"
                  />
                ) : (
                  <span>{ticket.assignee_name ?? '—'}</span>
                )}
              </Descriptions.Item>

              {ticket.ticket_type_name && (
                <Descriptions.Item label="Тип">
                  {ticket.ticket_type_name}
                </Descriptions.Item>
              )}

              <Descriptions.Item label="Создана">
                {formatDate(ticket.created_at)}
              </Descriptions.Item>

              <Descriptions.Item label="Обновлена">
                {formatDate(ticket.updated_at)}
              </Descriptions.Item>

              {ticket.sla_deadline && (
                <Descriptions.Item label="Дедлайн SLA">
                  <Space direction="vertical" size={2}>
                    <span>{formatDate(ticket.sla_deadline)}</span>
                    {ticket.sla_violated && <Tag color="red">Нарушен</Tag>}
                  </Space>
                </Descriptions.Item>
              )}

              {ticket.closed_at && (
                <Descriptions.Item label="Закрыта">
                  {formatDate(ticket.closed_at)}
                </Descriptions.Item>
              )}

              <Descriptions.Item label="Теги">
                {canEdit ? (
                  <TagSelector
                    ticketId={ticket.id}
                    currentTags={ticket.tags}
                    onChange={tags => setTicket(prev => prev ? { ...prev, tags } : prev)}
                    disabled={actionLoading}
                  />
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {ticket.tags.length === 0
                      ? <span style={{ color: '#bbb' }}>—</span>
                      : ticket.tags.map(tag => (
                          <Tag key={tag.id} color={tag.color_hex}>{tag.name}</Tag>
                        ))
                    }
                  </div>
                )}
              </Descriptions.Item>
            </Descriptions>

            {ticket.sla_paused_at && (
              <>
                <Divider style={{ margin: '8px 0' }} />
                <Tag color="gold" style={{ width: '100%', textAlign: 'center' }}>
                  SLA на паузе
                </Tag>
              </>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
