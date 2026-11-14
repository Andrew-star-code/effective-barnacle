import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// Новая страница: файл в src/pages/ + запись здесь + пункт в navigation.ts
// (docs/guides/add-corp-admin-page.md — появится на этапе 1).
export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/pages/DashboardPage.vue') },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/pages/NotFoundPage.vue'),
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})
