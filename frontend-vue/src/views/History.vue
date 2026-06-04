<template>
  <div class="history">
    <h1 class="title">History</h1>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="loading" class="loader">
      <div class="spinner"></div>
    </div>

    <div v-else-if="items.length === 0" class="empty-state">
      <p>No analyses yet</p>
      <router-link to="/" class="btn-primary">Start analysis</router-link>
    </div>

    <div v-else class="history-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="history-item"
        @click="selectItem(item)"
      >
        <div class="item-header">
          <div class="item-title">{{ item.title }}</div>
          <div class="item-date">{{ formatDate(item.date) }}</div>
        </div>
        <div class="item-preview">{{ item.preview }}</div>
        <div class="item-summary">{{ item.summary }}</div>
      </div>
    </div>

    <div class="modal" v-if="selected" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ selected.title }}</h2>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="result-card">
            <h3>Summary</h3>
            <p>{{ selected.summary }}</p>
          </div>
          <div class="result-card">
            <h3>Preview</h3>
            <p>{{ selected.preview }}</p>
          </div>
          <div class="result-card">
            <h3>Date</h3>
            <p>{{ formatDate(selected.date) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api, { formatApiError } from '../api'

export default {
  data() {
    return {
      items: [],
      loading: true,
      selected: null,
      error: ''
    }
  },
  async mounted() {
    await this.fetchHistory()
  },
  methods: {
    async fetchHistory() {
      this.error = ''
      try {
        const res = await api.get('/history')
        this.items = Array.isArray(res.data) ? res.data : []
      } catch (err) {
        this.error = formatApiError(err, 'Failed to load history')
        this.items = []
      } finally {
        this.loading = false
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    },
    selectItem(item) {
      this.selected = item
    },
    closeModal() {
      this.selected = null
    }
  }
}
</script>

<style scoped>
.history {
  max-width: 800px;
  margin: 0 auto;
}

.title {
  font-size: 28px;
  font-weight: 400;
  letter-spacing: -0.5px;
  margin-bottom: 32px;
}

.error {
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid #991b1b;
  color: #fca5a5;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 8px;
}

.empty-state p {
  color: #8b8b8b;
  margin-bottom: 20px;
}

.btn-primary {
  display: inline-block;
  background: #1e6f9f;
  color: white;
  text-decoration: none;
  padding: 8px 24px;
  border-radius: 6px;
  font-size: 14px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.history-item:hover {
  border-color: #1e6f9f;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-title {
  font-weight: 500;
  font-size: 16px;
}

.item-date {
  color: #5a5a5a;
  font-size: 12px;
}

.item-preview {
  color: #8b8b8b;
  font-size: 13px;
  margin-bottom: 8px;
}

.item-summary {
  font-size: 13px;
  line-height: 1.4;
}

.loader {
  display: flex;
  justify-content: center;
  padding: 60px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 2px solid #2a2a2a;
  border-top-color: #1e6f9f;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h2 {
  font-size: 20px;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  color: #8b8b8b;
  font-size: 28px;
  cursor: pointer;
}

.modal-body {
  padding: 20px 24px;
}

.result-card {
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.result-card h3 {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #5a5a5a;
  margin-bottom: 8px;
}
</style>
