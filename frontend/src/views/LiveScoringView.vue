<template>
  <div class="page">
    <div class="container live-container">

      <!-- Scoreboard Header -->
      <div class="scoreboard card">
        <div class="sb-top">
          <div class="sb-match-info">
            <span class="live-dot"></span>
            <span class="badge badge-red">LIVE</span>
            <span class="text-muted" style="font-size:0.8rem;margin-left:0.5rem">{{ state?.match?.overs }} overs</span>
          </div>
          <div class="sb-actions">
            <RouterLink :to="`/match/${matchId}/scorecard`" class="btn btn-ghost btn-sm">Scorecard</RouterLink>
          </div>
        </div>

        <div class="sb-scores" v-if="state">
          <div class="sb-team" :class="{ batting: true }">
            <div class="sb-team-name">{{ battingTeam?.name }}</div>
            <div class="score-big">{{ inn?.total_runs }}<span class="score-wkts">/{{ inn?.total_wickets }}</span></div>
            <div class="sb-overs text-muted">{{ oversDisplay }} overs</div>
          </div>
          <div class="sb-divider">
            <div class="vs-badge">VS</div>
            <div v-if="inn?.innings_number===2 && inn?.target" class="target-info">
              <div class="text-accent" style="font-size:0.8rem;font-weight:700">Target {{ inn.target }}</div>
              <div class="text-muted" style="font-size:0.75rem">Need {{ inn.target - inn.total_runs }} in {{ remainingBalls }} balls</div>
            </div>
          </div>
          <div class="sb-team">
            <div class="sb-team-name">{{ bowlingTeam?.name }}</div>
            <div v-if="inn?.innings_number===2" class="sb-prev-score text-dim">
              {{ prevInnings?.total_runs }}/{{ prevInnings?.total_wickets }} ({{ prevOversDisplay }})
            </div>
            <div class="rates">
              <div class="rate-item"><span class="text-muted">CRR</span> <span class="text-primary">{{ state.run_rate }}</span></div>
              <div v-if="state.required_rate" class="rate-item"><span class="text-muted">RRR</span> <span class="text-accent">{{ state.required_rate }}</span></div>
            </div>
          </div>
        </div>

        <!-- Current over balls -->
        <div class="over-balls" v-if="state?.current_over_events?.length">
          <span class="text-muted" style="font-size:0.8rem">This over:</span>
          <div class="balls-row">
            <div v-for="e in state.current_over_events" :key="e.id"
              class="ball-display"
              :class="ballClass(e)">
              {{ ballLabel(e) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Main scoring area -->
      <div class="scoring-layout">
        <!-- Left: Batsmen & Bowler -->
        <div class="batting-info">
          <div class="card" style="margin-bottom:1rem">
            <div class="section-title" style="margin-bottom:0.75rem">At the Crease</div>
            <div v-for="b in activeBatsmen" :key="b.player_id" class="batsman-row" :class="{ 'on-strike': b.is_on_strike }">
              <div class="batsman-name">
                <span v-if="b.is_on_strike" class="strike-marker">*</span>
                {{ b.player_name }}
              </div>
              <div class="batsman-stats">
                <span class="stat-chip">{{ b.runs }}<span class="text-muted">({{ b.balls_faced }})</span></span>
                <span class="stat-chip text-accent">4s: {{ b.fours }}</span>
                <span class="stat-chip text-green">6s: {{ b.sixes }}</span>
                <span class="text-dim" style="font-size:0.78rem">SR {{ b.strike_rate }}</span>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="section-title" style="margin-bottom:0.75rem">Bowling</div>
            <div v-for="b in currentBowler ? [currentBowler] : []" :key="b.player_id" class="batsman-row">
              <div class="batsman-name">{{ b.player_name }}</div>
              <div class="batsman-stats">
                <span class="stat-chip">{{ b.overs_display }} ov</span>
                <span class="stat-chip">{{ b.runs_conceded }} runs</span>
                <span class="stat-chip text-red">{{ b.wickets }}W</span>
                <span class="text-dim" style="font-size:0.78rem">Eco {{ b.economy_rate }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Scoring Controls -->
        <div class="scoring-controls card">
          <div class="section-title" style="margin-bottom:1rem">Record Delivery</div>

          <!-- Run buttons -->
          <div class="run-buttons">
            <button v-for="r in [0,1,2,3,4,6]" :key="r" class="run-btn" :class="`r${r}`" @click="quickRun(r)">{{ r }}</button>
            <button class="run-btn rwd" @click="openExtra('wide')">Wd</button>
            <button class="run-btn rnb" @click="openExtra('no_ball')">NB</button>
            <button class="run-btn rw" @click="openWicket">W</button>
          </div>

          <!-- Extras quick row -->
          <div class="extras-row">
            <button class="btn btn-ghost btn-sm" @click="openExtra('bye')">Bye</button>
            <button class="btn btn-ghost btn-sm" @click="openExtra('leg_bye')">Leg Bye</button>
            <button class="btn btn-ghost btn-sm" @click="undoBall" :disabled="!canUndo">Undo</button>
          </div>

          <!-- End of over: change bowler -->
          <div v-if="needNewBowler" class="change-bowler-box">
            <div class="section-title">Select Next Bowler</div>
            <select v-model.number="nextBowlerId" class="select" style="margin-bottom:0.75rem">
              <option value="">Choose bowler</option>
              <option v-for="p in bowlingTeamPlayers" :key="p.id" :value="p.id"
                :disabled="p.id === currentBowler?.player_id">{{ p.name }}</option>
            </select>
            <button class="btn btn-primary" @click="confirmNewBowler" :disabled="!nextBowlerId">Confirm Bowler</button>
          </div>

          <!-- New batsman needed -->
          <div v-if="needNewBatsman" class="change-bowler-box">
            <div class="section-title">Select Next Batsman</div>
            <select v-model.number="nextBatsmanId" class="select" style="margin-bottom:0.75rem">
              <option value="">Choose batsman</option>
              <option v-for="p in nextBatsmanList" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
            <button class="btn btn-primary" @click="confirmNewBatsman" :disabled="!nextBatsmanId">Send In</button>
          </div>

          <div v-if="store.error" class="error-msg">{{ store.error }}</div>
        </div>
      </div>

      <!-- Innings break / match over -->
      <div v-if="state?.match?.status === 'innings_break'" class="innings-break card">
        <h3>🔄 Innings Break</h3>
        <p class="text-dim">{{ bowlingTeam?.name }} needs {{ (inn?.total_runs || 0) + 1 }} to win.</p>
        <button class="btn btn-primary btn-lg" @click="startSecondInnings">Start 2nd Innings</button>
      </div>

      <div v-if="state?.match?.status === 'completed'" class="match-over card">
        <div style="font-size:2rem">🏆</div>
        <h3>Match Complete!</h3>
        <p class="text-green" style="font-size:1.1rem;font-weight:700">{{ state.match.result_summary }}</p>
        <RouterLink :to="`/match/${matchId}/scorecard`" class="btn btn-primary btn-lg" style="margin-top:1rem">View Scorecard</RouterLink>
      </div>
    </div>

    <!-- Extra/Wicket Modal -->
    <div v-if="modal.open" class="modal-overlay" @click.self="modal.open=false">
      <div class="modal card">
        <h3 class="section-title">{{ modal.title }}</h3>

        <div v-if="modal.type === 'wicket'">
          <div class="form-group" style="margin-bottom:1rem">
            <label class="form-label">Dismissed Batsman</label>
            <select v-model.number="modal.dismissed_id" class="select">
              <option v-for="b in activeBatsmen" :key="b.player_id" :value="b.player_id">{{ b.player_name }}</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom:1rem">
            <label class="form-label">Wicket Type</label>
            <div class="wicket-types">
              <button v-for="wt in wicketTypes" :key="wt.v"
                class="wicket-btn" :class="{ selected: modal.wicket_type === wt.v }"
                @click="modal.wicket_type = wt.v">{{ wt.l }}</button>
            </div>
          </div>
          <div v-if="['caught','stumped','run_out'].includes(modal.wicket_type)" class="form-group" style="margin-bottom:1rem">
            <label class="form-label">Fielder</label>
            <select v-model.number="modal.fielder_id" class="select">
              <option :value="null">None</option>
              <option v-for="p in bowlingTeamPlayers" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom:1rem">
            <label class="form-label">Runs Scored Off This Delivery</label>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
              <button v-for="r in [0,1,2,3,4,6]" :key="r"
                class="run-btn" style="width:44px;height:44px;font-size:1rem"
                :class="[`r${r}`, modal.runs_scored===r?'selected-run':'']"
                @click="modal.runs_scored=r">{{ r }}</button>
            </div>
          </div>
        </div>

        <div v-if="['wide','no_ball','bye','leg_bye'].includes(modal.type)">
          <div class="form-group" style="margin-bottom:1rem">
            <label class="form-label">Extra Runs</label>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
              <button v-for="r in [1,2,3,4,6]" :key="r"
                class="run-btn" :class="`r${r}`" style="width:44px;height:44px;font-size:1rem"
                @click="modal.extra_runs=r">
                <span :style="modal.extra_runs===r?'color:var(--primary)':''">{{ r }}</span>
              </button>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.5rem">
              <input type="number" v-model.number="modal.extra_runs" class="input" style="width:80px" min="1" />
              <span class="text-muted">runs</span>
            </div>
          </div>
          <div v-if="modal.type==='no_ball'" class="form-group" style="margin-bottom:1rem">
            <label class="form-label">Runs off Bat</label>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
              <button v-for="r in [0,1,2,3,4,6]" :key="r"
                class="run-btn" :class="`r${r}`" style="width:44px;height:44px;font-size:1rem"
                @click="modal.runs_scored=r">{{ r }}</button>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn btn-ghost" @click="modal.open=false">Cancel</button>
          <button class="btn btn-primary" @click="submitModal" :disabled="store.loading">
            <span v-if="store.loading" class="spinner" style="width:16px;height:16px;border-width:2px"></span>
            Confirm
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCricketStore } from '@/stores/cricket'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const store = useCricketStore()
const matchId = computed(() => route.params.id)

const state = computed(() => store.liveState)
const inn = computed(() => state.value?.innings)
const battingTeam = computed(() => {
  if (!state.value) return null
  const m = state.value.match
  const i = inn.value
  if (!i) return null
  return i.batting_team_id === m.team1_id ? m.team1 : m.team2
})
const bowlingTeam = computed(() => {
  if (!state.value) return null
  const m = state.value.match
  const i = inn.value
  if (!i) return null
  return i.bowling_team_id === m.team1_id ? m.team1 : m.team2
})

const canUndo = computed(() => {
  return !!state.value?.last_event
})
const activeBatsmen = computed(() => state.value?.batting_scores.filter(b => b.is_at_crease) || [])
const currentBowler = computed(() => state.value?.bowling_scores.find(b => b.is_current_bowler))
const oversDisplay = computed(() => {
  if (!inn.value) return '0.0'
  const b = inn.value.total_balls
  return `${Math.floor(b/6)}.${b%6}`
})
const remainingBalls = computed(() => {
  if (!state.value?.match || !inn.value) return 0
  return state.value.match.overs * 6 - inn.value.total_balls
})
const prevInnings = ref(null)
const prevOversDisplay = computed(() => {
  if (!prevInnings.value) return '0.0'
  const b = prevInnings.value.total_balls
  return `${Math.floor(b/6)}.${b%6}`
})

const needNewBowler = ref(false)
const nextBowlerId = ref('')
const bowlingTeamPlayers = ref([])
const needNewBatsman = ref(false)
const nextBatsmanId = ref('')

watch(() => inn.value?.bowling_team_id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadBowlingPlayers()
  }
}, { immediate: true })
const nextBatsmanList = ref([])

const modal = ref({ open: false, type: '', title: '', wicket_type: 'bowled', dismissed_id: null, fielder_id: null, runs_scored: 0, extra_runs: 1 })
const wicketTypes = [
  { v: 'bowled', l: 'Bowled' }, { v: 'caught', l: 'Caught' }, { v: 'lbw', l: 'LBW' },
  { v: 'run_out', l: 'Run Out' }, { v: 'stumped', l: 'Stumped' }, { v: 'hit_wicket', l: 'Hit Wicket' }
]

function ballClass(e) {
  if (e.is_wicket) return 'is-wicket'
  if (e.runs_scored === 6) return 'is-six'
  if (e.runs_scored === 4) return 'is-four'
  if (!e.is_legal) return 'is-extra'
  if (e.total_runs === 0) return 'is-dot'
  return ''
}
function ballLabel(e) {
  if (e.is_wicket) return `W${e.runs_scored > 0 ? '+' + e.runs_scored : ''}`
  if (e.extras_type === 'wide') return e.extras_runs > 1 ? `Wd+${e.extras_runs - 1}` : 'Wd'
  if (e.extras_type === 'no_ball') return `Nb+${e.runs_scored}`
  if (e.extras_type === 'bye') return `B+${e.extras_runs}`
  if (e.extras_type === 'leg_bye') return `Lb+${e.extras_runs}`
  return e.runs_scored
}

async function quickRun(runs) {
  if (!inn.value) return
  const striker = activeBatsmen.value.find(b => b.is_on_strike)
  const nonStriker = activeBatsmen.value.find(b => !b.is_on_strike)
  if (!striker || !nonStriker || !currentBowler.value) return
  await postBall({ striker_id: striker.player_id, non_striker_id: nonStriker.player_id, bowler_id: currentBowler.value.player_id, runs_scored: runs })
}

function openExtra(type) {
  modal.value = { open: true, type, title: type.replace('_',' ').toUpperCase(), wicket_type: 'bowled', dismissed_id: null, fielder_id: null, runs_scored: 0, extra_runs: 1 }
}
function openWicket() {
  const striker = activeBatsmen.value.find(b => b.is_on_strike)
  modal.value = { open: true, type: 'wicket', title: 'Wicket!', wicket_type: 'bowled', dismissed_id: striker?.player_id || null, fielder_id: null, runs_scored: 0, extra_runs: 0 }
}

async function submitModal() {
  const striker = activeBatsmen.value.find(b => b.is_on_strike)
  const nonStriker = activeBatsmen.value.find(b => !b.is_on_strike)
  if (!striker || !nonStriker || !currentBowler.value) return
  const m = modal.value
  const ball = {
    striker_id: striker.player_id,
    non_striker_id: nonStriker.player_id,
    bowler_id: currentBowler.value.player_id,
    runs_scored: m.type === 'wicket' ? m.runs_scored : (m.type === 'no_ball' ? m.runs_scored : 0),
    extras_type: m.type !== 'wicket' ? m.type : null,
    extras_runs: m.type !== 'wicket' ? m.extra_runs : 0,
    is_wicket: m.type === 'wicket',
    wicket_type: m.type === 'wicket' ? m.wicket_type : null,
    dismissed_player_id: m.type === 'wicket' ? m.dismissed_id : null,
    fielder_id: m.fielder_id || null
  }
  await postBall(ball)
  modal.value.open = false
}

async function postBall(ball) {
  if (!inn.value) return
  const prevBalls = inn.value.total_balls
  const result = await store.recordBall(inn.value.id, ball)
  if (!result) return
  const newBalls = result.innings?.total_balls || 0
  const endOfOver = ball.extras_type !== 'wide' && ball.extras_type !== 'no_ball' && newBalls % 6 === 0 && newBalls > prevBalls
  if (endOfOver && result.match?.status === 'live') {
    needNewBowler.value = true
    await loadBowlingPlayers()
  }
  if (ball.is_wicket && result.match?.status === 'live') {
    await loadNextBatsmen(result)
  }
}

async function loadBowlingPlayers() {
  try {
    const m = state.value?.match
    if (!m || !inn.value) return
    const bowlTeamId = inn.value.bowling_team_id
    const { data } = await api.get(`/teams/${bowlTeamId}`)
    bowlingTeamPlayers.value = data.players
  } catch {}
}

async function loadNextBatsmen(result) {
  try {
    const batTeamId = inn.value?.batting_team_id
    if (!batTeamId) return
    const { data } = await api.get(`/teams/${batTeamId}`)
    const usedIds = new Set((result.batting_scores || []).map(b => b.player_id))
    nextBatsmanList.value = data.players.filter(p => !usedIds.has(p.id))
    if (nextBatsmanList.value.length > 0) needNewBatsman.value = true
  } catch {}
}

async function confirmNewBowler() {
  if (!nextBowlerId.value || !inn.value) return
  await api.post(`/innings/${inn.value.id}/next-bowler`, null, { params: { bowler_id: nextBowlerId.value } })
  await store.fetchLive(matchId.value)
  needNewBowler.value = false; nextBowlerId.value = ''
}

async function confirmNewBatsman() {
  if (!nextBatsmanId.value || !inn.value) return
  const striker = activeBatsmen.value.find(b => b.is_on_strike)
  const onStrike = !striker
  await api.post(`/innings/${inn.value.id}/next-batsman`, null, { params: { player_id: nextBatsmanId.value, on_strike: onStrike } })
  await store.fetchLive(matchId.value)
  needNewBatsman.value = false; nextBatsmanId.value = ''
}

async function startSecondInnings() {
  try {
    const m = state.value?.match
    if (!m) return
    const bowlTeamId = inn.value?.bowling_team_id
    const { data: team } = await api.get(`/teams/${bowlTeamId}`)
    const batTeamId = inn.value?.batting_team_id
    const { data: bowlTeam } = await api.get(`/teams/${batTeamId}`)
    await api.post(`/matches/${m.id}/start-innings`, {
      striker_id: team.players[0].id,
      non_striker_id: team.players[1].id,
      bowler_id: bowlTeam.players[0].id
    })
    await store.fetchLive(matchId.value)
  } catch (e) { console.error(e) }
}

async function undoBall() {
  if (!inn.value) return
  if (!confirm('Are you sure you want to undo the last delivery?')) return
  try {
    await store.undoBall(inn.value.id)
    if (inn.value && inn.value.total_balls > 0 && inn.value.total_balls % 6 === 0) {
      needNewBowler.value = true
      await loadBowlingPlayers()
    } else {
      needNewBowler.value = false
    }
    needNewBatsman.value = false
  } catch (e) {
    console.error('Failed to undo', e)
  }
}

let pollInterval = null
onMounted(async () => {
  await store.fetchLive(matchId.value)
  if (inn.value?.innings_number === 2) {
    // load prev innings
    try {
      const { data } = await api.get(`/matches/${matchId.value}/scorecard`)
      prevInnings.value = data.innings_list[0]?.innings || null
    } catch {}
  }
  pollInterval = setInterval(() => store.fetchLive(matchId.value), 15000)
})
onUnmounted(() => clearInterval(pollInterval))
</script>

<style scoped>
.live-container { max-width: 960px; }
.scoreboard { margin-bottom: 1.25rem; }
.sb-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
.sb-match-info { display: flex; align-items: center; gap: 0.5rem; }
.sb-scores { display: grid; grid-template-columns: 1fr auto 1fr; gap: 1rem; align-items: center; margin-bottom: 1rem; }
.sb-team { }
.sb-team:last-child { text-align: right; }
.sb-team-name { font-size: 0.85rem; font-weight: 600; color: var(--text-dim); margin-bottom: 0.25rem; }
.score-wkts { font-size: 1.8rem; color: var(--text-muted); }
.sb-overs { font-size: 0.82rem; margin-top: 0.2rem; }
.sb-divider { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
.target-info { text-align: center; }
.rates { display: flex; gap: 1rem; margin-top: 0.5rem; }
.rate-item { font-size: 0.82rem; display: flex; gap: 0.3rem; align-items: center; }
.over-balls { display: flex; align-items: center; gap: 0.75rem; padding-top: 1rem; border-top: 1px solid var(--border); flex-wrap: wrap; }
.balls-row { display: flex; gap: 0.4rem; flex-wrap: wrap; }

.scoring-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.batsman-row { padding: 0.75rem 0; border-bottom: 1px solid var(--border); }
.batsman-row:last-child { border-bottom: none; }
.batsman-row.on-strike { background: var(--primary-glow); border-radius: var(--radius-sm); padding: 0.75rem; }
.batsman-name { font-weight: 700; margin-bottom: 0.3rem; }
.strike-marker { color: var(--primary); margin-right: 0.25rem; }
.batsman-stats { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; font-size: 0.82rem; }
.stat-chip { font-weight: 600; }

.run-buttons { display: grid; grid-template-columns: repeat(3,1fr); gap: 0.75rem; margin-bottom: 1rem; justify-items: center; }
.extras-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.change-bowler-box { padding: 1rem; background: var(--bg-card2); border-radius: var(--radius-sm); border: 1px solid var(--border-accent); margin-top: 1rem; }

.innings-break, .match-over { text-align: center; padding: 2.5rem; margin-top: 1.25rem; }
.innings-break h3, .match-over h3 { font-size: 1.4rem; margin: 0.75rem 0 0.5rem; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 1rem; }
.modal { width: 100%; max-width: 480px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem; border-top: 1px solid var(--border); padding-top: 1rem; }
.wicket-types { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
.wicket-btn { padding: 0.4rem 0.875rem; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg-card2); color: var(--text-dim); font-size: 0.82rem; font-weight: 600; transition: all 0.15s; }
.wicket-btn.selected { border-color: var(--red); color: var(--red); background: var(--red-glow); }
.error-msg { color: var(--red); font-size: 0.85rem; margin-top: 0.75rem; padding: 0.75rem; background: var(--red-glow); border-radius: var(--radius-sm); }

@media (max-width: 768px) {
  .scoring-layout { grid-template-columns: 1fr; }
  .sb-scores { grid-template-columns: 1fr auto 1fr; }
  .score-big { font-size: 2.5rem; }
  .run-buttons { grid-template-columns: repeat(3,1fr); gap: 0.5rem; }
}
</style>
