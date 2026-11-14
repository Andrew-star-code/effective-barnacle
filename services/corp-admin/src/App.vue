<script setup lang="ts">
import ruRU from 'tdesign-vue-next/es/locale/ru_RU'
</script>

<template>
  <t-config-provider :global-config="ruRU">
    <router-view />
  </t-config-provider>
</template>
