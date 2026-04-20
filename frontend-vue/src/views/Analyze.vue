<template>
  <div>
    <h1>Анализ текста</h1>
    
    <div class="input-area">
      <textarea 
        v-model="text" 
        placeholder="Введите текст для анализа..." 
        rows="10"
      ></textarea>
      
      <div class="info">
        <span>{{ text.length }} символов | {{ wordCount }} слов</span>
        <button @click="handleAnalyze" :disabled="loading">
          {{ loading ? 'Анализ...' : 'Анализировать' }}
        </button>
      </div>
      
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="loading" class="loader"></div>

    <div v-if="result" class="results">
      
      <div class="card">
        <h3>Заголовок</h3>
        <p>{{ result.title }}</p>
      </div>

      <div class="card">
        <h3>Краткое содержание</h3>
        <p>{{ result.summary }}</p>
        <div v-if="result.compression" class="compression">
          Сжато на {{ result.compression }}%
        </div>
      </div>

      <div class="card">
        <h3>Тональность</h3>
        <p :class="sentimentClass">{{ result.sentiment.sentiment }}</p>
        <div class="sentiment-stats">
          <span>Позитивных: {{ result.sentiment.positive_words }}</span>
          <span>Негативных: {{ result.sentiment.negative_words }}</span>
          <span>Уверенность: {{ Math.round(result.sentiment.confidence * 100) }}%</span>
        </div>
      </div>

      <div class="card">
        <h3>Ключевые слова</h3>
        <div class="keywords">
          <span 
            v-for="kw in result.keywords" 
            :key="kw.word" 
            class="keyword"
          >
            {{ kw.word }}
            <small>({{ kw.frequency }})</small>
          </span>
        </div>
        <div v-if="!result.keywords || result.keywords.length === 0" class="no-data">
          Ключевые слова не найдены
        </div>
      </div>

      <div class="card">
        <h3>Статистика</h3>
        <div class="stats-grid">
          <div>Символов: {{ result.statistics.total_characters }}</div>
          <div>Символов без пробелов: {{ result.statistics.characters_without_spaces }}</div>
          <div>Слов: {{ result.statistics.words }}</div>
          <div>Уникальных слов: {{ result.statistics.unique_words }}</div>
          <div>Предложений: {{ result.statistics.sentences }}</div>
          <div>Ср. длина слова: {{ result.statistics.average_word_length }}</div>
          <div>Ср. длина предложения: {{ result.statistics.average_sentence_length }}</div>
        </div>
      </div>

      <div class="export-buttons">
        <button @click="exportTxt" class="export-btn">Экспорт TXT</button>
        <button @click="exportJson" class="export-btn">Экспорт JSON</button>
        <button @click="exportPdf" class="export-btn">Экспорт PDF</button>
      </div>

    </div>
  </div>
</template>

<script>
import axios from 'axios'
import html2pdf from 'html2pdf.js'

export default {
  data() {
    return {
      text: '',
      loading: false,
      result: null,
      error: ''
    }
  },
  computed: {
    wordCount() {
      return this.text.split(/\s+/).filter(w => w.length > 0).length
    },
    sentimentClass() {
      const s = this.result?.sentiment?.sentiment
      if (s === 'ПОЛОЖИТЕЛЬНЫЙ') return 'positive'
      if (s === 'ОТРИЦАТЕЛЬНЫЙ') return 'negative'
      return 'neutral'
    }
  },
  methods: {
    async handleAnalyze() {
      if (!this.text.trim()) {
        this.error = 'Введите текст для анализа'
        return
      }

      this.loading = true
      this.error = ''
      this.result = null

      try {
        const res = await axios.post('http://localhost:8000/analyze', { 
          text: this.text 
        })
        this.result = res.data
      } catch (err) {
        const detail = err.response?.data?.detail
        
        if (Array.isArray(detail)) {
          this.error = detail.map(e => e.msg).join(', ')
        } else if (typeof detail === 'string') {
          this.error = detail
        } else {
          this.error = 'Ошибка анализа'
        }
      } finally {
        this.loading = false
      }
    }
    },

    exportTxt() {
      if (!this.result) return

      const content = `OPUS TEXT ANALYSIS REPORT
========================================

TITLE:
${this.result.title}

SUMMARY:
${this.result.summary}

COMPRESSION:
${this.result.compression || 0}%

SENTIMENT:
${this.result.sentiment.sentiment}
Confidence: ${Math.round(this.result.sentiment.confidence * 100)}%
Positive words: ${this.result.sentiment.positive_words}
Negative words: ${this.result.sentiment.negative_words}

KEYWORDS:
${this.result.keywords.map(k => `${k.word} (${k.frequency})`).join(', ')}

STATISTICS:
Characters: ${this.result.statistics.total_characters}
Characters without spaces: ${this.result.statistics.characters_without_spaces}
Words: ${this.result.statistics.words}
Unique words: ${this.result.statistics.unique_words}
Sentences: ${this.result.statistics.sentences}
Average word length: ${this.result.statistics.average_word_length}
Average sentence length: ${this.result.statistics.average_sentence_length}

Analysis date: ${new Date().toLocaleString()}
`

      const blob = new Blob([content], { type: 'text/plain' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `opus_analysis_${Date.now()}.txt`
      link.click()
      URL.revokeObjectURL(link.href)
    },

    exportJson() {
      if (!this.result) return

      const exportData = {
        title: this.result.title,
        summary: this.result.summary,
        compression: this.result.compression || 0,
        sentiment: this.result.sentiment,
        keywords: this.result.keywords,
        statistics: this.result.statistics,
        exported_at: new Date().toISOString()
      }

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `opus_analysis_${Date.now()}.json`
      link.click()
      URL.revokeObjectURL(link.href)
    },

    exportPdf() {
      if (!this.result) return

      const element = document.createElement('div')
      element.innerHTML = `
        <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #1e6f9f; text-align: center; }
            h2 { color: #333; margin-top: 20px; font-size: 16px; }
            .section { margin-bottom: 20px; }
            .label { font-weight: bold; margin-bottom: 5px; }
            .keywords span { display: inline-block; background: #f0f0f0; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 12px; }
            .stats { display: grid; grid-template-columns: repeat(2,1fr); gap: 10px; }
            .compression { color: #1e6f9f; font-weight: bold; }
          </style>
        </head>
        <body>
          <h1>OPUS TEXT ANALYSIS REPORT</h1>
          
          <div class="section">
            <div class="label">TITLE:</div>
            <div>${this.result.title}</div>
          </div>
          
          <div class="section">
            <div class="label">SUMMARY:</div>
            <div>${this.result.summary}</div>
            <div class="compression">Compression: ${this.result.compression || 0}%</div>
          </div>
          
          <div class="section">
            <div class="label">SENTIMENT:</div>
            <div>${this.result.sentiment.sentiment}</div>
            <div>Confidence: ${Math.round(this.result.sentiment.confidence * 100)}%</div>
            <div>Positive words: ${this.result.sentiment.positive_words}</div>
            <div>Negative words: ${this.result.sentiment.negative_words}</div>
          </div>
          
          <div class="section">
            <div class="label">KEYWORDS:</div>
            <div class="keywords">
              ${this.result.keywords.map(k => `<span>${k.word} (${k.frequency})</span>`).join('')}
            </div>
          </div>
          
          <div class="section">
            <div class="label">STATISTICS:</div>
            <div class="stats">
              <div>Characters: ${this.result.statistics.total_characters}</div>
              <div>Characters without spaces: ${this.result.statistics.characters_without_spaces}</div>
              <div>Words: ${this.result.statistics.words}</div>
              <div>Unique words: ${this.result.statistics.unique_words}</div>
              <div>Sentences: ${this.result.statistics.sentences}</div>
              <div>Avg word length: ${this.result.statistics.average_word_length}</div>
              <div>Avg sentence length: ${this.result.statistics.average_sentence_length}</div>
            </div>
          </div>
          
          <div style="margin-top: 40px; text-align: center; color: #888;">
            Analysis date: ${new Date().toLocaleString()}
          </div>
        </body>
        </html>
      `

      const opt = {
        margin: 0.5,
        filename: `opus_analysis_${Date.now()}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
      }

      html2pdf().set(opt).from(element).save()
    }
  }
}
</script>

<style scoped>
h1 {
  font-size: 1.875rem;
  font-weight: 300;
  margin-bottom: 1.5rem;
}

.input-area {
  background: var(--surface-dark);
  border: 1px solid var(--border-dark);
  border-radius: 12px;
  padding: 1.5rem;
}

body.light .input-area {
  background: var(--surface-light);
  border: 1px solid var(--border-light);
}

textarea {
  width: 100%;
  padding: 0.75rem;
  background: #0a0a0a;
  border: 1px solid var(--border-dark);
  border-radius: 8px;
  color: var(--text-dark);
  font-family: inherit;
  resize: vertical;
}

body.light textarea {
  background: #ffffff;
  border: 1px solid var(--border-light);
  color: var(--text-light);
}

textarea:focus {
  outline: none;
  border-color: #1e6f9f;
}

.info {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
}

.info span {
  color: #8b8b8b;
  font-size: 0.875rem;
}

button {
  padding: 0.5rem 1.5rem;
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
  margin-top: 1rem;
  background: rgba(220, 38, 38, 0.2);
  border: 1px solid #991b1b;
  color: #fca5a5;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.loader {
  width: 32px;
  height: 32px;
  margin: 2rem auto;
  border: 2px solid #1f1f1f;
  border-top-color: #1e6f9f;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.results {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card {
  background: var(--surface-dark);
  border: 1px solid var(--border-dark);
  border-radius: 12px;
  padding: 1.5rem;
}

body.light .card {
  background: var(--surface-light);
  border: 1px solid var(--border-light);
}

.card h3 {
  font-size: 0.875rem;
  font-weight: 500;
  color: #8b8b8b;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.positive {
  color: #4ade80;
}

.negative {
  color: #f87171;
}

.neutral {
  color: #fbbf24;
}

.sentiment-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #8b8b8b;
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.keyword {
  background: #0a0a0a;
  border: 1px solid var(--border-dark);
  border-radius: 9999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  color: var(--text-dark);
}

body.light .keyword {
  background: #ffffff;
  border: 1px solid var(--border-light);
  color: var(--text-light);
}

.keyword small {
  color: #8b8b8b;
  font-size: 0.7rem;
  margin-left: 0.25rem;
}

.no-data {
  margin-top: 0.5rem;
  color: #8b8b8b;
  font-size: 0.875rem;
}

.compression {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #1e6f9f;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

.export-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1rem;
}

.export-btn {
  background: #1e6f9f;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.export-btn:hover {
  background: #155a82;
}
</style>