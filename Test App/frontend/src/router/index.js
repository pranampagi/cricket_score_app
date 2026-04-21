import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/match/new', name: 'new-match', component: () => import('@/views/NewMatchView.vue') },
  { path: '/match/:id/live', name: 'live', component: () => import('@/views/LiveScoringView.vue') },
  { path: '/match/:id/scorecard', name: 'scorecard', component: () => import('@/views/ScorecardView.vue') },
  { path: '/tournaments', name: 'tournaments', component: () => import('@/views/TournamentsView.vue') },
  { path: '/tournaments/new', name: 'new-tournament', component: () => import('@/views/NewTournamentView.vue') },
  { path: '/tournaments/:id', name: 'tournament-detail', component: () => import('@/views/TournamentDetailView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
