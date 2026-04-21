<template>
  <div id="app-wrapper">
    <AppNavbar />
    <main class="main-content">
      <RouterView v-slot="{ Component }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
    <BottomNav />
  </div>
</template>

<script setup>
import AppNavbar from '@/components/AppNavbar.vue'
import BottomNav from '@/components/BottomNav.vue'
</script>

<style scoped>
#app-wrapper { min-height: 100vh; display: flex; flex-direction: column; }
.main-content { flex: 1; }
</style>
