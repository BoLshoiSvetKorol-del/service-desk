import { useEffect, useRef, useState } from 'react'
import { Button, DatePicker, Dropdown, Input, Modal, Select, Space, Tag, message } from 'antd'
import { BookOutlined } from '@ant-design/icons'
import type { TicketStatus, PriorityName, TicketFilters, SavedFilter, Priority } from '../../../types/ticket'
import { STATUS_LABELS, PRIORITY_LABELS } from '../../../types/ticket'
import { getDepartments } from '../../../api/departments'
import { getUsers } from '../../../api/users'
import { getPriorities } from '../../../api/priorities'
import { getSavedFilters, createSavedFilter, deleteSavedFilter } from '../../../api/filters'
import type { Department, User } from '../../../types/user'
import { getErrorMessage } from '../../../types/common'

const { RangePicker } = DatePicker

const ALL_STATUSES: TicketStatus[] = ['new', 'in_progress', 'waiting_info', 'resolved', 'cancelled']

const STATUS_COLORS: Record<TicketStatus, string> = {
  new: '#1677ff',
  in_progress: '#13c2c2',
  waiting_info: '#d48806',
  resolved: '#52c41a',
  cancelled: '#8c8c8c',
}

const PRIORITY_COLORS: Record<PriorityName, string> = {
  low: '#8c8c8c',
  normal: '#1677ff',
  high: '#fa8c16',
  critical: '#f5222d',
}

interface Props {
  filters: TicketFilters
  onChange: (f: TicketFilters) => void
}

export default function FilterPanel({ filters, onChange }: Props) {
  const [searchInput, setSearchInput] = useState(filters.search ?? '')
  const [departments, setDepartments] = useState<Department[]>([])
  const [agents, setAgents] = useState<User[]>([])
  const [priorities, setPriorities] = useState<Priority[]>([])
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([])
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saving, setSaving] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => {})
    getUsers({ role: 'agent', page_size: 100 }).then(r => setAgents(r.items)).catch(() => {})
    getPriorities().then(setPriorities).catch(() => {})
    getSavedFilters().then(setSavedFilters).catch(() => {})
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onChange({ ...filters, search: searchInput || undefined, page: 1 })
    }, 300)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput])

  function setFilter(patch: Partial<TicketFilters>) {
    onChange({ ...filters, ...patch, page: 1 })
  }

  function toggleStatus(s: TicketStatus) {
    setFilter({ status: filters.status === s ? undefined : s })
  }

  function togglePriority(p: Priority) {
    setFilter({ priority_id: filters.priority_id === p.id ? undefined : p.id })
  }

  async function handleSaveFilter() {
    if (!saveName.trim()) return
    setSaving(true)
    try {
      const saved = await createSavedFilter(saveName.trim(), filters)
      setSavedFilters(prev => [...prev, saved])
      setSaveModalOpen(false)
      setSaveName('')
      message.success('Фильтр сохранён')
    } catch (e) {
      message.error(getErrorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteFilter(id: number, e: React.MouseEvent) {
    e.stopPropagation()
    try {
      await deleteSavedFilter(id)
      setSavedFilters(prev => prev.filter(f => f.id !== id))
    } catch (e) {
      message.error(getErrorMessage(e))
    }
  }

  function applyFilter(saved: SavedFilter) {
    onChange({ ...saved.filter_params, page: 1 })
    setSearchInput(saved.filter_params.search ?? '')
  }

  const savedMenuItems = [
    ...(savedFilters.length === 0
      ? [{ key: 'empty', label: <span style={{ color: '#999' }}>Нет сохранённых фильтров</span>, disabled: true }]
      : savedFilters.map(sf => ({
          key: sf.id,
          label: (
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <span onClick={() => applyFilter(sf)}>{sf.name}</span>
              <span
                style={{ color: '#ff4d4f', cursor: 'pointer', fontSize: 12 }}
                onClick={e => handleDeleteFilter(sf.id, e)}
              >✕</span>
            </Space>
          ),
        }))),
    { type: 'divider' as const },
    { key: 'save', label: <span>Сохранить текущий фильтр...</span>, onClick: () => setSaveModalOpen(true) },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, paddingBottom: 12 }}>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <Input.Search
          placeholder="Поиск по номеру или заголовку"
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          onSearch={v => setSearchInput(v)}
          style={{ width: 260 }}
          allowClear
        />
        <RangePicker
          placeholder={['Дата от', 'Дата до']}
          onChange={(_, strings) => {
            const [from, to] = strings as [string, string]
            setFilter({ date_from: from || undefined, date_to: to || undefined })
          }}
          format="DD.MM.YYYY"
          style={{ width: 240 }}
        />
        <Select
          placeholder="Отдел"
          allowClear
          style={{ width: 180 }}
          value={filters.department_id ?? undefined}
          onChange={v => setFilter({ department_id: v ?? undefined })}
          options={departments.map(d => ({ value: d.id, label: d.name }))}
        />
        <Select
          placeholder="Исполнитель"
          allowClear
          style={{ width: 180 }}
          value={filters.assignee_id ?? undefined}
          onChange={v => setFilter({ assignee_id: v ?? undefined })}
          options={agents.map(u => ({ value: u.id, label: u.full_name || u.username }))}
        />
        <Dropdown menu={{ items: savedMenuItems }} trigger={['click']}>
          <Button icon={<BookOutlined />}>Мои фильтры</Button>
        </Dropdown>
        {(filters.status || filters.priority_id || filters.department_id || filters.assignee_id || filters.search) && (
          <Button
            size="small"
            type="link"
            onClick={() => { onChange({ page: 1, page_size: filters.page_size }); setSearchInput('') }}
          >
            Сбросить все
          </Button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ color: '#666', fontSize: 13, minWidth: 52 }}>Статус:</span>
        {ALL_STATUSES.map(s => {
          const active = filters.status === s
          return (
            <Tag.CheckableTag
              key={s}
              checked={active}
              onChange={() => toggleStatus(s)}
              style={active ? { backgroundColor: STATUS_COLORS[s], borderColor: STATUS_COLORS[s], color: '#fff' } : {}}
            >
              {STATUS_LABELS[s]}
            </Tag.CheckableTag>
          )
        })}
      </div>

      {priorities.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ color: '#666', fontSize: 13, minWidth: 52 }}>Приоритет:</span>
          {priorities.map(p => {
            const active = filters.priority_id === p.id
            const color = PRIORITY_COLORS[p.name as PriorityName]
            return (
              <Tag.CheckableTag
                key={p.id}
                checked={active}
                onChange={() => togglePriority(p)}
                style={active ? { backgroundColor: color, borderColor: color, color: '#fff' } : {}}
              >
                {PRIORITY_LABELS[p.name as PriorityName]}
              </Tag.CheckableTag>
            )
          })}
        </div>
      )}

      <Modal
        title="Сохранить фильтр"
        open={saveModalOpen}
        onOk={handleSaveFilter}
        onCancel={() => { setSaveModalOpen(false); setSaveName('') }}
        confirmLoading={saving}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Input
          placeholder="Название фильтра"
          value={saveName}
          onChange={e => setSaveName(e.target.value)}
          onPressEnter={handleSaveFilter}
          autoFocus
        />
      </Modal>
    </div>
  )
}
