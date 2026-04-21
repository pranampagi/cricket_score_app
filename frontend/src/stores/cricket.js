import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useCricketStore = defineStore('cricket', () => {
  const liveState = ref(null)
  const currentMatch = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchLive(matchId) {
    loading.value = true
    try {
      const { data } = await api.get(`/matches/${matchId}/live`)
      liveState.value = data
      currentMatch.value = data.match
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function recordBall(inningsId, ballData) {
    loading.value = true
    try {
      const { data } = await api.post(`/innings/${inningsId}/ball`, ballData)
      liveState.value = data
      currentMatch.value = data.match
      return data
    } catch (e) {
      error.value = e.response?.data?.detail || e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  function reset() {
    liveState.value = null
    currentMatch.value = null
    error.value = null
  }

  return { liveState, currentMatch, loading, error, fetchLive, recordBall, reset }
})
