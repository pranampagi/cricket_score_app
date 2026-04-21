<template>
  <div class="page">
    <div class="container">
      <div class="page-header">
        <RouterLink to="/tournaments" class="btn btn-ghost btn-sm">← Tournaments</RouterLink>
        <div v-if="tournament" class="td-title-row">
          <h1 class="page-title">{{ tournament.name }}</h1>
          <span class="badge" :class="statusBadge(tournament.status)">{{ tournament.status }}</span>
          <span class="badge badge-primary">{{ tournament.format }}</span>
        </div>
        <RouterLink :to="newMatchUrl" class="btn btn-primary btn-sm">+ Match</RouterLink>
      </div>

      <div v-if="loading" class="spinner-wrap"><div class="spinner"></div></div>

      <div v-else-if="tournament" class="td-layout">
        <!-- Points Table -->
        <div class="td-section">
          <h2 class="section-title">Points Table</h2>
          <div class="card">
            <div class="table-wrap">
              <table class="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Team</th>
                    <th style="text-align:right">P</th>
                    <th style="text-align:right">W</th>
                    <th style="text-align:right">L</th>
                    <th style="text-align:right" class="hide-mobile">T</th>
                    <th style="text-align:right">Pts</th>
                    <th style="text-align:right" class="hide-mobile">NRR</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in standings" :key="row.id" :class="{ 'top-team': i < 2 }">
                    <td class="rank-cell">{{ i+1 }}</td>
                    <td class="player-name-cell">{{ row.name }}</td>
                    <td style="text-align:right;color:var(--text-muted)">{{ row.played }}</td>
                    <td style="text-align:right;color:var(--green);font-weight:700">{{ row.won }}</td>
                    <td style="text-align:right;color:var(--red)">{{ row.lost }}</td>
                    <td style="text-align:right;color:var(--text-muted)" class="hide-mobile">{{ row.tied }}</td>
                    <td style="text-align:right;font-weight:800;font-size:1rem">{{ row.points }}</td>
                    <td style="text-align:right;color:var(--text-dim)" class="hide-mobile">{{ row.nrr.toFixed(3) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Teams -->
        <div class="td-section">
          <h2 class="section-title">Teams</h2>
          <div class="teams-grid">
            <div v-for="team in tournament.teams" :key="team.id" class="team-card card">
              <div class="team-card-name">{{ team.name }}</div>
              <div class="team-players-list">
                <div v-for="p in team.players" :key="p.id" class="team-player-item">
                  <span class="player-dot"></span>{{ p.name }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Matches -->
        <div class="td-section">
          <h2 class="section-title">Matches</h2>
          <div v-if="tournament.matches.length === 0" class="text-muted" style="padding:1rem 0">
            No matches yet. <RouterLink :to="newMatchUrl" class="text-primary">Schedule one →</RouterLink>
          </div>
          <div class="matches-list">
            <RouterLink
              v-for="m in tournament.matches" :key="m.id"
              :to="m.status === 'live' || m.status === 'innings_break' ? `/match/${m.id}/live` : `/match/${m.id}/scorecard`"
              class="match-row card"
            >
              <div class="match-row-inner">
                <span class="badge" :class="mStatusBadge(m.status)">
                  <span v-if="m.status==='live'" class="live-dot"></span>
                  {{ mStatusLabel(m.status) }}
                </span>
                <div class="match-row-teams">
                  <span>{{ teamName(m.team1_id) }}</span>
                  <span class="text-muted" style="font-size:0.8rem">vs</span>
                  <span>{{ teamName(m.team2_id) }}</span>
                </div>
                <div v-if="m.result_summary" class="text-green" style="font-size:0.82rem">{{ m.result_summary }}</div>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-muted"><path d="M9 18l6-6-6-6"/></svg>
              </div>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

const route = useRoute()
const tid = computed(() => route.params.id)
const tournament = ref(null)
const standings = ref([])
const loading = ref(true)

const newMatchUrl = computed(() => `/match/new?tournament_id=${tid.value}`)

const teamMap = computed(() => {
  const m = {}
  if (tournament.value) tournament.value.teams.forEach(t => { m[t.id] = t.name })
  return m
})
function teamName(id) { return teamMap.value[id] || 'Team' }

function statusBadge(s) { return { setup: 'badge-purple', in_progress: 'badge-accent', completed: 'badge-green' }[s] || 'badge-primary' }
function mStatusBadge(s) { return { live: 'badge-red', completed: 'badge-green', setup: 'badge-purple', toss: 'badge-accent' }[s] || 'badge-primary' }
function mStatusLabel(s) { return { live: 'Live', completed: 'Done', setup: 'Setup', toss: 'Toss', innings_break: 'Break' }[s] || s }

onMounted(async () => {
  try {
    const [tRes, sRes] = await Promise.all([
      api.get(`/tournaments/${tid.value}`),
      api.get(`/tournaments/${tid.value}/standings`)
    ])
    tournament.value = tRes.data
    standings.value = sRes.data
  } finally { loading.value = false }
})
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
.td-title-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.td-layout { display: flex; flex-direction: column; gap: 2rem; }
.td-section {}
.teams-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
.team-card { padding: 1rem; }
.team-card-name { font-weight: 800; font-size: 1rem; margin-bottom: 0.75rem; color: var(--primary); }
.team-players-list { display: flex; flex-direction: column; gap: 0.35rem; }
.team-player-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: var(--text-dim); }
.player-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--border); flex-shrink: 0; }
.matches-list { display: flex; flex-direction: column; gap: 0.75rem; }
.match-row { cursor: pointer; text-decoration: none; transition: transform 0.15s; padding: 1rem; }
.match-row:hover { transform: translateX(2px); }
.match-row-inner { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.match-row-teams { display: flex; align-items: center; gap: 0.5rem; flex: 1; font-weight: 600; }
.rank-cell { font-weight: 700; color: var(--text-muted); }
.top-team td:first-child { color: var(--accent); }
.table-wrap { overflow-x: auto; }
</style>
