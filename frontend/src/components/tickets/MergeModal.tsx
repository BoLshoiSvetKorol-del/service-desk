import { useState } from 'react'
import { Input, List, Modal, Spin, Typography, message } from 'antd'
import { MergeCellsOutlined } from '@ant-design/icons'
import { findDuplicates, mergeTicket } from '../../api/tickets'
import type { TicketListItem } from '../../types/ticket'
import StatusBadge from '../common/StatusBadge'

interface Props {
  ticketId: number
  onMerged: () => void
  onClose: () => void
}

export default function MergeModal({ ticketId, onMerged, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<TicketListItem[]>([])
  const [searching, setSearching] = useState(false)
  const [merging, setMerging] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  async function handleSearch(value: string) {
    setQuery(value)
    setSearching(true)
    try {
      const list = await findDuplicates(ticketId, value)
      setResults(list)
    } catch {
      message.error('Ошибка поиска')
    } finally {
      setSearching(false)
    }
  }

  async function handleMerge() {
    if (!selectedId) return
    setMerging(true)
    try {
      await mergeTicket(ticketId, selectedId)
      message.success('Заявка объединена')
      onMerged()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      message.error(err?.response?.data?.detail ?? 'Ошибка объединения')
    } finally {
      setMerging(false)
    }
  }

  return (
    <Modal
      open
      title={
        <span>
          <MergeCellsOutlined style={{ marginRight: 8 }} />
          Объединить заявку
        </span>
      }
      onCancel={onClose}
      onOk={handleMerge}
      okText="Объединить"
      cancelText="Отмена"
      okButtonProps={{ disabled: !selectedId, loading: merging }}
      width={560}
    >
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
        Выберите заявку-цель. Текущая заявка будет помечена как «объединена» и закрыта.
      </Typography.Text>

      <Input.Search
        placeholder="Поиск по номеру или заголовку"
        value={query}
        onChange={e => handleSearch(e.target.value)}
        onSearch={handleSearch}
        style={{ marginBottom: 12 }}
        allowClear
      />

      {searching ? (
        <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>
      ) : (
        <List
          size="small"
          dataSource={results}
          locale={{ emptyText: query ? 'Ничего не найдено' : 'Введите запрос для поиска' }}
          renderItem={item => (
            <List.Item
              onClick={() => setSelectedId(item.id)}
              style={{
                cursor: 'pointer',
                padding: '8px 12px',
                borderRadius: 6,
                background: selectedId === item.id ? '#e6f4ff' : undefined,
                border: selectedId === item.id ? '1px solid #1677ff' : '1px solid transparent',
                marginBottom: 4,
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Typography.Text strong style={{ fontSize: 13 }}>{item.number}</Typography.Text>
                  <StatusBadge status={item.status} />
                </div>
                <Typography.Text style={{ fontSize: 13, color: '#555' }}>{item.title}</Typography.Text>
              </div>
            </List.Item>
          )}
          style={{ maxHeight: 300, overflowY: 'auto' }}
        />
      )}
    </Modal>
  )
}
