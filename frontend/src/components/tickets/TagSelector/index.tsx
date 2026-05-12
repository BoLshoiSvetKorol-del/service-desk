import { useEffect, useState } from 'react'
import { Select, Tag, message } from 'antd'
import { getTags, createTag, setTicketTags } from '../../../api/tags'
import type { Tag as TagType } from '../../../api/tags'

interface Props {
  ticketId: number
  currentTags: TagType[]
  onChange: (tags: TagType[]) => void
  disabled?: boolean
}

export default function TagSelector({ ticketId, currentTags, onChange, disabled }: Props) {
  const [allTags, setAllTags] = useState<TagType[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getTags().then(setAllTags).catch(() => {})
  }, [])

  async function handleChange(selectedNames: string[]) {
    setSaving(true)
    try {
      const existingByName = Object.fromEntries(allTags.map(t => [t.name, t]))
      const tagIds: number[] = []

      for (const name of selectedNames) {
        if (existingByName[name]) {
          tagIds.push(existingByName[name].id)
        } else {
          // create new tag on the fly
          const created = await createTag(name)
          setAllTags(prev => [...prev, created])
          tagIds.push(created.id)
        }
      }

      const updated = await setTicketTags(ticketId, tagIds)
      onChange(updated)
    } catch {
      message.error('Ошибка обновления тегов')
    } finally {
      setSaving(false)
    }
  }

  const options = allTags.map(t => ({
    value: t.name,
    label: (
      <Tag color={t.color_hex} style={{ margin: 0 }}>{t.name}</Tag>
    ),
  }))

  return (
    <Select
      mode="tags"
      size="small"
      style={{ width: '100%' }}
      value={currentTags.map(t => t.name)}
      onChange={handleChange}
      options={options}
      loading={saving}
      disabled={disabled}
      placeholder="Добавить тег..."
      tokenSeparators={[',']}
      tagRender={props => (
        <Tag
          color={allTags.find(t => t.name === props.value)?.color_hex ?? '#1677ff'}
          closable={props.closable}
          onClose={props.onClose}
          style={{ marginInlineEnd: 4 }}
        >
          {props.label}
        </Tag>
      )}
    />
  )
}
