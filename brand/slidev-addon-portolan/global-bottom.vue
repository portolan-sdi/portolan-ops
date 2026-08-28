<script setup>
import { useNav } from '@slidev/client'
import { computed } from 'vue'

const { currentSlideRoute } = useNav()
// Any slide can drop the mark with `hideLogomark: true` in its frontmatter.
const hide = computed(
  () => currentSlideRoute?.value?.meta?.slide?.frontmatter?.hideLogomark,
)
</script>

<template>
  <footer v-if="!hide" class="fixed bottom-5 right-6 z-10 pointer-events-none">
    <svg viewBox="0 0 32 32" class="w-5 opacity-40">
      <g fill="var(--color-text)">
        <path d="M2.83 18.247l26.34-9.124L2.83 0z"/>
        <path d="M29.17 32V13.753L2.83 22.877z"/>
      </g>
    </svg>
  </footer>
</template>
