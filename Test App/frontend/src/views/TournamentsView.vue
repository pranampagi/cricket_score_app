<template>
  <div class="page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">Tournaments</h1>
        <RouterLink to="/tournaments/new" class="btn btn-primary">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          New Tournament
        </RouterLink>
      </div>

      <div v-if="loading" class="spinner-wrap"><div class="spinner"></div></div>

      <div v-else-if="tournaments.length === 0" class="empty-state card">
        <div class="empty-icon">🏆</div>
        <h3>No tournaments yet</h3>
        <p class="text-muted">Create your first tournament to track team standings and match schedules.</p>
        <RouterLink to="/tournaments/new" class="btn btn-primary" style="margin-top:1rem">Create Tournament</RouterLink>
      </div>

      <div v-else class="tournaments-grid">
        <RouterLink v-for="t in tournaments" :key="t.id" :to="`/tournaments/${t.id}`" class="tournament-card card">
          <div class="tc-top">
            <span class="badge" :class="formatBadge(t.format)">{{ t.format }}</span>
            <span class="badge" :class="statusBadge(t.status)">{{ t.status }}</span>
          </div>
          <h3 class="tc-name">{{ t.name }}</h3>
          <div class="tc-meta">
            <span class="meta-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
              {{ t.overs_per_match }} overs
            </span>
            <span class="meta-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
              {{ t.players_per_team }} per team
            </span>
            <span class="meta-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
              {{ t.teams?.length || 0 }} teams
            </span>
          </div>
          <div class="tc-matches">
            {{ t.matches?.length || 0 }} matches
          </div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const tournaments = ref([])
const loading = ref(true)

onMounted(async () => {
  try { const { data } = await api.get('/tournaments'); tournaments.value = data }
  finally { loading.value = false }
})

function formatBadge(f) { return f === 'knockout' ? 'badge-red' : 'badge-primary' }
function statusBadge(s) { return { setup: 'badge-purple', in_progress: 'badge-accent', completed: 'badge-green' }[s] || 'badge-primary' }
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.tournaments-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.tournament-card { display: flex; flex-direction: column; gap: 0.75rem; cursor: pointer; text-decoration: none; transition: transform 0.2s; }
.tournament-card:hover { transform: translateY(-2px); }
.tc-top { display: flex; gap: 0.5rem; }
.tc-name { font-size: 1.2rem; font-weight: 800; }
.tc-meta { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.meta-item { display: flex; align-items: center; gap: 0.3rem; font-size: 0.8rem; color: var(--text-dim); }
.tc-matches { font-size: 0.82rem; color: var(--text-muted); border-top: 1px solid var(--border); padding-top: 0.75rem; }
.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }
</style>
