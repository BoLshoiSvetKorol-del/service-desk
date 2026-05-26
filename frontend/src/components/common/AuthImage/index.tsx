import { useEffect, useState } from 'react'
import { Image, Spin } from 'antd'
import client from '../../../api/client'

interface Props {
  attachmentId: number
  filename: string
  width?: number
  height?: number
}

export default function AuthImage({ attachmentId, filename, width = 80, height = 80 }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let objectUrl: string | null = null
    client.get(`/attachments/${attachmentId}`, { responseType: 'blob' })
      .then(res => {
        objectUrl = URL.createObjectURL(res.data as Blob)
        setBlobUrl(objectUrl)
      })
      .catch(() => setFailed(true))

    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [attachmentId])

  if (failed) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #f0f0f0', borderRadius: 4, background: '#fafafa', color: '#ccc', fontSize: 11 }}>
        {filename.slice(0, 8)}
      </div>
    )
  }

  if (!blobUrl) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #f0f0f0', borderRadius: 4 }}>
        <Spin size="small" />
      </div>
    )
  }

  return (
    <Image
      src={blobUrl}
      width={width}
      height={height}
      style={{ objectFit: 'cover', borderRadius: 4, border: '1px solid #f0f0f0' }}
      preview={{ src: blobUrl }}
    />
  )
}
