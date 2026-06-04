<template>
  <div class="app">
    <nav class="nav">
      <div class="logo">Opus</div>
      <div class="nav-links">
        <router-link to="/">Analyze</router-link>
        <router-link v-if="isLoggedIn" to="/history">History</router-link>
        <router-link v-if="isLoggedIn" to="/profile">Profile</router-link>
        <router-link v-if="isLoggedIn" to="/settings">Settings</router-link>
        <router-link v-if="!isLoggedIn" to="/login">Login</router-link>
        <router-link v-if="!isLoggedIn" to="/register">Register</router-link>
        <button v-if="isLoggedIn" class="logout-btn" @click="logout">Logout</button>
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
    return { token: localStorage.getItem('token') }
  },
  computed: {
    isLoggedIn() {
      return !!this.token
    }
  },
  mounted() {
    window.addEventListener('storage', this.syncToken)
    this._unwatch = this.$watch(
      () => this.$route.fullPath,
      () => this.syncToken()
    )
  },
  beforeUnmount() {
    window.removeEventListener('storage', this.syncToken)
    if (this._unwatch) this._unwatch()
  },
  methods: {
    syncToken() {
      this.token = localStorage.getItem('token')
    },
    logout() {
      localStorage.removeItem('token')
      this.token = null
      this.$router.push('/login')
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #0a0a0a;
  color: #e5e5e5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.5;
}

.app {
  min-height: 100vh;
}

.nav {
  background: #111111;
  border-bottom: 1px solid #1f1f1f;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #1e6f9f;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-links a {
  color: #8b8b8b;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: #e5e5e5;
}

.nav-links a.router-link-active {
  color: #1e6f9f;
}

.logout-btn {
  background: none;
  border: 1px solid #2a2a2a;
  color: #8b8b8b;
  padding: 4px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.logout-btn:hover {
  color: #e5e5e5;
  border-color: #1e6f9f;
}

.main {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 24px;
}
</style>
