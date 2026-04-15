<template>
  <div class="notification-system">
    <div class="dropdown">
      <!-- Bell Button with Dynamic Badge -->
      <button 
        class="btn btn-notify position-relative" 
        type="button" 
        data-bs-toggle="dropdown" 
        @click="handleBellClick"
        :aria-expanded="false"
      >
        <i class="fas fa-bell text-white"></i>
        <span v-if="unreadCount > 0" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger border border-light animate-bounce">
          {{ unreadCount }}
        </span>
      </button>

      <!-- Dropdown Menu -->
      <div class="dropdown-menu dropdown-menu-end shadow-lg border-0 p-0 notification-dropdown">
        <div class="p-3 border-bottom d-flex justify-content-between align-items-center bg-light">
          <h6 class="mb-0 fw-bold">Recent Alerts</h6>
          <div class="d-flex gap-2">
            <span v-if="unreadCount > 0" class="badge bg-primary rounded-pill">{{ unreadCount }} New</span>
            <button class="btn btn-link p-0 text-decoration-none extra-small fw-bold" @click.stop="syncNotifications">
              <i class="fas fa-sync-alt" :class="{'fa-spin': isSyncing}"></i>
            </button>
          </div>
        </div>

        <div class="notification-list custom-scrollbar">
          <!-- Loading State -->
          <div v-if="isSyncing && notifications.length === 0" class="p-5 text-center">
            <div class="spinner-border spinner-border-sm text-primary mb-2"></div>
            <p class="text-muted extra-small mb-0">Fetching alerts...</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="notifications.length === 0" class="p-5 text-center text-muted small">
            <i class="fas fa-bell-slash d-block mb-3 opacity-25 fa-3x"></i>
            <p class="mb-0 fw-bold text-dark opacity-50">Identity Registry Quiet</p>
            <p class="extra-small mb-0">No placement alerts recorded for your account.</p>
          </div>

          <!-- Notification Items -->
          <div 
            v-for="note in notifications" 
            :key="note.id" 
            class="notification-item p-3 border-bottom" 
            :class="{ unread: !note.read, 'report-alert': note.category === 'report' }"
          >
            <div class="d-flex align-items-start">
              <div class="icon-indicator me-3 shadow-sm flex-shrink-0" :class="'bg-' + (note.type || 'info')">
                <i :class="getIcon(note.type, note.category)"></i>
              </div>
              <div class="flex-grow-1 overflow-hidden">
                <div class="d-flex justify-content-between align-items-start mb-1">
                  <p class="mb-0 small fw-bold text-dark text-truncate pe-2">{{ note.title }}</p>
                  <small class="text-muted extra-small white-space-nowrap">{{ note.time }}</small>
                </div>
                <p class="mb-2 small text-secondary lh-sm">{{ note.message }}</p>

                <!-- Specialized Report Actions (Requirement: Choose between HTML and PDF) -->
                <div v-if="note.category === 'report'" class="report-actions d-flex gap-2 mt-2">
                  <a :href="note.html_url" target="_blank" class="btn btn-xs btn-outline-primary rounded-pill px-3 py-1 extra-small fw-bold text-decoration-none">
                    <i class="fas fa-code me-1"></i> HTML View
                  </a>
                  <a :href="note.pdf_url" download class="btn btn-xs btn-primary rounded-pill px-3 py-1 extra-small fw-bold text-decoration-none text-white">
                    <i class="fas fa-file-pdf me-1"></i> PDF Report
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="p-2 text-center bg-light rounded-bottom-4">
          <button class="btn btn-link btn-sm text-decoration-none fw-bold text-primary py-1" @click.prevent="syncNotifications">
            Sync Institutional Feed
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotificationBell',
  data() {
    return {
      notifications: [],
      unreadCount: 0,
      isSyncing: false,
      pollInterval: null
    }
  },
  methods: {
    getIcon(type, category) {
      if (category === 'report') return 'fas fa-chart-line';
      const icons = { 
        success: 'fas fa-check-circle', 
        warning: 'fas fa-exclamation-triangle', 
        danger: 'fas fa-times-circle', 
        info: 'fas fa-info-circle' 
      };
      return icons[type] || icons.info;
    },
    async syncNotifications() {
      const role = localStorage.getItem('shaanu_role');
      const token = localStorage.getItem('shaanu_token');
      if (!role || !token) return;

      this.isSyncing = true;
      
      const pathMap = { 'admin': 'controller', 'student': 'candidate', 'company': 'enterprise' };
      const endpoint = `/api/v1/${pathMap[role]}/notifications`;

      try {
        const res = await fetch(endpoint, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (res.ok) {
          const data = await res.json();
          this.notifications = data.sort((a, b) => new Date(b.time) - new Date(a.time));
          this.unreadCount = this.notifications.filter(n => !n.read).length;
        }
      } catch (err) {
        console.error("Alert System Sync Failure:", err);
      } finally {
        this.isSyncing = false;
      }
    },
    async handleBellClick() {
      if (this.unreadCount > 0) {
        await this.markAllAsRead();
      }
    },
    async markAllAsRead() {
      const role = localStorage.getItem('shaanu_role');
      const token = localStorage.getItem('shaanu_token');
      if (!role || !token) return;

      this.unreadCount = 0;
      
      const pathMap = { 'admin': 'controller', 'student': 'candidate', 'company': 'enterprise' };
      const endpoint = `/api/v1/${pathMap[role]}/notifications/mark-read`;

      try {
        fetch(endpoint, { 
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          } 
        }).then(() => {
          this.notifications.forEach(n => n.read = true);
        });
      } catch (err) {
        console.warn("Could not synchronize read status.");
      }
    }
  },
  mounted() {
    this.syncNotifications();
    this.pollInterval = setInterval(this.syncNotifications, 60000);
  },
  beforeUnmount() {
    if (this.pollInterval) clearInterval(this.pollInterval);
  }
}
</script>

<style scoped>
.btn-notify { 
  background: rgba(255, 255, 255, 0.1); 
  border: 1px solid rgba(255, 255, 255, 0.1); 
  width: 42px; 
  height: 42px; 
  border-radius: 12px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  transition: all 0.2s ease;
}

.btn-notify:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.notification-dropdown { 
  width: 380px; 
  border-radius: 20px; 
  margin-top: 12px; 
  overflow: hidden; 
  z-index: 1100;
}

.notification-list { 
  max-height: 450px; 
  overflow-y: auto; 
}

.notification-item {
  transition: background-color 0.2s ease;
}

.notification-item.unread { 
  background-color: rgba(30, 60, 114, 0.04); 
}

.notification-item.report-alert {
  background-color: rgba(13, 110, 253, 0.02);
}

.notification-item:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.icon-indicator { 
  width: 38px; 
  height: 38px; 
  border-radius: 12px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  color: white; 
  font-size: 0.9rem;
}

.extra-small { font-size: 0.65rem; }
.white-space-nowrap { white-space: nowrap; }

.animate-bounce { 
  animation: bounce 2.5s infinite; 
}

@keyframes bounce { 
  0%, 20%, 50%, 80%, 100% { transform: translateY(0) translateX(50%); } 
  40% { transform: translateY(-4px) translateX(50%); } 
  60% { transform: translateY(-2px) translateX(50%); } 
}

.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #cbd5e1; }

.btn-xs {
  font-size: 0.6rem;
  padding: 2px 8px;
}
</style>