import { Button, Image, List, Popconfirm, Space, Typography } from 'antd'
import {
  DownloadOutlined, DeleteOutlined,
  FileOutlined, FileImageOutlined, FilePdfOutlined,
  FileTextOutlined, FileZipOutlined, FileExcelOutlined, FileWordOutlined,
} from '@ant-design/icons'
import type { Attachment } from '../../../types/ticket'
import { downloadAttachment } from '../../../api/attachments'
import { message } from 'antd'

function getFileIcon(mimetype: string) {
  if (mimetype.startsWith('image/')) return <FileImageOutlined style={{ color: '#52c41a', fontSize: 20 }} />
  if (mimetype === 'application/pdf') return <FilePdfOutlined style={{ color: '#f5222d', fontSize: 20 }} />
  if (mimetype.startsWith('text/')) return <FileTextOutlined style={{ color: '#1677ff', fontSize: 20 }} />
  if (mimetype.includes('zip') || mimetype.includes('rar') || mimetype.includes('7z') || mimetype.includes('tar'))
    return <FileZipOutlined style={{ color: '#fa8c16', fontSize: 20 }} />
  if (mimetype.includes('excel') || mimetype.includes('spreadsheet'))
    return <FileExcelOutlined style={{ color: '#52c41a', fontSize: 20 }} />
  if (mimetype.includes('word') || mimetype.includes('document'))
    return <FileWordOutlined style={{ color: '#1677ff', fontSize: 20 }} />
  return <FileOutlined style={{ fontSize: 20 }} />
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} КБ`
  return `${(bytes / 1_048_576).toFixed(1)} МБ`
}

interface Props {
  attachments: Attachment[]
  canDelete?: boolean
  onDelete?: (id: number) => void
}

export default function AttachmentList({ attachments, canDelete = false, onDelete }: Props) {
  if (attachments.length === 0) {
    return <Typography.Text type="secondary">Нет вложений</Typography.Text>
  }

  async function handleDownload(a: Attachment) {
    try {
      await downloadAttachment(a.id, a.original_filename)
    } catch {
      message.error('Ошибка скачивания файла')
    }
  }

  const images = attachments.filter(a => a.mimetype.startsWith('image/') && a.url)
  const others = attachments.filter(a => !a.mimetype.startsWith('image/') || !a.url)

  return (
    <div>
      {images.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <Image.PreviewGroup>
            <Space wrap size={8}>
              {images.map(a => (
                <div key={a.id} style={{ position: 'relative' }}>
                  <Image
                    src={a.url}
                    width={80}
                    height={80}
                    style={{ objectFit: 'cover', borderRadius: 4, border: '1px solid #f0f0f0' }}
                    fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                  />
                  <div style={{ fontSize: 11, color: '#888', maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {a.original_filename}
                  </div>
                  {canDelete && onDelete && (
                    <Popconfirm
                      title="Удалить файл?"
                      onConfirm={() => onDelete(a.id)}
                      okText="Удалить"
                      cancelText="Отмена"
                      okType="danger"
                    >
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        style={{ position: 'absolute', top: 0, right: 0, background: 'rgba(255,255,255,0.8)', padding: '0 2px' }}
                      />
                    </Popconfirm>
                  )}
                </div>
              ))}
            </Space>
          </Image.PreviewGroup>
        </div>
      )}

      {others.length > 0 && (
        <List<Attachment>
          dataSource={others}
          renderItem={a => (
            <List.Item
              actions={[
                <Button
                  key="dl"
                  type="link"
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownload(a)}
                >
                  Скачать
                </Button>,
                ...(canDelete && onDelete
                  ? [
                      <Popconfirm
                        key="del"
                        title="Удалить файл?"
                        onConfirm={() => onDelete(a.id)}
                        okText="Удалить"
                        cancelText="Отмена"
                        okType="danger"
                      >
                        <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                          Удалить
                        </Button>
                      </Popconfirm>,
                    ]
                  : []),
              ]}
            >
              <List.Item.Meta
                avatar={getFileIcon(a.mimetype)}
                title={
                  <Space>
                    <span>{a.original_filename}</span>
                  </Space>
                }
                description={
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {formatSize(a.size_bytes)}
                    {a.uploader_name ? ` · ${a.uploader_name}` : ''}
                  </Typography.Text>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  )
}
