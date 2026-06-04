<template>
  <div class="analyze">
    <h1 class="title">Text Analysis</h1>

    <div class="drop-zone" @dragover.prevent @drop.prevent="handleDrop">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
      <p>Drop file here or <button class="browse-btn" @click="openFile">browse</button></p>
      <small>TXT, PDF, DOCX</small>
      <input ref="fileInput" type="file" @change="handleFile" style="display:none" accept=".txt,.pdf,.docx" />
    </div>

    <textarea
      v-model="text"
      class="text-input"
      placeholder="Paste your text here (min 10 characters)..."
      rows="12"
    ></textarea>

    <textarea
      v-model="refText"
      class="text-input ref-input"
      placeholder="Reference text for plagiarism check (optional)..."
      rows="4"
    ></textarea>

    <div class="action-bar">
      <span class="counter">{{ text.length }} characters</span>
      <button class="btn-primary" @click="analyze" :disabled="loading">
        {{ loading ? 'Analyzing...' : 'Analyze' }}
      </button>
    </div>

    <div v-if="loading" class="loader">
      <div class="spinner"></div>
      <p>Processing...</p>
    </div>

    <div v-if="result" class="results">
      <div class="result-card">
        <h3>Title</h3>
        <p class="title-text">{{ result.title }}</p>
      </div>

      <div class="result-card">
        <h3>Summary</h3>
        <p>{{ result.summary }}</p>
        <div class="badge">Compressed {{ result.compression }}%</div>
      </div>

      <div class="result-card">
        <h3>Plan</h3>
        <div class="plan" v-html="formattedPlan"></div>
      </div>

      <div class="result-card">
        <h3>Keywords</h3>
        <div class="tags">
          <span v-for="k in result.keywords" :key="k.word" class="tag">
            {{ k.word }}
            <span class="tag-freq">({{ k.freq }})</span>
            <span v-if="k.score != null" class="tag-score">{{ formatScore(k.score) }}</span>
          </span>
        </div>
      </div>

      <div class="result-card">
        <h3>Statistics</h3>
        <div class="stats-grid">
          <div>Characters: {{ result.stats.chars }}</div>
          <div>Without spaces: {{ result.stats.chars_no_space }}</div>
          <div>Words: {{ result.stats.words }}</div>
          <div>Sentences: {{ result.stats.sentences }}</div>
          <div>Unique words: {{ result.stats.unique }}</div>
          <div>Avg word length: {{ result.stats.avg_w_len }}</div>
          <div>Avg sentence length: {{ result.stats.avg_s_len }}</div>
        </div>
      </div>

      <div class="result-card" v-if="hasEntities">
        <h3>Named Entities</h3>
        <div v-if="entities.persons.length" class="entity-group">
          <span class="entity-label">Persons:</span>
          <span class="entity-tag" v-for="p in entities.persons" :key="p.text">{{ p.text }}</span>
        </div>
        <div v-if="entities.orgs.length" class="entity-group">
          <span class="entity-label">Organizations:</span>
          <span class="entity-tag" v-for="o in entities.orgs" :key="o.text">{{ o.text }}</span>
        </div>
        <div v-if="entities.locs.length" class="entity-group">
          <span class="entity-label">Locations:</span>
          <span class="entity-tag" v-for="l in entities.locs" :key="l.text">{{ l.text }}</span>
        </div>
        <div v-if="entities.dates.length" class="entity-group">
          <span class="entity-label">Dates:</span>
          <span class="entity-tag" v-for="d in entities.dates" :key="d.text">{{ d.text }}</span>
        </div>
      </div>

      <div class="result-card" v-if="hasPlagiarism">
        <h3>Plagiarism Check</h3>
        <div class="plag-stats">
          <div>Uniqueness: <strong>{{ result.plagiarism.uniqueness }}%</strong></div>
          <div>Similarity: <strong>{{ result.plagiarism.similarity }}</strong></div>
          <div v-if="result.plagiarism.common?.length">Common words: {{ result.plagiarism.common.join(', ') }}</div>
        </div>
      </div>

      <div class="export-bar">
        <button class="btn-secondary" @click="exportTxt" :disabled="exporting">
          {{ exporting === 'txt' ? 'Exporting...' : 'Export TXT' }}
        </button>
        <button class="btn-secondary" @click="exportJson" :disabled="exporting">
          {{ exporting === 'json' ? 'Exporting...' : 'Export JSON' }}
        </button>
        <button class="btn-secondary" @click="exportPdf" :disabled="exporting">
          {{ exporting === 'pdf' ? 'Exporting...' : 'Export PDF' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
import api, { formatApiError } from '../api'

export default {
  data() {
    return {
      text: '',
      refText: '',
      loading: false,
      exporting: null,
      result: null,
      error: ''
    }
  },
  computed: {
    formattedPlan() {
      if (!this.result?.plan) return ''
      return this.result.plan.replace(/\n/g, '<br>')
    },
    entities() {
      return this.result?.entities || { persons: [], orgs: [], locs: [], dates: [] }
    },
    hasEntities() {
      const e = this.entities
      return e.persons.length || e.orgs.length || e.locs.length || e.dates.length
    },
    hasPlagiarism() {
      return this.result?.plagiarism && this.result.plagiarism.uniqueness !== undefined
    }
  },
  methods: {
    analyzePayload() {
      const payload = { text: this.text }
      if (this.refText.trim()) {
        payload.ref_text = this.refText.trim()
      }
      return payload
    },
    exportPayload() {
      const payload = this.analyzePayload()
      if (this.result) {
        payload.result = this.result
      }
      return payload
    },
    openFile() {
      this.$refs.fileInput.click()
    },
    async readTxtFile(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsText(file)
      })
    },
    formatScore(score) {
      return `${(score * 100).toFixed(1)}%`
    },
    appendRefText(form) {
      if (this.refText.trim()) {
        form.append('ref_text', this.refText.trim())
      }
    },
    async uploadFile(file) {
      const form = new FormData()
      form.append('file', file)
      this.appendRefText(form)
      this.loading = true
      this.error = ''
      this.result = null
      try {
        if (file.name.toLowerCase().endsWith('.txt')) {
          this.text = await this.readTxtFile(file)
        }
        const res = await api.post('/upload', form)
        this.result = res.data
      } catch (err) {
        this.error = formatApiError(err, 'upload failed')
      } finally {
        this.loading = false
      }
    },
    async handleFile(e) {
      const file = e.target.files[0]
      if (!file) return
      await this.uploadFile(file)
      this.$refs.fileInput.value = ''
    },
    async handleDrop(e) {
      const file = e.dataTransfer.files[0]
      if (!file) return
      await this.uploadFile(file)
    },
    async analyze() {
      const trimmed = this.text.trim()
      if (!trimmed) {
        this.error = 'Enter text to analyze'
        return
      }
      if (trimmed.length < 10) {
        this.error = 'Text must be at least 10 characters'
        return
      }
      this.loading = true
      this.error = ''
      this.result = null
      try {
        const res = await api.post('/analyze', this.analyzePayload())
        this.result = res.data
      } catch (err) {
        this.error = formatApiError(err, 'analysis failed')
      } finally {
        this.loading = false
      }
    },
    async runExport(format, filename) {
      if (!this.result) {
        this.error = 'Run analysis first before export'
        return
      }
      if (!this.text.trim()) {
        this.error = 'No text to export'
        return
      }
      this.exporting = format
      this.error = ''
      try {
        const res = await api.post(`/export/${format}`, this.exportPayload(), { responseType: 'blob' })
        this.downloadBlob(res.data, filename)
      } catch (err) {
        this.error = formatApiError(err, 'export failed')
      } finally {
        this.exporting = null
      }
    },
    exportTxt() {
      return this.runExport('txt', 'opus_report.txt')
    },
    exportJson() {
      return this.runExport('json', 'opus_report.json')
    },
    exportPdf() {
      return this.runExport('pdf', 'opus_report.pdf')
    },
    downloadBlob(blob, name) {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = name
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.analyze {
  max-width: 900px;
  margin: 0 auto;
}

.title {
  font-size: 28px;
  font-weight: 400;
  letter-spacing: -0.5px;
  margin-bottom: 32px;
}

.drop-zone {
  border: 2px dashed #2a2a2a;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  margin-bottom: 20px;
  transition: all 0.2s;
}

.drop-zone svg {
  color: #5a5a5a;
  margin-bottom: 8px;
}

.browse-btn {
  background: none;
  border: none;
  color: #1e6f9f;
  cursor: pointer;
  font-size: 14px;
}

.browse-btn:hover {
  text-decoration: underline;
}

.drop-zone small {
  display: block;
  color: #5a5a5a;
  font-size: 12px;
  margin-top: 8px;
}

.text-input {
  width: 100%;
  padding: 16px;
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  color: #e5e5e5;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  margin-bottom: 12px;
}

.ref-input {
  margin-bottom: 0;
}

.text-input:focus {
  outline: none;
  border-color: #1e6f9f;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.counter {
  color: #5a5a5a;
  font-size: 12px;
}

.btn-primary {
  background: #1e6f9f;
  border: none;
  color: white;
  padding: 8px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-primary:hover:not(:disabled) {
  background: #155a82;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #e5e5e5;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.btn-secondary:hover:not(:disabled) {
  background: #2a2a2a;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
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

.loader p {
  margin-top: 12px;
  color: #8b8b8b;
  font-size: 14px;
}

.results {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  background: #111111;
  border: 1px solid #1f1f1f;
  border-radius: 8px;
  padding: 20px;
}

.result-card h3 {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #5a5a5a;
  margin-bottom: 12px;
}

.title-text {
  font-size: 20px;
  font-weight: 500;
  letter-spacing: -0.3px;
}

.badge {
  display: inline-block;
  background: #1a1a1a;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #1e6f9f;
  margin-top: 12px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 13px;
}

.tag-freq {
  color: #5a5a5a;
  font-size: 11px;
  margin-left: 4px;
}

.plan {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.tag-score {
  color: #1e6f9f;
  font-size: 11px;
  margin-left: 4px;
}

.entity-group {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.entity-label {
  color: #5a5a5a;
  font-size: 12px;
  min-width: 100px;
}

.entity-tag {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.plag-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plag-stats strong {
  color: #1e6f9f;
}

.export-bar {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.error {
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid #991b1b;
  color: #fca5a5;
  padding: 12px;
  border-radius: 8px;
  margin-top: 16px;
}
</style>