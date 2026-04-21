<template>
  <div class="page">
    <div class="container">
      <!-- Hero -->
      <div class="hero">
        <div class="hero-badge badge badge-primary">🏏 Live Scoring</div>
        <h1 class="page-title hero-title">Cricket Scorecard<br><span class="text-primary">Made Simple</span></h1>
        <p class="hero-sub">Ball-by-ball scoring, tournament management, and full scorecards — all in one place.</p>
        <div class="hero-actions">
          <RouterLink to="/match/new" class="btn btn-primary btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
            New Match
          </RouterLink>
          <RouterLink to="/tournaments" class="btn btn-ghost btn-lg">View Tournaments</RouterLink>
        </div>
      </div>

      <!-- Stats row -->
      <div class="stats-row" v-if="stats.matches > 0">
        <div class="stat-card card">
          <div class="stat-num text-primary">{{ stats.matches }}</div>
          <div class="stat-label">Matches</div>
        </div>
        <div class="stat-card card">
          <div class="stat-num text-accent">{{ stats.tournaments }}</div>
          <div class="stat-label">Tournaments</div>
        </div>
        <div class="stat-card card">
          <div class="stat-num text-green">{{ stats.live }}</div>
          <div class="stat-label">Live Now</div>
        </div>
      </div>

      <!-- Recent matches -->
      <section v-if="recentMatches.length">
        <h2 class="section-title">Recent Matches</h2>
        <div class="matches-grid">
          <RouterLink
            v-for="m in recentMatches" :key="m.id"
            :to="m.status === 'live' || m.status === 'innings_break' ? `/match/${m.id}/live` : `/match/${m.id}/scorecard`"
            class="match-card card"
          >
            <div class="match-card-top">
              <span class="badge" :class="statusBadge(m.status)">
                <span v-if="m.status==='live'" class="live-dot"></span>
                {{ statusLabel(m.status) }}
              </span>
              <span class="text-muted" style="font-size:0.8rem">{{ m.overs }} overs</span>
            </div>
            <div class="match-teams">
              <div class="team-name">{{ m.team1?.name || 'Team 1' }}</div>
              <div class="vs-badge">VS</div>
              <div class="team-name">{{ m.team2?.name || 'Team 2' }}</div>
            </div>
            <div v-if="m.result_summary" class="match-result text-green">{{ m.result_summary }}</div>
            <div class="match-date text-muted">{{ formatDate(m.created_at) }}</div>
          </RouterLink>
        </div>
      </section>

      <!-- Empty state -->
      <div v-else class="empty-state card">
        <div class="empty-icon">🏏</div>
        <h3>No matches yet</h3>
        <p class="text-muted">Start your first match or create a tournament to get going.</p>
        <RouterLink to="/match/new" class="btn btn-primary" style="margin-top:1rem">Start a Match</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const recentMatches = ref([])
const stats = ref({ matches: 0, tournaments: 0, live: 0 })

async function load() {
  try {
    const [matchRes, tourRes] = await Promise.all([
      api.get('/matches'),
      api.get('/tournaments')
    ])
    recentMatches.value = matchRes.data.slice(0, 6)
    stats.value = {
      matches: matchRes.data.length,
      tournaments: tourRes.data.length,
      live: matchRes.data.filter(m => m.status === 'live').length
    }
  } catch (e) { /* ignore */ }
}

function statusBadge(s) {
  return { live: 'badge-red', completed: 'badge-green', setup: 'badge-purple', toss: 'badge-accent', innings_break: 'badge-accent' }[s] || 'badge-primary'
}
function statusLabel(s) {
  return { live: 'Live', completed: 'Completed', setup: 'Setup', toss: 'Toss', innings_break: 'Break' }[s] || s
}
function formatDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' })
}

onMounted(load)
</script>

<style scoped>
.hero { text-align: center; padding: 3.5rem 0 2.5rem; }
.hero-badge { margin-bottom: 1rem; }
.hero-title { font-size: 2.8rem; line-height: 1.15; margin: 0.75rem 0; }
.hero-sub { color: var(--text-dim); max-width: 480px; margin: 0 auto 2rem; }
.hero-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1.5rem 0 2.5rem; }
.stat-card { text-align: center; padding: 1.25rem; }
.stat-num { font-size: 2.25rem; font-weight: 900; }
.stat-label { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }

.matches-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.match-card { display: flex; flex-direction: column; gap: 0.75rem; cursor: pointer; text-decoration: none; transition: transform 0.2s; }
.match-card:hover { transform: translateY(-2px); }
.match-card-top { display: flex; justify-content: space-between; align-items: center; }
.match-teams { display: flex; align-items: center; gap: 1rem; }
.team-name { font-weight: 700; font-size: 1rem; flex: 1; }
.vs-badge { font-size: 0.7rem; font-weight: 800; color: var(--text-muted); background: var(--bg-card2); padding: 0.2rem 0.5rem; border-radius: 4px; }
.match-result { font-size: 0.85rem; font-weight: 600; }
.match-date { font-size: 0.78rem; }

.empty-state { text-align: center; padding: 4rem 2rem; margin-top: 2rem; }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }

@media (max-width: 768px) {
  .hero-title { font-size: 2rem; }
  .stats-row { grid-template-columns: repeat(3,1fr); gap: 0.5rem; }
}
</style>
