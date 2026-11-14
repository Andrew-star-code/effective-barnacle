import { describe, expect, it } from 'vitest'

import { i18n } from '@/i18n'
import ru from '@/i18n/locales/ru'
import { routes } from '@/router'
import { navigation } from '@/router/navigation'

function keys(node: object, prefix = ''): string[] {
  return Object.entries(node).flatMap(([key, value]) =>
    typeof value === 'object' ? keys(value as object, prefix + key + '.') : [prefix + key],
  )
}

describe('i18n', () => {
  it('использует русский по умолчанию', () => {
    expect(i18n.global.locale.value).toBe('ru')
    expect(i18n.global.t('nav.dashboard')).toBe('Дашборд')
  })

  it('не содержит иероглифов в строках', () => {
    const cjk = /[㐀-鿿]/
    for (const key of keys(ru)) {
      expect(cjk.test(i18n.global.t(key)), key).toBe(false)
    }
  })
})

describe('навигация', () => {
  it('каждый пункт меню ведёт на существующий маршрут и имеет перевод', () => {
    const names = routes.flatMap((r) => [r.name, ...(r.children ?? []).map((c) => c.name)])
    const known = new Set(keys(ru))
    for (const item of navigation) {
      expect(names).toContain(item.route)
      expect(known.has(item.label), item.label).toBe(true)
    }
  })
})
