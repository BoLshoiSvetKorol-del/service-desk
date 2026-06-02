import { useEffect, useRef, useState } from 'react'
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
  const urlRef = useRef<string | null>(null)

  useEffect(() => {
    setBlobUrl(null)
    setFailed(false)

    client.get(`/attachments/${attachmentId}`, { responseType: 'blob' })
      .then(res => {
        const blob = res.data as Blob
        // Guard: only create URL for actual image blobs
        if (!blob.type.startsWith('image/')) {
          setFailed(true)
          return
        }
        const url = URL.createObjectURL(blob)
        urlRef.current = url
        setBlobUrl(url)
      })
      .catch(() => setFailed(true))

    return () => {
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current)
        urlRef.current = null
      }
    }
  }, [attachmentId])

  if (failed) {
    return (
      <div style={{
        width, height,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: '1px solid #f0f0f0', borderRadius: 4, background: '#fafafa',
        color: '#ccc', fontSize: 11, textAlign: 'center', padding: 4,
        overflow: 'hidden', wordBreak: 'break-all',
      }}>
        {filename.slice(0, 12)}
      </div>
    )
  }

  if (!blobUrl) {
    return (
      <div style={{
        width, height,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: '1px solid #f0f0f0', borderRadius: 4,
      }}>
        <Spin size="small" />
      </div>
    )
  }

  return (
    <Image
      src={blobUrl}
      width={width}
      height={height}
      style={{ objectFit: 'cover', borderRadius: 4, border: '1px solid #f0f0f0', display: 'block' }}
      preview={{ src: blobUrl }}
      fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    />
  )
}
