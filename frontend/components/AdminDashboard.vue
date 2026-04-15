<template>
  <div class="admin-workspace container-fluid py-4 fade-in">
    <!-- Unified Header with Command Search -->
    <div class="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center mb-5 gap-4">
      <div>
        <h2 class="fw-bold text-dark mb-0">Institutional Command Center</h2>
        <p class="text-muted small mb-0">Governance, Moderation, and Ecosystem Oversight</p>
      </div>
      
      <!-- Global Search Field -->
      <div class="search-container position-relative flex-grow-1 mx-lg-5" style="max-width: 500px;">
        <i class="fas fa-search position-absolute top-50 start-0 translate-middle-y ms-3 text-muted"></i>
        <input 
          v-model="searchQuery" 
          type="text" 
          class="form-control form-control-lg rounded-pill ps-5 border-0 shadow-sm" 
          placeholder="Search by name, company, or role..."
        >
      </div>

      <button class="btn btn-outline-primary rounded-pill px-4 shadow-sm" @click="syncAll" :disabled="loading">
        <i class="fas fa-sync-alt me-2" :class="{'fa-spin': loading}"></i> Sync System
      </button>
    </div>

    <!-- Navigation Pills -->
    <ul class="nav nav-pills mb-4 gap-2 bg-white p-2 rounded-pill shadow-sm d-inline-flex border">
      <li class="nav-item"><button :class="['nav-link rounded-pill px-4', activeTab === 'overview' ? 'active' : '']" @click="activeTab = 'overview'">Metrics</button></li>
      <li class="nav-item"><button :class="['nav-link rounded-pill px-4', activeTab === 'moderation' ? 'active' : '']" @click="activeTab = 'moderation'">Moderation Queue</button></li>
      <li class="nav-item"><button :class="['nav-link rounded-pill px-4', activeTab === 'drives' ? 'active' : '']" @click="activeTab = 'drives'">Drive Management</button></li>
      <li class="nav-item"><button :class="['nav-link rounded-pill px-4', activeTab === 'registry' ? 'active' : '']" @click="activeTab = 'registry'">User Registry</button></li>
      <li class="nav-item"><button :class="['nav-link rounded-pill px-4', activeTab === 'ledger' ? 'active' : '']" @click="activeTab = 'ledger'">Master Ledger</button></li>
    </ul>

    <!-- 1. OVERVIEW TAB -->
    <div v-if="activeTab === 'overview'" class="fade-in">
      <div class="row g-4 mb-4">
        <div class="col-md-3" v-for="(val, key) in metricsList" :key="key">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white border-start border-4 text-center" :class="'border-' + val.color">
            <h6 class="text-uppercase extra-small fw-bold text-muted mb-2">{{ val.label }}</h6>
            <h2 class="fw-bold mb-0" :class="'text-' + val.color">{{ metrics[key] || 0 }}</h2>
          </div>
        </div>
      </div>
      <div class="card border-0 shadow-sm rounded-4 p-4 bg-white mb-4">
        <h6 class="fw-bold mb-4">Placement Velocity Trend</h6>
        <chart-component v-if="chartData" :data="chartData" type="line" height="320px"></chart-component>
      </div>
    </div>

    <!-- 2. MODERATION QUEUE (Verification) -->
    <div v-if="activeTab === 'moderation'" class="fade-in">
      <h6 class="fw-bold mb-3 text-primary text-uppercase small"><i class="fas fa-building me-2"></i> Pending Enterprise Partners</h6>
      <div class="row g-4 mb-5">
        <div v-if="filteredPendingCompanies.length === 0" class="col-12 text-center py-4 bg-white rounded-4 border">
          <p class="text-muted small mb-0">No companies matching search found in queue.</p>
        </div>
        <div v-for="company in filteredPendingCompanies" :key="company.id" class="col-md-6 col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
            <h6 class="fw-bold mb-1">{{ company.name }}</h6>
            <p class="extra-small text-muted mb-3">{{ company.sector }} • {{ company.email }}</p>
            <div class="d-flex gap-2 pt-3 border-top mt-auto">
              <button class="btn btn-success btn-sm rounded-pill px-3 fw-bold w-100" @click="resolveCompany(company.id, 'approved')">Approve</button>
              <button class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-bold w-100" @click="resolveCompany(company.id, 'rejected')">Deny</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. DRIVE MANAGEMENT (All Drives) -->
    <div v-if="activeTab === 'drives'" class="fade-in">
      <div class="row g-4">
        <div v-if="filteredDrives.length === 0" class="col-12 text-center py-5 text-muted">
            <i class="fas fa-briefcase fa-4x mb-3 opacity-25"></i>
            <p>No placement drives found matching "{{ searchQuery }}".</p>
        </div>
        <div v-for="drive in filteredDrives" :key="drive.id" class="col-md-6 col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 h-100 bg-white d-flex flex-column drive-card border-top border-5" :class="getStatusBorder(drive.status)">
            <div class="card-body p-4">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <span :class="['badge rounded-pill px-3 py-2 extra-small', getDriveBadge(drive.status)]">{{ drive.status.toUpperCase() }}</span>
                <span class="fw-bold text-success">{{ drive.package }}</span>
              </div>
              <h5 class="fw-bold text-dark mb-1">{{ drive.title }}</h5>
              <p class="extra-small text-muted mb-3">Partner: <strong class="text-primary">{{ drive.company }}</strong></p>
              
              <div class="mt-auto d-flex flex-wrap gap-2 pt-3 border-top">
                <button v-if="drive.status !== 'active'" class="btn btn-success btn-sm rounded-pill px-3 fw-bold" @click="resolveDrive(drive.id, 'active')">Activate</button>
                <button v-if="drive.status === 'active'" class="btn btn-warning btn-sm rounded-pill px-3 fw-bold" @click="resolveDrive(drive.id, 'closed')">Close</button>
                <button v-if="drive.status !== 'rejected'" class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-bold" @click="resolveDrive(drive.id, 'rejected')">Deny</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. USER REGISTRY -->
    <div v-if="activeTab === 'registry'" class="fade-in">
        <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
            <div class="table-responsive">
              <table class="table align-middle mb-0 table-hover">
                  <thead class="bg-light"><tr class="extra-small fw-bold text-muted text-uppercase">
                      <th class="ps-4 py-3">Institutional Identity</th><th>Role</th><th>Status</th><th class="text-end pe-4">Action</th>
                  </tr></thead>
                  <tbody>
                      <tr v-for="user in filteredRegistry" :key="user.id">
                          <td class="ps-4">
                              <div class="fw-bold small text-dark">{{ user.display_name }}</div>
                              <div class="extra-small text-muted">{{ user.email }}</div>
                          </td>
                          <td><span class="badge bg-light text-dark border extra-small px-3 text-uppercase">{{ user.role }}</span></td>
                          <td><span :class="['badge rounded-pill px-3 py-1 extra-small', user.is_active ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger']">{{ user.is_active ? 'Authorized' : 'Blacklisted' }}</span></td>
                          <td class="text-end pe-4"><button :class="['btn btn-sm rounded-pill px-3 fw-bold', user.is_active ? 'btn-outline-danger' : 'btn-success']" @click="toggleUser(user.id)">{{ user.is_active ? 'Block' : 'Allow' }}</button></td>
                      </tr>
                  </tbody>
              </table>
            </div>
        </div>
    </div>

    <!-- 5. MASTER LEDGER -->
    <div v-if="activeTab === 'ledger'" class="fade-in">
      <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="bg-light">
              <tr class="extra-small text-muted fw-bold text-uppercase">
                <th class="ps-4 py-3">Candidate</th><th>Partner</th><th>Role</th><th>Status</th><th class="text-end pe-4">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="app in filteredLedger" :key="app.id">
                <td class="ps-4 fw-bold text-dark">{{ app.student }}</td>
                <td>{{ app.company }}</td>
                <td>{{ app.role }}</td>
                <td><span :class="['badge rounded-pill px-3 py-1 extra-small', getStageClass(app.stage)]">{{ app.stage }}</span></td>
                <td class="text-end pe-4 small text-muted">{{ app.date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminDashboard',
  props: ['currentTab'],
  data() {
    return {
      activeTab: this.currentTab === 'dashboard' ? 'overview' : (this.currentTab || 'overview'),
      loading: false,
      searchQuery: '',
      metrics: {},
      pendingCompanies: [],
      allDrives: [],
      registry: [],
      ledger: [],
      chartData: null,
      metricsList: {
          candidate_count: { label: 'Candidates', color: 'primary' },
          enterprise_count: { label: 'Partners', color: 'success' },
          active_drives: { label: 'Active Drives', color: 'warning' },
          placed_students: { label: 'Placed', color: 'info' }
      }
    }
  },
  computed: {
    filteredRegistry() {
      const q = this.searchQuery.toLowerCase();
      return this.registry.filter(u => u.display_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
    },
    filteredDrives() {
      const q = this.searchQuery.toLowerCase();
      return this.allDrives.filter(d => d.title.toLowerCase().includes(q) || d.company.toLowerCase().includes(q));
    },
    filteredLedger() {
      const q = this.searchQuery.toLowerCase();
      return this.ledger.filter(a => a.student.toLowerCase().includes(q) || a.company.toLowerCase().includes(q) || a.role.toLowerCase().includes(q));
    },
    filteredPendingCompanies() {
      const q = this.searchQuery.toLowerCase();
      return this.pendingCompanies.filter(c => c.name.toLowerCase().includes(q));
    }
  },
  watch: {
    currentTab(newVal) {
      if (newVal === 'dashboard') this.activeTab = 'overview';
      else if (newVal) this.activeTab = newVal;
      this.syncAll();
    }
  },
  methods: {
    async syncAll() {
      this.loading = true;
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` };
      try {
        const [m, c, d, r, l] = await Promise.all([
          fetch('/api/v1/controller/dashboard/metrics', { headers: h }),
          fetch('/api/v1/controller/moderate/enterprises', { headers: h }),
          fetch('/api/v1/controller/moderate/drives/all', { headers: h }),
          fetch('/api/v1/controller/registry/all', { headers: h }),
          fetch('/api/v1/controller/monitor/applications', { headers: h })
        ]);
        if(m.ok) { this.metrics = await m.json(); this.updateChart(); }
        if(c.ok) this.pendingCompanies = await c.json();
        if(d.ok) this.allDrives = await d.json();
        if(r.ok) this.registry = await r.json();
        if(l.ok) this.ledger = await l.json();
      } finally { this.loading = false; }
    },
    updateChart() {
      this.chartData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Current'],
        datasets: [{
          label: 'Institutional Placements',
          data: [5, 12, 18, 25, 30, this.metrics.placed_students || 0],
          borderColor: '#1e3c72',
          backgroundColor: 'rgba(30, 60, 114, 0.1)',
          fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: '#1e3c72'
        }]
      };
    },
    async resolveCompany(id, status) {
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
      await fetch(`/api/v1/controller/action/enterprise/${id}`, { method: 'PATCH', headers: h, body: JSON.stringify({ status }) });
      this.syncAll();
    },
    async resolveDrive(id, status) {
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
      await fetch(`/api/v1/controller/action/drive/${id}`, { method: 'PATCH', headers: h, body: JSON.stringify({ status }) });
      this.syncAll();
    },
    async toggleUser(id) {
       await fetch(`/api/v1/controller/registry/toggle-access/${id}`, { method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` } });
       this.syncAll();
    },
    getDriveBadge(s) {
      const maps = { active: 'bg-success text-white', pending_approval: 'bg-info text-dark', rejected: 'bg-danger text-white', closed: 'bg-secondary text-white' };
      return maps[s] || 'bg-light';
    },
    getStatusBorder(s) {
      const maps = { active: 'border-success', pending_approval: 'border-info', rejected: 'border-danger', closed: 'border-secondary' };
      return maps[s] || '';
    },
    getStageClass(s) {
      const c = { 'Selected': 'bg-success text-white', 'Rejected': 'bg-danger text-white', 'Interviewing': 'bg-primary text-white', 'Shortlisted': 'bg-info text-dark', 'Applied': 'bg-light text-dark border' };
      return c[s] || 'bg-light text-dark';
    }
  },
  mounted() { this.syncAll(); }
}
</script>

<style scoped>
.rounded-4 { border-radius: 1.25rem !important; }
.extra-small { font-size: 0.65rem; }
.nav-link.active { background-color: #1e3c72; color: white; }
.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
.drive-card { transition: all 0.2s; }
.drive-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
.bg-success-subtle { background-color: #d1e7dd; }
.bg-danger-subtle { background-color: #f8d7da; }
.form-control-lg { font-size: 1rem; }
</style>