export interface NavItem {
  /** Имя маршрута из router/index.ts */
  route: string
  /** Ключ i18n */
  label: string
  icon: string
}

export const navigation: NavItem[] = [{ route: 'dashboard', label: 'nav.dashboard', icon: 'dashboard' }]
