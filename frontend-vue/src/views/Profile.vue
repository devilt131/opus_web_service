<template>
  <div>
    <h1 class="title">Profile</h1>
    <div v-if="loading" class="loader"></div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="card">
      <div class="avatar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </div>
      <div class="field"><label>Username</label><div>{{ profile.username }}</div></div>
      <div class="field"><label>Email</label><div>{{ profile.email }}</div></div>
      <div class="field"><label>Registered</label><div>{{ formattedDate }}</div></div>
    </div>
  </div>
</template>

<script>
import api, { formatApiError } from '../api'

export default {
  data() { return { profile: null, loading: true, error: '' } },
  computed: {
    formattedDate() {
      return this.profile?.created_at
        ? new Date(this.profile.created_at).toLocaleDateString('en-US')
        : ''
    }
  },
  async mounted() {
    try {
      const res = await api.get('/profile')
      this.profile = res.data
    } catch (err) {
      this.error = formatApiError(err, 'Failed to load profile')
    } finally {
      this.loading = false
    }
  }
}
</script>

<style scoped>
.title { font-size: 28px; font-weight: 400; margin-bottom: 24px; }
.card { background: #111; border: 1px solid #1f1f1f; border-radius: 12px; padding: 2rem; }
.avatar { display: flex; justify-content: center; margin-bottom: 1.5rem; }
.avatar svg { width: 80px; height: 80px; color: #8b8b8b; }
.field { margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #1f1f1f; }
.field label { display: block; font-size: 0.75rem; text-transform: uppercase; color: #8b8b8b; margin-bottom: 0.25rem; }
.field div { font-size: 1.125rem; }
.loader { width: 32px; height: 32px; margin: 2rem auto; border: 2px solid #1f1f1f; border-top-color: #1e6f9f; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.error { background: rgba(220,38,38,0.2); border: 1px solid #991b1b; color: #fca5a5; padding: 0.75rem; border-radius: 8px; text-align: center; }
</style>
