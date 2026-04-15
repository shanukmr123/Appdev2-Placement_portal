<template>
  <div class="shaanu-workspace">
    <!-- Navbar Orchestration -->
    <navbar 
      v-bind:current-tab="activeTab" 
      v-on:update:current-tab="updateNavigation" 
      v-on:logout="triggerLogout"
    ></navbar>

    <!-- Content Viewport -->
    <main class="workspace-viewport">
      <div class="container-fluid py-4 px-lg-5">
        <transition name="view-fade" mode="out-in">
          <div v-bind:key="activeTab">
            <!-- Dynamic Role Dispatcher - Standardized Event Listeners -->
            <admin-dashboard 
              v-if="userRole === 'admin'" 
              v-bind:current-tab="activeTab"
              v-on:update:current-tab="updateNavigation"
            ></admin-dashboard>

            <student-dashboard 
              v-else-if="userRole === 'student'" 
              v-bind:current-tab="activeTab"
              v-on:update:current-tab="updateNavigation"
            ></student-dashboard>

            <company-dashboard 
              v-else-if="userRole === 'company'" 
              v-bind:current-tab="activeTab"
              v-on:update:current-tab="updateNavigation"
            ></company-dashboard>

            <!-- Profile Fallback -->
            <div v-else-if="activeTab === 'profile'" class="profile-placeholder p-5 text-center">
                <div class="card border-0 shadow-sm p-5 rounded-5 glass-morphism mx-auto" style="max-width: 600px;">
                    <i class="fas fa-id-card fa-4x text-primary mb-4"></i>
                    <h3 class="fw-bold">Account Intelligence</h3>
                    <p class="text-muted">Institutional identity management is active. You can update your records here.</p>
                    <button class="btn btn-primary rounded-pill px-4 mt-3" v-on:click="activeTab = 'dashboard'">Return to Dashboard</button>
                </div>
            </div>
          </div>
        </transition>
      </div>
    </main>

    <!-- Global Footer -->
    <footer class="mt-auto py-3 bg-white border-top text-center desktop-only">
      <small class="text-muted">
        &copy; 2024 ShaanU Placement Cell &bull; Integrated Institutional Cloud &bull; 
        <span class="text-primary fw-bold">v1.2.0-STABLE</span>
      </small>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'DashboardComponent',
  data() {
    return {
      activeTab: 'dashboard',
      userRole: localStorage.getItem('shaanu_role') || 'guest'
    }
  },
  methods: {
    updateNavigation(newTab) {
      this.activeTab = newTab;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    triggerLogout() {
      if(confirm("Institutional Session End: Are you sure you want to sign out?")) {
        this.$emit('logout');
      }
    }
  }
}
</script>

<style scoped>
.shaanu-workspace { display: flex; flex-direction: column; min-height: 100vh; background-color: #f8fafd; }
.workspace-viewport { flex: 1 0 auto; }
.glass-morphism { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
.view-fade-enter-active, .view-fade-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.view-fade-enter-from { opacity: 0; transform: translateY(10px); }
.view-fade-leave-to { opacity: 0; transform: translateY(-10px); }
@media (max-width: 768px) { .desktop-only { display: none !important; } }
</style>