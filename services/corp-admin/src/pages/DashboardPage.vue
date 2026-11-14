<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { api } from '@/api/client'

const { t } = useI18n()
const state = ref<'loading' | 'ok' | 'error'>('loading')
const version = ref('')

onMounted(async () => {
  try {
    const { data } = await api.GET('/corp/api/version')
    if (!data) throw new Error('empty response')
    version.value = data.version
    state.value = 'ok'
  } catch {
    state.value = 'error'
  }
})
</script>

<template>
  <h2>{{ t('dashboard.title') }}</h2>
  <t-card :title="t('dashboard.backend')" class="dashboard-card">
    <t-loading v-if="state === 'loading'" :text="t('dashboard.loading')" size="small" />
    <t-tag v-else-if="state === 'ok'" theme="success" variant="light">
      {{ t('dashboard.version', { version }) }}
    </t-tag>
    <t-tag v-else theme="danger" variant="light">{{ t('dashboard.unavailable') }}</t-tag>
  </t-card>
  <p>{{ t('dashboard.stub') }}</p>
</template>

<style scoped>
.dashboard-card {
  max-width: 480px;
  margin: 16px 0;
}
</style>
