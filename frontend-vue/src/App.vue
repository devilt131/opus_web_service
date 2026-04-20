<template>
  <div class="app">
    <nav class="nav">
      <div class="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span>Opus</span>
      </div>
      <div class="nav-links">
        <router-link to="/">Анализ</router-link>
        <router-link v-if="!token" to="/login">Вход</router-link>
        <router-link v-if="!token" to="/register">Регистрация</router-link>
        <router-link v-if="token" to="/profile">{{ username || 'Профиль' }}</router-link>
        <router-link v-if="token" to="/settings">Настройки</router-link>
        <button v-if="token" @click="logout" class="logout">Выйти</button>
      </div>
    </nav>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return {
      token: localStorage.getItem('token'),
      username: localStorage.getItem('username')
    }
  },
  methods: {
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      this.token = null
      this.username = null
      this.$router.push('/login')
    }
  },
  mounted() {
    window.addEventListener('storage', () => {
      this.token = localStorage.getItem('token')
      this.username = localStorage.getItem('username')
    })
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0a; color: #e5e5e5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
.app { min-height: 100vh; }
.nav { background: #111111; border-bottom: 1px solid #1f1f1f; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }
.logo { display: flex; align-items: center; gap: 0.5rem; font-size: 1.25rem; font-weight: 500; color: #e5e5e5; }
.nav-links { display: flex; gap: 1.5rem; align-items: center; }
.nav-links a { color: #8b8b8b; text-decoration: none; font-size: 0.875rem; transition: color 0.2s; }
.nav-links a:hover { color: #e5e5e5; }
.nav-links a.router-link-active { color: #1e6f9f; }
.logout { background: none; border: none; color: #8b8b8b; cursor: pointer; font-size: 0.875rem; }
.logout:hover { color: #e5e5e5; }
.main { max-width: 800px; margin: 0 auto; padding: 2rem; }
</style>
