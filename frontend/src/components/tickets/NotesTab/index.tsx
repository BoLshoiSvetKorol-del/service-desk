import { useEffect, useState } from 'react'
import { Button, Empty, Input, Space, Typography, Popconfirm, message } from 'antd'
import { EditOutlined, DeleteOutlined, PlusOutlined, SaveOutlined, CloseOutlined } from '@ant-design/icons'
import { getNotes, createNote, updateNote, deleteNote } from '../../../api/notes'
import type { TicketNote } from '../../../api/notes'

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

interface Props {
  ticketId: number
}

export default function NotesTab({ ticketId }: Props) {
  const [notes, setNotes] = useState<TicketNote[]>([])
  const [loading, setLoading] = useState(true)
  const [newText, setNewText] = useState('')
  const [adding, setAdding] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')

  useEffect(() => {
    load()
  }, [ticketId])

  async function load() {
    setLoading(true)
    try {
      setNotes(await getNotes(ticketId))
    } catch {
      // 403 for users — handled by parent not rendering this tab
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate() {
    if (!newText.trim()) return
    setAdding(true)
    try {
      const note = await createNote(ticketId, newText.trim())
      setNotes(prev => [...prev, note])
      setNewText('')
      setShowForm(false)
    } catch {
      message.error('Ошибка создания заметки')
    } finally {
      setAdding(false)
    }
  }

  async function handleUpdate(note: TicketNote) {
    try {
      const updated = await updateNote(ticketId, note.id, editText.trim())
      setNotes(prev => prev.map(n => n.id === updated.id ? updated : n))
      setEditingId(null)
    } catch {
      message.error('Ошибка обновления заметки')
    }
  }

  async function handleDelete(noteId: number) {
    try {
      await deleteNote(ticketId, noteId)
      setNotes(prev => prev.filter(n => n.id !== noteId))
    } catch {
      message.error('Ошибка удаления заметки')
    }
  }

  return (
    <div style={{ padding: '8px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <Typography.Text type="secondary" style={{ fontSize: 13 }}>
          Заметки видны только вам
        </Typography.Text>
        {!showForm && (
          <Button size="small" icon={<PlusOutlined />} onClick={() => setShowForm(true)}>
            Добавить заметку
          </Button>
        )}
      </div>

      {showForm && (
        <div style={{ marginBottom: 16, padding: 12, background: '#fffbe6', borderRadius: 6, border: '1px solid #ffe58f' }}>
          <Input.TextArea
            autoFocus
            rows={3}
            value={newText}
            onChange={e => setNewText(e.target.value)}
            placeholder="Введите заметку..."
            style={{ marginBottom: 8 }}
          />
          <Space>
            <Button type="primary" size="small" icon={<SaveOutlined />} loading={adding} onClick={handleCreate}>
              Сохранить
            </Button>
            <Button size="small" icon={<CloseOutlined />} onClick={() => { setShowForm(false); setNewText('') }}>
              Отмена
            </Button>
          </Space>
        </div>
      )}

      {!loading && notes.length === 0 && !showForm && (
        <Empty description="Нет заметок" style={{ padding: '24px 0' }} />
      )}

      {notes.map(note => (
        <div
          key={note.id}
          style={{
            marginBottom: 12, padding: 12,
            background: '#fffbe6', borderRadius: 6,
            border: '1px solid #ffe58f',
          }}
        >
          {editingId === note.id ? (
            <>
              <Input.TextArea
                autoFocus
                rows={3}
                value={editText}
                onChange={e => setEditText(e.target.value)}
                style={{ marginBottom: 8 }}
              />
              <Space>
                <Button type="primary" size="small" icon={<SaveOutlined />} onClick={() => handleUpdate(note)}>
                  Сохранить
                </Button>
                <Button size="small" icon={<CloseOutlined />} onClick={() => setEditingId(null)}>
                  Отмена
                </Button>
              </Space>
            </>
          ) : (
            <>
              <Typography.Text style={{ whiteSpace: 'pre-wrap', display: 'block', marginBottom: 8 }}>
                {note.body}
              </Typography.Text>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {formatDate(note.created_at)}
                  {note.updated_at !== note.created_at && ' (изм.)'}
                </Typography.Text>
                <Space size={4}>
                  <Button
                    size="small" type="text" icon={<EditOutlined />}
                    onClick={() => { setEditingId(note.id); setEditText(note.body) }}
                  />
                  <Popconfirm
                    title="Удалить заметку?"
                    onConfirm={() => handleDelete(note.id)}
                    okText="Да" cancelText="Нет"
                  >
                    <Button size="small" type="text" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  )
}
