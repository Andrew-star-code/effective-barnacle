<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <t-space direction="vertical" align="center" class="not-found">
    <h2>{{ t('notFound.title') }}</h2>
    <router-link :to="{ name: 'dashboard' }">{{ t('notFound.back') }}</router-link>
  </t-space>
</template>

<style scoped>
.not-found {
  width: 100%;
  padding-top: 96px;
}
</style>
