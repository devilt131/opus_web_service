<template>
  <div class="auth">
    <div class="auth-card">
      <h2>Register</h2>
      <input v-model="username" type="text" placeholder="Username" />
      <input v-model="email" type="email" placeholder="Email" />
      <input v-model="password" type="password" placeholder="Password (min 6)" />
      <button @click="register">Create account</button>
      <p v-if="error" class="error">{{ error }}</p>
      <p class="link"><router-link to="/login">Already have account?</router-link></p>
    </div>
  </div>
</template>

<script>
import api, { formatApiError } from '../api'

export default {
  data() { return { username: '', email: '', password: '', error: '' } },
  methods: {
    async register() {
      this.error = ''
      try {
        await api.post('/register', {
          username: this.username,
          email: this.email,
          password: this.password
        })
        this.$router.push('/login')
      } catch (err) {
        this.error = formatApiError(err, 'Registration failed')
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
