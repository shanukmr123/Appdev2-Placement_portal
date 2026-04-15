<template>
  <div class="theme-switcher">
    <button @click="toggleTheme" class="btn btn-theme shadow-none" :title="'Switch to ' + (isDark ? 'Light' : 'Dark') + ' mode'">
      <div class="theme-icon-container">
        <i v-if="isDark" class="fas fa-sun text-warning animate-spin-in"></i>
        <i v-else class="fas fa-moon text-indigo animate-spin-in"></i>
      </div>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ThemeToggle',
  data() {
    return {
      isDark: localStorage.getItem('shaanu_theme') === 'dark'
    }
  },
  methods: {
    toggleTheme() {
      this.isDark = !this.isDark;
      const theme = this.isDark ? 'dark' : 'light';
      localStorage.setItem('shaanu_theme', theme);
      document.body.setAttribute('data-bs-theme', theme);
      
      // Update body background color directly to ensure smooth transitions
      document.body.style.backgroundColor = this.isDark ? '#121212' : '#f8fafd';
      
      // Dispatch a custom event so other components (like charts) can respond to theme changes
      window.dispatchEvent(new CustomEvent('shaanu-theme-changed', { detail: { theme } }));
    }
  },
  mounted() {
    // Initialize theme based on local storage or system preference
    const savedTheme = localStorage.getItem('shaanu_theme') || 
                      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    this.isDark = savedTheme === 'dark';
    document.body.setAttribute('data-bs-theme', savedTheme);
    document.body.style.backgroundColor = this.isDark ? '#121212' : '#f8fafd';
  }
}
</script>

<style scoped>
.btn-theme {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.2s ease;
}

.btn-theme:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.text-indigo { color: #6610f2; }

.animate-spin-in {
  animation: spinIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes spinIn {
  from { transform: rotate(-180deg) scale(0); opacity: 0; }
  to { transform: rotate(0) scale(1); opacity: 1; }
}

/* Ensure the icon is centered correctly */
.theme-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}
</style>