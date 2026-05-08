import { useState } from 'react'
import { Avatar, Button, Input, List, Popconfirm, Space, Tag, Typography, message } from 'antd'
import { EditOutlined, DeleteOutlined, PaperClipOutlined } from '@ant-design/icons'
import { updateComment, deleteComment } from '../../../api/comments'
import type { Comment, Attachment } from '../../../types/ticket'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage } from '../../../types/common'
import AttachmentList from '../AttachmentList'

const FIVE_MINUTES = 5 * 60 * 1000

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

interface CommentItemProps {
  comment: Comment
  ticketId: number
  onUpdated: (c: Comment) => void
  onDeleted: (id: number) => void
}

function CommentItem({ comment, ticketId, onUpdated, onDeleted }: CommentItemProps) {
  const [editing, setEditing] = useState(false)
  const [editBody, setEditBody] = useState(comment.body)
  const [saving, setSaving] = useState(false)
  const currentUser = useAuthStore(s => s.user)

  const isOwner = currentUser?.id === comment.author_id
  const withinWindow = Date.now() - new Date(comment.created_at).getTime() < FIVE_MINUTES
  const isAdmin = currentUser?.role === 'admin'
  const canEdit = isOwner && withinWindow
  const canDelete = (isOwner && withinWindow) || isAdmin

  async function handleSave() {
    if (!editBody.trim()) return
    setSaving(true)
    try {
      const updated = await updateComment(ticketId, comment.id, editBody.trim())
      onUpdated(updated)
      setEditing(false)
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    try {
      await deleteComment(ticketId, comment.id)
      onDeleted(comment.id)
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  const initials = (comment.author_name ?? '?').slice(0, 2).toUpperCase()

  return (
    <List.Item
      style={{
        backgroundColor: comment.is_internal ? '#fffbe6' : undefined,
        borderRadius: 6,
        padding: '8px 12px',
        marginBottom: 8,
        border: '1px solid #f0f0f0',
      }}
    >
      <div style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
          <Space>
            <Avatar size={28} style={{ backgroundColor: '#1677ff', fontSize: 12 }}>
              {initials}
            </Avatar>
            <Typography.Text strong style={{ fontSize: 13 }}>
              {comment.author_name ?? 'Пользователь'}
            </Typography.Text>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {formatDate(comment.created_at)}
            </Typography.Text>
            {comment.is_internal && (
              <Tag color="gold" style={{ fontSize: 11 }}>Внутренний</Tag>
            )}
          </Space>
          <Space size={4}>
            {canEdit && !editing && (
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => { setEditing(true); setEditBody(comment.body) }}
              />
            )}
            {canDelete && !editing && (
              <Popconfirm
                title="Удалить комментарий?"
                onConfirm={handleDelete}
                okText="Удалить"
                cancelText="Отмена"
                okType="danger"
              >
                <Button type="text" size="small" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            )}
          </Space>
        </div>

        {editing ? (
          <div>
            <Input.TextArea
              value={editBody}
              onChange={e => setEditBody(e.target.value)}
              rows={3}
              autoFocus
            />
            <Space style={{ marginTop: 6 }}>
              <Button type="primary" size="small" loading={saving} onClick={handleSave}>
                Сохранить
              </Button>
              <Button size="small" onClick={() => setEditing(false)}>Отмена</Button>
            </Space>
          </div>
        ) : (
          <Typography.Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {comment.body}
          </Typography.Paragraph>
        )}

        {(comment.attachments?.length ?? 0) > 0 && (
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid #f0f0f0' }}>
            <Space style={{ marginBottom: 4 }}>
              <PaperClipOutlined />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>Вложения:</Typography.Text>
            </Space>
            <AttachmentList
              attachments={comment.attachments as Attachment[]}
              canDelete={isAdmin}
            />
          </div>
        )}
      </div>
    </List.Item>
  )
}

interface Props {
  comments: Comment[]
  ticketId: number
  onCommentUpdated: (c: Comment) => void
  onCommentDeleted: (id: number) => void
}

export default function CommentList({ comments, ticketId, onCommentUpdated, onCommentDeleted }: Props) {
  if (comments.length === 0) {
    return (
      <Typography.Text type="secondary" style={{ display: 'block', padding: '16px 0' }}>
        Комментариев пока нет
      </Typography.Text>
    )
  }

  return (
    <List<Comment>
      dataSource={comments}
      split={false}
      renderItem={comment => (
        <CommentItem
          key={comment.id}
          comment={comment}
          ticketId={ticketId}
          onUpdated={onCommentUpdated}
          onDeleted={onCommentDeleted}
        />
      )}
    />
  )
}
