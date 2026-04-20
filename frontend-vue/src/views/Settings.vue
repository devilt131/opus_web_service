<template>
  <div>
    <h1>Настройки</h1>
    <div class="card">
      <div class="about"><div class="label">О приложении</div><div class="description">Opus — интеллектуальный анализ текста</div><div class="description">Версия 2.0.1</div></div>
    </div>
  </div>
</template>

<script>
export default { data() { return { theme: 'Темная' } } }
</script>

<style scoped>
h1 { font-size: 1.875rem; font-weight: 300; margin-bottom: 1.5rem; }
.card { background: #111; border: 1px solid #1f1f1f; border-radius: 12px; padding: 1.5rem; }
.setting { display: flex; justify-content: space-between; align-items: center; padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid #1f1f1f; }
.label { font-weight: 500; margin-bottom: 0.25rem; }
.description { color: #8b8b8b; font-size: 0.875rem; }
select { padding: 0.25rem 0.5rem; background: #0a0a0a; border: 1px solid #1f1f1f; border-radius: 6px; color: #e5e5e5; }
.about { margin-top: 1rem; }
.about .description { margin-top: 0.25rem; }
</style>
