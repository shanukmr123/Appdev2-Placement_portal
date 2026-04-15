<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-shaanu shadow sticky-top">
    <div class="container-fluid px-4">
      <a class="navbar-brand d-flex align-items-center" href="#" v-on:click.prevent="setTab('overview')">
        <div class="logo-box me-2 bg-white rounded p-1">
            <i class="fas fa-graduation-cap text-primary"></i>
        </div>
        <span class="fw-bold">SHAANU <small class="fw-light opacity-75 d-none d-sm-inline">Placement Portal</small></span>
      </a>

      <!-- Mobile Toggle -->
      <button class="navbar-toggler border-0 shadow-none" type="button" data-bs-toggle="collapse" data-bs-target="#shaanuNav">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="shaanuNav">
        <ul class="navbar-nav mx-auto mb-2 mb-lg-0">
          <!-- Shared Dashboard Link -->
          <li class="nav-item">
            <a class="nav-link" v-bind:class="{active: currentTab === 'overview' || currentTab === 'dashboard'}" href="#" v-on:click.prevent="setTab('overview')">
                <i class="fas fa-th-large me-1"></i> {{ userRole === 'admin' ? 'Metrics' : 'Dashboard' }}
            </a>
          </li>
          
          <!-- Admin-Specific Orchestration -->
          <template v-if="userRole === 'admin'">
            <li class="nav-item">
                <a class="nav-link" v-bind:class="{active: currentTab === 'moderation'}" href="#" v-on:click.prevent="setTab('moderation')">
                    <i class="fas fa-check-double me-1"></i> Moderation
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" v-bind:class="{active: currentTab === 'registry'}" href="#" v-on:click.prevent="setTab('registry')">
                    <i class="fas fa-users-cog me-1"></i> Registry
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" v-bind:class="{active: currentTab === 'ledger'}" href="#" v-on:click.prevent="setTab('ledger')">
                    <i class="fas fa-file-invoice me-1"></i> Master Ledger
                </a>
            </li>
          </template>

          <!-- Student-Specific Orchestration -->
          <template v-if="userRole === 'student'">
            <li class="nav-item">
                <a class="nav-link" v-bind:class="{active: currentTab === 'drives'}" href="#" v-on:click.prevent="setTab('drives')">
                    <i class="fas fa-briefcase me-1"></i> Job Board
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" v-bind:class="{active: currentTab === 'history'}" href="#" v-on:click.prevent="setTab('history')">
                    <i class="fas fa-history me-1"></i> My Journey
                </a>
            </li>
          </template>

          <!-- Company-Specific Orchestration -->
          <template v-if="userRole === 'company'">
            <li class="nav-item">
                <a class="nav-link" v-bind:class="{active: currentTab === 'postings'}" href="#" v-on:click.prevent="setTab('postings')">
                    <i class="fas fa-plus-circle me-1"></i> Create Drive
                </a>
            </li>
          </template>
        </ul>

        <div class="d-flex align-items-center gap-2 gap-lg-3 mt-3 mt-lg-0">
          <notification-bell />
          <theme-toggle />
          
          <div class="dropdown">
            <button class="btn btn-user dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown">
              <div class="avatar bg-warning text-dark me-2 shadow-sm">{{ userName[0].toUpperCase() }}</div>
              <div class="text-start d-none d-md-block pe-2">
                <div class="small fw-bold text-white lh-1 mb-1">{{ userName }}</div>
                <div class="badge bg-primary-light text-uppercase p-1" style="font-size: 0.55rem;">{{ userRole }}</div>
              </div>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow-lg border-0 rounded-4 mt-2">
              <li class="px-3 py-3 border-bottom bg-light rounded-top-4">
                <small class="text-muted d-block fw-bold text-uppercase" style="font-size: 0.6rem;">Institutional ID</small>
                <strong class="small text-dark">{{ userEmail }}</strong>
              </li>
              <li><a class="dropdown-item py-2 mt-1" href="#" v-on:click.prevent="setTab('profile')"><i class="fas fa-id-card me-2 text-primary"></i> Account Profile</a></li>
              <li><hr class="dropdown-divider"></li>
              <li><a class="dropdown-item py-2 text-danger fw-bold" href="#" v-on:click.prevent="logout"><i class="fas fa-sign-out-alt me-2"></i> End Session</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
  props: ['currentTab'],
  data() {
    return {
      userName: localStorage.getItem('shaanu_user') || 'User',
      userRole: localStorage.getItem('shaanu_role') || 'guest',
      userEmail: localStorage.getItem('shaanu_email') || 'user@shaanu.edu'
    }
  },
  methods: {
    setTab(t) { this.$emit('update:current-tab', t); },
    logout() { this.$emit('logout'); }
  }
}
</script>

<style scoped>
.bg-shaanu { background: #1e3c72; }
.logo-box { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.nav-link { font-weight: 600; color: rgba(255,255,255,0.7) !important; margin: 0 5px; padding: 8px 15px !important; border-radius: 50px; transition: all 0.2s ease; }
.nav-link:hover { color: #fff !important; background: rgba(255,255,255,0.1); }
.nav-link.active { color: #fff !important; background: rgba(255,255,255,0.15); box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2); }
.btn-user { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); border-radius: 50px; color: white; padding: 4px 16px 4px 4px; transition: all 0.2s ease; }
.avatar { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; }
.bg-primary-light { background: rgba(255,255,255,0.2); }
</style>