import { Button, Card, Collapse, Space, Typography } from 'antd'
import { ArrowLeftOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

const FAQ_ITEMS = [
  {
    key: '1',
    label: 'Как создать заявку?',
    children: (
      <Paragraph>
        Нажмите кнопку <Text strong>«Создать заявку»</Text> на главной странице портала. Заполните тему обращения,
        подробное описание проблемы и выберите тип обращения. При необходимости прикрепите файлы (скриншоты,
        документы). После отправки заявке будет присвоен уникальный номер в формате <Text code>SD-2026-00001</Text>.
      </Paragraph>
    ),
  },
  {
    key: '2',
    label: 'Как отслеживать статус заявки?',
    children: (
      <Paragraph>
        Все ваши заявки доступны в разделе <Text strong>«Мои заявки»</Text>. Нажмите на заявку, чтобы увидеть
        подробную информацию, статус обработки и историю переписки. Вы также получите уведомления об изменении
        статуса по электронной почте.
      </Paragraph>
    ),
  },
  {
    key: '3',
    label: 'Что означают статусы заявки?',
    children: (
      <>
        <Paragraph>Каждая заявка проходит следующие стадии:</Paragraph>
        <ul>
          <li><Text strong>Новая</Text> — заявка зарегистрирована и ожидает обработки.</li>
          <li><Text strong>В работе</Text> — специалист приступил к решению.</li>
          <li><Text strong>Ожидает информации</Text> — от вас запрошены дополнительные данные. Ответьте в комментариях.</li>
          <li><Text strong>Выполнена</Text> — проблема решена. Вы можете переоткрыть заявку, если проблема повторилась.</li>
          <li><Text strong>Отменена</Text> — заявка закрыта без выполнения.</li>
        </ul>
      </>
    ),
  },
  {
    key: '4',
    label: 'Что такое SLA и сроки обработки?',
    children: (
      <>
        <Paragraph>
          SLA (Service Level Agreement) — гарантированное время реакции службы поддержки. Сроки зависят от
          приоритета заявки:
        </Paragraph>
        <ul>
          <li><Text strong>Критичный</Text> — 1 рабочий час</li>
          <li><Text strong>Высокий</Text> — 4 рабочих часа</li>
          <li><Text strong>Нормальный</Text> — 8 рабочих часов</li>
          <li><Text strong>Низкий</Text> — 24 рабочих часа</li>
        </ul>
        <Paragraph type="secondary">Рабочее время: понедельник–пятница, 9:00–18:00.</Paragraph>
      </>
    ),
  },
  {
    key: '5',
    label: 'Как добавить комментарий или уточнение к заявке?',
    children: (
      <Paragraph>
        Откройте нужную заявку и прокрутите до раздела <Text strong>«Комментарии»</Text>. Введите текст в поле
        ответа и нажмите <Text strong>«Отправить»</Text>. Специалист получит уведомление о вашем сообщении.
      </Paragraph>
    ),
  },
  {
    key: '6',
    label: 'Можно ли прикрепить файл к уже созданной заявке?',
    children: (
      <Paragraph>
        Да. Откройте заявку, перейдите на вкладку <Text strong>«Вложения»</Text> и загрузите нужный файл.
        Поддерживаются изображения, PDF, документы Word/Excel, архивы. Максимальный размер файла — 10 МБ.
      </Paragraph>
    ),
  },
  {
    key: '7',
    label: 'Как связаться со службой поддержки напрямую?',
    children: (
      <Paragraph>
        Вы можете создать заявку через портал — это самый быстрый способ. Также вы можете указать удобный
        способ обратной связи (телефон, Telegram, WhatsApp) в разделе <Text strong>«Профиль»</Text>, и
        специалист свяжется с вами напрямую.
      </Paragraph>
    ),
  },
  {
    key: '8',
    label: 'Я не получаю уведомления на почту. Что делать?',
    children: (
      <Paragraph>
        Проверьте папку «Спам» в вашем почтовом клиенте. Убедитесь, что в профиле указан правильный
        адрес электронной почты. Если проблема сохраняется — создайте заявку с описанием ситуации.
      </Paragraph>
    ),
  },
]

export default function PortalFaqPage() {
  const navigate = useNavigate()

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        style={{ paddingLeft: 0, marginBottom: 16 }}
        onClick={() => navigate('/portal/tickets')}
      >
        К списку заявок
      </Button>

      <Space align="center" style={{ marginBottom: 20 }}>
        <QuestionCircleOutlined style={{ fontSize: 22, color: '#1677ff' }} />
        <Title level={4} style={{ margin: 0 }}>Часто задаваемые вопросы</Title>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Paragraph type="secondary" style={{ margin: 0 }}>
          Здесь собраны ответы на наиболее частые вопросы о работе с порталом службы поддержки
          компании <Text strong>Экспресс Технологии</Text>. Если вы не нашли ответ — создайте заявку,
          и мы поможем.
        </Paragraph>
      </Card>

      <Collapse
        accordion={false}
        items={FAQ_ITEMS}
        style={{ background: '#fff' }}
        bordered={false}
      />
    </div>
  )
}
