<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { navigation } from '@/router/navigation'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const active = computed(() => String(route.name ?? ''))

function go(name: string | number) {
  void router.push({ name: String(name) })
}
</script>

<template>
  <t-layout class="admin-layout">
    <t-aside>
      <t-menu :value="active" @change="go">
        <template #logo>
          <span class="admin-layout__title">{{ t('app.title') }}</span>
        </template>
        <t-menu-item v-for="item in navigation" :key="item.route" :value="item.route">
          <template #icon><t-icon :name="item.icon" /></template>
          {{ t(item.label) }}
        </t-menu-item>
      </t-menu>
    </t-aside>
    <t-layout>
      <t-content class="admin-layout__content">
        <router-view />
      </t-content>
    </t-layout>
  </t-layout>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
}
.admin-layout__title {
  padding: 0 16px;
  font-weight: 600;
  line-height: 1.3;
}
.admin-layout__content {
  padding: 24px;
}
</style>
