import { useState } from 'react'
import { Button, Input, Space, Switch, Upload, Typography, message } from 'antd'
import { InboxOutlined, LockOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { createComment, uploadCommentAttachment } from '../../../api/comments'
import type { Comment } from '../../../types/ticket'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage } from '../../../types/common'

const { TextArea } = Input
const { Dragger } = Upload

interface Props {
  ticketId: number
  onCommentCreated: (comment: Comment) => void
}

export default function CommentForm({ ticketId, onCommentCreated }: Props) {
  const [body, setBody] = useState('')
  const [isInternal, setIsInternal] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [loading, setLoading] = useState(false)
  const currentUser = useAuthStore(s => s.user)
  const canMarkInternal = currentUser?.role === 'agent' || currentUser?.role === 'admin'

  async function handleSubmit() {
    if (!body.trim()) {
      message.warning('Введите текст комментария')
      return
    }

    setLoading(true)
    try {
      const comment = await createComment(ticketId, {
        body: body.trim(),
        is_internal: canMarkInternal ? isInternal : false,
      })

      for (const f of fileList) {
        if (f.originFileObj) {
          try {
            await uploadCommentAttachment(ticketId, comment.id, f.originFileObj)
          } catch {
            message.warning(`Не удалось загрузить файл: ${f.name}`)
          }
        }
      }

      onCommentCreated(comment)
      setBody('')
      setIsInternal(false)
      setFileList([])
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ marginTop: 16, padding: '12px 16px', border: '1px solid #f0f0f0', borderRadius: 6 }}>
      <TextArea
        rows={3}
        placeholder="Напишите комментарий..."
        value={body}
        onChange={e => setBody(e.target.value)}
        style={{ marginBottom: 8 }}
      />

      <Dragger
        multiple
        beforeUpload={() => false}
        fileList={fileList}
        onChange={({ fileList: fl }) => setFileList(fl)}
        style={{ marginBottom: 8 }}
      >
        <p style={{ margin: '4px 0', color: '#999', fontSize: 13 }}>
          <InboxOutlined style={{ marginRight: 6 }} />
          Перетащите файлы или нажмите для выбора (макс. 10 МБ)
        </p>
      </Dragger>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {canMarkInternal ? (
          <Space>
            <LockOutlined style={{ color: isInternal ? '#d48806' : '#ccc' }} />
            <Typography.Text style={{ fontSize: 13 }}>Внутренний комментарий</Typography.Text>
            <Switch
              size="small"
              checked={isInternal}
              onChange={setIsInternal}
            />
          </Space>
        ) : (
          <span />
        )}

        <Button
          type="primary"
          loading={loading}
          onClick={handleSubmit}
          disabled={!body.trim()}
        >
          Отправить
        </Button>
      </div>
    </div>
  )
}
