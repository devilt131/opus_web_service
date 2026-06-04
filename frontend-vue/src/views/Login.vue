<template>
  <div class="auth">
    <div class="auth-card">
      <h2>Login</h2>
      <input v-model="username" type="text" placeholder="Username" />
      <input v-model="password" type="password" placeholder="Password" />
      <button @click="login">Sign in</button>
      <p v-if="error" class="error">{{ error }}</p>
      <p class="link"><router-link to="/register">Create account</router-link></p>
    </div>
  </div>
</template>

<script>
import api, { formatApiError } from '../api'

export default {
  data() { return { username: '', password: '', error: '' } },
  methods: {
    async login() {
      this.error = ''
      try {
        const res = await api.post('/login', { username: this.username, password: this.password })
        localStorage.setItem('token', res.data.access_token)
        this.$router.push('/')
      } catch (err) {
        this.error = formatApiError(err, 'Invalid credentials')
      }
    }
  }
}
</script>

<style scoped>
.auth {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
}
.auth-card {
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 12px;
  padding: 32px;
  width: 360px;
}
h2 {
  margin-bottom: 24px;
  font-weight: 400;
}
input {
  width: 100%;
  padding: 10px;
  margin-bottom: 16px;
  background: #0a0a0a;
  border: 1px solid #1f1f1f;
  border-radius: 6px;
  color: #e5e5e5;
}
button {
  width: 100%;
  padding: 10px;
  background: #1e6f9f;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.error {
  color: #f87171;
  margin-top: 12px;
  font-size: 13px;
}
.link {
  margin-top: 16px;
  text-align: center;
}
.link a {
  color: #1e6f9f;
  text-decoration: none;
}
</style>
