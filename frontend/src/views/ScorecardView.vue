<template>
  <div class="page">
    <div class="container" style="max-width:900px">
      <div class="page-header">
        <RouterLink :to="`/match/${matchId}/live`" class="btn btn-ghost btn-sm">← Live</RouterLink>
        <h1 class="page-title">Scorecard</h1>
        <RouterLink to="/" class="btn btn-ghost btn-sm">Home</RouterLink>
      </div>

      <div v-if="loading" class="spinner-wrap"><div class="spinner"></div></div>

      <div v-else-if="scorecard">
        <!-- Match result banner -->
        <div class="result-banner card" :class="scorecard.match.status === 'completed' ? 'completed' : 'live'">
          <div class="result-teams">
            <span class="result-team">{{ scorecard.match.team1.name }}</span>
            <span class="result-vs">vs</span>
            <span class="result-team">{{ scorecard.match.team2.name }}</span>
          </div>
          <div v-if="scorecard.match.result_summary" class="result-text text-green">
            {{ scorecard.match.result_summary }}
          </div>
          <div v-else class="badge badge-red"><span class="live-dot"></span>Live</div>
        </div>

        <!-- Each innings -->
        <div v-for="inn in scorecard.innings_list" :key="inn.innings.id" class="innings-section">
          <div class="innings-header">
            <h2>{{ inn.batting_team.name }} Innings</h2>
            <div class="innings-summary">
              <span class="score-medium">{{ inn.innings.total_runs }}/{{ inn.innings.total_wickets }}</span>
              <span class="text-muted">({{ inn.overs_display }} ov)</span>
              <span v-if="inn.innings.target" class="badge badge-accent">Target {{ inn.innings.target }}</span>
            </div>
          </div>

          <!-- Batting table -->
          <div class="card table-card">
            <div class="table-title">Batting</div>
            <div class="table-wrap">
              <table class="table">
                <thead>
                  <tr>
                    <th>Batsman</th>
                    <th class="hide-mobile">Dismissal</th>
                    <th style="text-align:right">R</th>
                    <th style="text-align:right">B</th>
                    <th style="text-align:right">4s</th>
                    <th style="text-align:right">6s</th>
                    <th style="text-align:right">SR</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="b in inn.batting_scores" :key="b.id" :class="{ 'not-out': !b.is_out && b.balls_faced > 0 }">
                    <td>
                      <span class="player-name-cell">{{ b.player_name }}</span>
                      <span v-if="b.is_on_strike" class="badge badge-primary" style="margin-left:6px;font-size:0.65rem">*</span>
                      <span v-if="!b.is_out && b.balls_faced > 0" class="text-green" style="font-size:0.75rem;margin-left:6px">not out</span>
                    </td>
                    <td class="hide-mobile text-muted" style="font-size:0.82rem">{{ b.dismissal_text || (b.balls_faced === 0 ? 'dnb' : 'not out') }}</td>
                    <td style="text-align:right;font-weight:700">{{ b.runs }}</td>
                    <td style="text-align:right;color:var(--text-muted)">{{ b.balls_faced }}</td>
                    <td style="text-align:right;color:var(--accent)">{{ b.fours }}</td>
                    <td style="text-align:right;color:var(--green)">{{ b.sixes }}</td>
                    <td style="text-align:right;color:var(--text-dim)">{{ b.strike_rate }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="extras-row-table">
                    <td colspan="2"><span class="text-muted">Extras</span></td>
                    <td colspan="5" style="text-align:right;color:var(--text-dim)">{{ inn.innings.total_extras }}</td>
                  </tr>
                  <tr class="total-row">
                    <td colspan="2"><strong>Total</strong></td>
                    <td colspan="5" style="text-align:right"><strong>{{ inn.innings.total_runs }}/{{ inn.innings.total_wickets }}</strong> ({{ inn.overs_display }} ov)</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <!-- Bowling table -->
          <div class="card table-card" style="margin-top:1rem">
            <div class="table-title">Bowling</div>
            <div class="table-wrap">
              <table class="table">
                <thead>
                  <tr>
                    <th>Bowler</th>
                    <th style="text-align:right">O</th>
                    <th style="text-align:right">M</th>
                    <th style="text-align:right">R</th>
                    <th style="text-align:right">W</th>
                    <th style="text-align:right">Eco</th>
                    <th style="text-align:right" class="hide-mobile">Wd</th>
                    <th style="text-align:right" class="hide-mobile">NB</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="b in inn.bowling_scores" :key="b.id">
                    <td class="player-name-cell">{{ b.player_name }}</td>
                    <td style="text-align:right">{{ b.overs_display }}</td>
                    <td style="text-align:right;color:var(--text-muted)">{{ b.maidens }}</td>
                    <td style="text-align:right">{{ b.runs_conceded }}</td>
                    <td style="text-align:right;font-weight:700;color:var(--red)">{{ b.wickets }}</td>
                    <td style="text-align:right;color:var(--text-dim)">{{ b.economy_rate }}</td>
                    <td style="text-align:right;color:var(--text-muted)" class="hide-mobile">{{ b.wides }}</td>
                    <td style="text-align:right;color:var(--text-muted)" class="hide-mobile">{{ b.no_balls }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
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
const matchId = computed(() => route.params.id)
const scorecard = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get(`/matches/${matchId.value}/scorecard`)
    scorecard.value = data
  } finally { loading.value = false }
})
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
.result-banner { text-align: center; padding: 1.5rem; margin-bottom: 1.5rem; }
.result-banner.completed { border-color: var(--green); }
.result-banner.live { border-color: var(--red); }
.result-teams { display: flex; align-items: center; justify-content: center; gap: 1rem; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
.result-vs { color: var(--text-muted); font-size: 0.85rem; }
.result-text { font-size: 1rem; font-weight: 700; margin-top: 0.5rem; }
.innings-section { margin-bottom: 2rem; }
.innings-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem; }
.innings-header h2 { font-size: 1.15rem; font-weight: 700; }
.innings-summary { display: flex; align-items: center; gap: 0.75rem; }
.table-card { overflow: hidden; }
.table-title { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 0.75rem; }
.table-wrap { overflow-x: auto; }
.not-out td:first-child { color: var(--green); }
.total-row td { border-top: 1px solid var(--border); padding-top: 0.75rem; }
.player-name-cell { font-weight: 600; }
</style>
