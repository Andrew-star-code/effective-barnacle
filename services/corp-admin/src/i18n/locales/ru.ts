// Все строки интерфейса — только через i18n (SPEC §22, правило 10).
export default {
  app: {
    title: 'Администрирование ИИ-ассистента',
  },
  nav: {
    dashboard: 'Дашборд',
  },
  dashboard: {
    title: 'Дашборд',
    backend: 'Сервис corp-ext',
    version: 'Версия: {version}',
    loading: 'Проверяем соединение…',
    unavailable: 'Сервис недоступен',
    stub: 'Разделы админки появляются по мере этапов плана (SPEC §21).',
  },
  notFound: {
    title: 'Страница не найдена',
    back: 'На главную',
  },
} as const
