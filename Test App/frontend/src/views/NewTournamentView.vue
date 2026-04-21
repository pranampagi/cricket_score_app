<template>
  <div class="page">
    <div class="container" style="max-width:640px">
      <div class="page-header">
        <RouterLink to="/tournaments" class="btn btn-ghost btn-sm">← Back</RouterLink>
        <h1 class="page-title">New Tournament</h1>
      </div>

      <div class="card">
        <div class="form-grid">
          <div class="form-group" style="grid-column:1/-1">
            <label class="form-label">Tournament Name</label>
            <input v-model="form.name" class="input" placeholder="e.g. IPL 2025, Office Cricket League" />
          </div>
          <div class="form-group">
            <label class="form-label">Format</label>
            <select v-model="form.format" class="select">
              <option value="league">League (Round Robin)</option>
              <option value="knockout">Knockout</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Overs per Match</label>
            <input type="number" v-model.number="form.overs_per_match" class="input" min="1" max="100" placeholder="e.g. 20" />
          </div>
          <div class="form-group">
            <label class="form-label">Players per Team</label>
            <input type="number" v-model.number="form.players_per_team" class="input" min="2" max="30" placeholder="e.g. 11" />
          </div>
        </div>

        <div class="divider"></div>

        <!-- Add teams -->
        <div class="section-title">Teams</div>
        <div v-for="(team, ti) in form.teams" :key="ti" class="team-entry card" style="margin-bottom:1rem;padding:1rem">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
            <span class="form-label">Team {{ ti + 1 }}</span>
            <button class="btn btn-ghost btn-sm" style="color:var(--red)" @click="removeTeam(ti)">Remove</button>
          </div>
          <div class="form-group" style="margin-bottom:0.75rem">
            <input v-model="team.name" class="input" :placeholder="`Team ${ti+1} name`" />
          </div>
          <div class="players-list">
            <div v-for="(_, pi) in team.players" :key="pi" class="player-row">
              <span class="player-num">{{ pi+1 }}</span>
              <input v-model="team.players[pi]" class="input input-sm" :placeholder="`Player ${pi+1}`" />
            </div>
          </div>
        </div>

        <button class="btn btn-ghost" @click="addTeam" style="width:100%;margin-bottom:1.5rem">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          Add Team
        </button>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <div class="step-actions">
          <RouterLink to="/tournaments" class="btn btn-ghost">Cancel</RouterLink>
          <button class="btn btn-primary btn-lg" @click="create" :disabled="loading || !form.name || form.teams.length < 2">
            <span v-if="loading" class="spinner" style="width:18px;height:18px;border-width:2px"></span>
            Create Tournament
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')

const form = ref({
  name: '',
  format: 'league',
  overs_per_match: 20,
  players_per_team: 11,
  teams: []
})

function makeTeam() {
  return { name: '', players: Array(form.value.players_per_team).fill('') }
}

function addTeam() { form.value.teams.push(makeTeam()) }
function removeTeam(i) { form.value.teams.splice(i, 1) }

watch(() => form.value.players_per_team, (n) => {
  form.value.teams.forEach(t => { t.players = Array(n).fill('') })
})

async function create() {
  loading.value = true; error.value = ''
  try {
    const { data: tournament } = await api.post('/tournaments', {
      name: form.value.name,
      format: form.value.format,
      overs_per_match: form.value.overs_per_match,
      players_per_team: form.value.players_per_team
    })
    for (const team of form.value.teams) {
      const { data: t } = await api.post('/teams', { name: team.name || 'Team', tournament_id: tournament.id })
      for (let i = 0; i < team.players.length; i++) {
        await api.post('/players', { name: team.players[i] || `Player ${i+1}`, team_id: t.id })
      }
    }
    router.push(`/tournaments/${tournament.id}`)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally { loading.value = false }
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
.players-list { display: flex; flex-direction: column; gap: 0.4rem; }
.player-row { display: flex; align-items: center; gap: 0.5rem; }
.player-num { width: 22px; text-align: center; font-size: 0.78rem; color: var(--text-muted); font-weight: 600; flex-shrink: 0; }
.input-sm { padding: 0.5rem 0.75rem; font-size: 0.85rem; }
.step-actions { display: flex; justify-content: flex-end; gap: 0.75rem; }
.error-msg { color: var(--red); font-size: 0.875rem; margin-bottom: 1rem; padding: 0.75rem; background: var(--red-glow); border-radius: var(--radius-sm); }
@media (max-width: 600px) { .form-grid { grid-template-columns: 1fr; } }
</style>
