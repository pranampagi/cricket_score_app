<template>
  <div class="page">
    <div class="container" style="max-width:760px">
      <div class="page-header">
        <RouterLink to="/" class="btn btn-ghost btn-sm">← Back</RouterLink>
        <h1 class="page-title">New Match</h1>
      </div>

      <!-- Step indicator -->
      <div class="steps">
        <div class="step" v-for="(s,i) in stepLabels" :key="i"
          :class="{ active: step === i+1, done: step > i+1 }">
          <div class="step-dot">{{ step > i+1 ? '✓' : i+1 }}</div>
          <div class="step-label">{{ s }}</div>
        </div>
      </div>

      <!-- Step 1: Match Settings -->
      <Transition name="slide-up" mode="out-in">
      <div v-if="step === 1" key="s1" class="card">
        <h2 class="section-title">Match Settings</h2>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Tournament (optional)</label>
            <select v-model="form.tournament_id" class="select">
              <option :value="null">— Quick Match —</option>
              <option v-for="t in tournaments" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Overs per Side</label>
            <input type="number" v-model.number="form.overs" class="input" min="1" max="100" placeholder="e.g. 20" />
          </div>
          <div class="form-group">
            <label class="form-label">Players per Team</label>
            <input type="number" v-model.number="form.players_per_team" class="input" min="2" max="30" placeholder="e.g. 11" />
          </div>
        </div>
        <div class="step-actions">
          <button class="btn btn-primary btn-lg" @click="step=2">Next: Teams →</button>
        </div>
      </div>
      </Transition>

      <!-- Step 2: Team Names -->
      <Transition name="slide-up" mode="out-in">
      <div v-if="step === 2" key="s2" class="card">
        <h2 class="section-title">Teams</h2>
        <div class="grid-2">
          <div class="form-group" v-if="!isTournamentMode">
            <label class="form-label">Team 1 Name</label>
            <input v-model="form.team1_name" class="input" placeholder="e.g. Mumbai Indians" />
          </div>
          <div class="form-group" v-else>
            <label class="form-label">Team 1</label>
            <select v-model="form.team1_id" class="select" @change="updateTournamentTeam(1)">
              <option :value="null">Select Team</option>
              <option v-for="t in activeTournament?.teams" :key="t.id" :value="t.id" :disabled="t.id === form.team2_id">{{ t.name }}</option>
            </select>
          </div>
          <div class="form-group" v-if="!isTournamentMode">
            <label class="form-label">Team 2 Name</label>
            <input v-model="form.team2_name" class="input" placeholder="e.g. Chennai Super Kings" />
          </div>
          <div class="form-group" v-else>
            <label class="form-label">Team 2</label>
            <select v-model="form.team2_id" class="select" @change="updateTournamentTeam(2)">
              <option :value="null">Select Team</option>
              <option v-for="t in activeTournament?.teams" :key="t.id" :value="t.id" :disabled="t.id === form.team1_id">{{ t.name }}</option>
            </select>
          </div>
        </div>
        <div class="step-actions">
          <button class="btn btn-ghost" @click="step=1">← Back</button>
          <button class="btn btn-primary btn-lg" @click="goToPlayers" :disabled="isTournamentMode ? (!form.team1_id || !form.team2_id) : (!form.team1_name || !form.team2_name)">Next: Players →</button>
        </div>
      </div>
      </Transition>

      <!-- Step 3: Players -->
      <Transition name="slide-up" mode="out-in">
      <div v-if="step === 3" key="s3" class="card">
        <h2 class="section-title">Player Names</h2>
        <div class="players-columns">
          <div class="team-players">
            <div class="team-players-title">{{ form.team1_name }}</div>
            <div v-for="(_, i) in form.team1_players" :key="`t1-${i}`" class="player-row">
              <span class="player-num">{{ i+1 }}</span>
              <input v-model="form.team1_players[i]" class="input" :placeholder="`Player ${i+1}`" :disabled="isTournamentMode" />
            </div>
          </div>
          <div class="team-players">
            <div class="team-players-title">{{ form.team2_name }}</div>
            <div v-for="(_, i) in form.team2_players" :key="`t2-${i}`" class="player-row">
              <span class="player-num">{{ i+1 }}</span>
              <input v-model="form.team2_players[i]" class="input" :placeholder="`Player ${i+1}`" :disabled="isTournamentMode" />
            </div>
          </div>
        </div>
        <div class="step-actions">
          <button class="btn btn-ghost" @click="step=2">← Back</button>
          <button class="btn btn-primary btn-lg" @click="step=4">Next: Toss →</button>
        </div>
      </div>
      </Transition>

      <!-- Step 4: Toss -->
      <Transition name="slide-up" mode="out-in">
      <div v-if="step === 4" key="s4" class="card">
        <h2 class="section-title">Toss</h2>
        <div class="toss-section">
          <div class="form-group">
            <label class="form-label">Toss Won By</label>
            <div class="toss-btns">
              <button class="toss-team-btn" :class="{ selected: form.toss_winner === 1 }" @click="form.toss_winner=1">{{ form.team1_name }}</button>
              <button class="toss-team-btn" :class="{ selected: form.toss_winner === 2 }" @click="form.toss_winner=2">{{ form.team2_name }}</button>
            </div>
          </div>
          <div class="form-group" style="margin-top:1.25rem">
            <label class="form-label">Elected To</label>
            <div class="toss-btns">
              <button class="toss-team-btn" :class="{ selected: form.toss_decision === 'bat' }" @click="form.toss_decision='bat'">🏏 Bat</button>
              <button class="toss-team-btn" :class="{ selected: form.toss_decision === 'bowl' }" @click="form.toss_decision='bowl'">🎳 Bowl</button>
            </div>
          </div>
        </div>
        <div class="step-actions">
          <button class="btn btn-ghost" @click="step=3">← Back</button>
          <button class="btn btn-primary btn-lg" @click="step=5" :disabled="!form.toss_winner || !form.toss_decision">Next: Open →</button>
        </div>
      </div>
      </Transition>

      <!-- Step 5: Opening Players -->
      <Transition name="slide-up" mode="out-in">
      <div v-if="step === 5" key="s5" class="card">
        <h2 class="section-title">Opening Players</h2>
        <p class="text-dim" style="margin-bottom:1.25rem;font-size:0.875rem">
          <strong>{{ battingTeamName }}</strong> will bat first.
        </p>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Striker (On Strike)</label>
            <select v-model.number="form.striker_id" class="select">
              <option value="">Select batsman</option>
              <option v-for="(p,i) in battingPlayers" :key="i" :value="i">{{ p || `Player ${i+1}` }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Non-Striker</label>
            <select v-model.number="form.non_striker_id" class="select">
              <option value="">Select batsman</option>
              <option v-for="(p,i) in battingPlayers" :key="i" :value="i" :disabled="i===form.striker_id">{{ p || `Player ${i+1}` }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Opening Bowler</label>
            <select v-model.number="form.bowler_id" class="select">
              <option value="">Select bowler</option>
              <option v-for="(p,i) in bowlingPlayers" :key="i" :value="i">{{ p || `Player ${i+1}` }}</option>
            </select>
          </div>
        </div>
        <div class="step-actions">
          <button class="btn btn-ghost" @click="step=4">← Back</button>
          <button class="btn btn-green btn-lg" @click="startMatch" :disabled="loading || form.striker_id==='' || form.non_striker_id==='' || form.bowler_id===''">
            <span v-if="loading" class="spinner" style="width:18px;height:18px;border-width:2px"></span>
            🏏 Start Match
          </button>
        </div>
        <div v-if="error" class="error-msg">{{ error }}</div>
      </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const step = ref(1)
const loading = ref(false)
const error = ref('')
const tournaments = ref([])

const stepLabels = ['Settings', 'Teams', 'Players', 'Toss', 'Open']

const form = ref({
  tournament_id: null,
  overs: 20,
  players_per_team: 11,
  team1_name: '',
  team2_name: '',
  team1_id: null,
  team2_id: null,
  team1_players: Array(11).fill(''),
  team2_players: Array(11).fill(''),
  toss_winner: null,
  toss_decision: '',
  striker_id: '',
  non_striker_id: '',
  bowler_id: ''
})

const isTournamentMode = computed(() => !!form.value.tournament_id)
const activeTournament = computed(() => tournaments.value.find(t => t.id === form.value.tournament_id))

watch(() => form.value.players_per_team, (n) => {
  if (!isTournamentMode.value) {
    form.value.team1_players = Array(n).fill('')
    form.value.team2_players = Array(n).fill('')
  }
})

function updateTournamentTeam(teamNum) {
  if (!activeTournament.value) return
  const tid = teamNum === 1 ? form.value.team1_id : form.value.team2_id
  const team = activeTournament.value.teams.find(t => t.id === tid)
  if (team) {
    if (teamNum === 1) {
      form.value.team1_name = team.name
      form.value.team1_players = team.players.map(p => p.name)
    } else {
      form.value.team2_name = team.name
      form.value.team2_players = team.players.map(p => p.name)
    }
  }
}

function goToPlayers() {
  if (isTournamentMode.value) {
    if (!form.value.team1_id || !form.value.team2_id) return
  } else {
    if (!form.value.team1_name || !form.value.team2_name) return
  }
  step.value = 3
}

const battingTeamName = computed(() => {
  if (!form.value.toss_winner || !form.value.toss_decision) return ''
  const winnerName = form.value.toss_winner === 1 ? form.value.team1_name : form.value.team2_name
  if (form.value.toss_decision === 'bat') return winnerName
  return form.value.toss_winner === 1 ? form.value.team2_name : form.value.team1_name
})

const battingTeamIndex = computed(() => {
  if (!form.value.toss_winner || !form.value.toss_decision) return 1
  if (form.value.toss_decision === 'bat') return form.value.toss_winner
  return form.value.toss_winner === 1 ? 2 : 1
})

const battingPlayers = computed(() =>
  battingTeamIndex.value === 1 ? form.value.team1_players : form.value.team2_players
)
const bowlingPlayers = computed(() =>
  battingTeamIndex.value === 1 ? form.value.team2_players : form.value.team1_players
)

async function startMatch() {
  loading.value = true; error.value = ''
  try {
    const f = form.value
    let matchId
    let batTeamData
    let bowlTeamData

    if (!isTournamentMode.value) {
      const t1p = f.team1_players.map((n,i) => n || `Player ${i+1}`)
      const t2p = f.team2_players.map((n,i) => n || `Player ${i+1}`)
      const payload = {
        tournament_id: null,
        overs: f.overs,
        players_per_team: f.players_per_team,
        team1_name: f.team1_name,
        team2_name: f.team2_name,
        team1_players: t1p,
        team2_players: t2p,
        toss_winner: f.toss_winner,
        toss_decision: f.toss_decision
      }
      const { data: match } = await api.post('/matches/quick', payload)
      matchId = match.id
      const { data: t1 } = await api.get(`/teams/${match.team1.id}`)
      const { data: t2 } = await api.get(`/teams/${match.team2.id}`)
      batTeamData = battingTeamIndex.value === 1 ? t1 : t2
      bowlTeamData = battingTeamIndex.value === 1 ? t2 : t1
    } else {
      const { data: match } = await api.post('/matches', {
        tournament_id: f.tournament_id,
        overs: f.overs,
        players_per_team: f.players_per_team,
        team1_id: f.team1_id,
        team2_id: f.team2_id
      })
      matchId = match.id

      const tossWinnerId = f.toss_winner === 1 ? f.team1_id : f.team2_id
      await api.post(`/matches/${matchId}/toss`, {
        toss_winner_id: tossWinnerId,
        toss_decision: f.toss_decision
      })

      const t1 = activeTournament.value.teams.find(t => t.id === f.team1_id)
      const t2 = activeTournament.value.teams.find(t => t.id === f.team2_id)
      batTeamData = battingTeamIndex.value === 1 ? t1 : t2
      bowlTeamData = battingTeamIndex.value === 1 ? t2 : t1
    }

    const striker = batTeamData.players[f.striker_id]
    const nonStriker = batTeamData.players[f.non_striker_id]
    const bowler = bowlTeamData.players[f.bowler_id]
    
    await api.post(`/matches/${matchId}/start-innings`, {
      striker_id: striker.id,
      non_striker_id: nonStriker.id,
      bowler_id: bowler.id
    })
    
    router.push(`/match/${matchId}/live`)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/tournaments')
    tournaments.value = data
    
    const queryTid = router.currentRoute.value.query.tournament_id
    if (queryTid) {
      form.value.tournament_id = parseInt(queryTid)
      const t = tournaments.value.find(x => x.id === form.value.tournament_id)
      if (t) {
        form.value.overs = t.overs_per_match
        form.value.players_per_team = t.players_per_team
      }
    }
  } catch {}
})
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.step-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; border-top: 1px solid var(--border); padding-top: 1.25rem; }
.players-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.team-players-title { font-weight: 700; color: var(--primary); margin-bottom: 0.75rem; font-size: 0.95rem; }
.player-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
.player-num { width: 24px; font-size: 0.8rem; color: var(--text-muted); font-weight: 600; flex-shrink: 0; text-align: center; }
.toss-btns { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.5rem; }
.toss-team-btn {
  flex: 1; min-width: 120px; padding: 0.875rem 1.25rem;
  border: 2px solid var(--border); border-radius: var(--radius);
  background: var(--bg-card2); color: var(--text-dim);
  font-weight: 700; font-size: 0.95rem; transition: all 0.2s;
}
.toss-team-btn.selected { border-color: var(--primary); color: var(--primary); background: var(--primary-glow); }
.toss-team-btn:hover { border-color: var(--primary); }
.error-msg { color: var(--red); font-size: 0.875rem; margin-top: 0.75rem; padding: 0.75rem; background: var(--red-glow); border-radius: var(--radius-sm); }
@media (max-width: 600px) {
  .form-grid, .players-columns { grid-template-columns: 1fr; }
}
</style>
