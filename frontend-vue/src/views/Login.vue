<template>
  <div class="login">
    <div class="card">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <h1>Вход в Opus</h1>
      <div v-if="error" class="error">{{ error }}</div>
      <form @submit.prevent="handleLogin">
        <input type="text" v-model="username" placeholder="Логин" required />
        <input type="password" v-model="password" placeholder="Пароль" required />
        <button :disabled="loading">{{ loading ? 'Вход...' : 'Войти' }}</button>
      </form>
      <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data() {
    return {
      username: '',
      password: '',
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = ''
      
      try {
        const res = await axios.post('http://localhost:8000/login', {
          username: this.username,
          password: this.password
        })
        localStorage.setItem('token', res.data.access_token)
        localStorage.setItem('username', res.data.username)
        window.dispatchEvent(new Event('storage'))
        this.$router.push('/')
      } catch (err) {
        const detail = err.response?.data?.detail
        
        if (Array.isArray(detail)) {
          this.error = detail.map(e => e.msg).join(', ')
        } else if (typeof detail === 'string') {
          this.error = detail
        } else {
          this.error = 'Ошибка входа'
        }
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
}
.card {
  background: var(--surface-dark);
  border: 1px solid var(--border-dark);
  border-radius: 12px;
  padding: 2rem;
  width: 400px;
  text-align: center;
}
body.light .card {
  background: var(--surface-light);
  border: 1px solid var(--border-light);
}
.icon {
  width: 48px;
  height: 48px;
  color: #1e6f9f;
  margin-bottom: 1rem;
}
h1 {
  font-weight: 300;
  margin-bottom: 1.5rem;
  color: var(--text-dark);
}
body.light h1 {
  color: var(--text-light);
}
input {
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 1rem;
  background: #0a0a0a;
  border: 1px solid var(--border-dark);
  border-radius: 6px;
  color: var(--text-dark);
}
body.light input {
  background: #ffffff;
  border: 1px solid var(--border-light);
  color: var(--text-light);
}
input:focus {
  outline: none;
  border-color: #1e6f9f;
}
button {
  width: 100%;
  padding: 0.75rem;
  background: #1e6f9f;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
}
.error {
  background: rgba(220, 38, 38, 0.2);
  border: 1px solid #991b1b;
  color: #fca5a5;
  padding: 0.5rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}
p {
  margin-top: 1rem;
  color: #8b8b8b;
  font-size: 0.875rem;
}
a {
  color: #1e6f9f;
  text-decoration: none;
}
</style>