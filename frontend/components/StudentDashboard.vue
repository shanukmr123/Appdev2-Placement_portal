<template>
  <div class="student-workspace fade-in">
    <!-- 1. DASHBOARD OVERVIEW -->
    <div v-if="activeTab === 'dashboard'" class="row g-4 mb-4">
      <div class="col-lg-8">
        <!-- Welcome Card -->
        <div class="card border-0 shadow-sm rounded-4 p-5 bg-primary text-white position-relative overflow-hidden mb-4">
          <div style="position: relative; z-index: 2;">
            <h1 class="fw-bold mb-2">Welcome, {{ profile.full_name }}</h1>
            <p class="lead opacity-75 mb-4">{{ profile.department }} • <strong>{{ profile.cgpa }} CGPA</strong></p>
            <div class="d-flex gap-3">
              <button class="btn btn-warning rounded-pill px-4 fw-bold shadow-sm text-dark" @click="setTab('drives')">Explore Jobs</button>
              <button class="btn btn-outline-light rounded-pill px-4" @click="setTab('profile')">Update Profile</button>
            </div>
          </div>
          <i class="fas fa-user-graduate position-absolute bottom-0 end-0 p-4 fa-6x opacity-10"></i>
        </div>

        <!-- Activity Feed -->
        <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h5 class="fw-bold mb-0">Institutional Alerts & Updates</h5>
            <button class="btn btn-sm btn-light rounded-pill px-3" @click="syncData">
              <i class="fas fa-sync-alt small me-1"></i> Refresh
            </button>
          </div>
          <div class="activity-list">
            <div v-if="notifications.length === 0" class="text-center py-5 text-muted small">
              <i class="fas fa-bell-slash d-block mb-3 opacity-25 fa-3x"></i>
              No recent notifications from the Placement Cell.
            </div>
            <div v-for="note in notifications.slice(0, 5)" :key="note.id" class="d-flex align-items-start mb-3 p-3 rounded-4 bg-light border-start border-4" :class="'border-' + (note.type || 'primary')">
              <div class="flex-grow-1">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <span class="fw-bold small text-dark">{{ note.title }}</span>
                  <small class="text-muted extra-small">{{ note.time }}</small>
                </div>
                <p class="mb-0 small text-muted lh-sm">{{ note.message }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-4">
        <!-- Portfolio Card -->
        <div class="card border-0 shadow-sm rounded-4 p-4 mb-4 bg-white text-center">
          <h6 class="text-uppercase small fw-bold text-muted mb-3">Institutional Portfolio</h6>
          <div v-if="profile.resume" class="mb-3 text-success">
            <i class="fas fa-file-pdf fa-3x mb-2"></i>
            <p class="small fw-bold mb-0">PDF Portfolio Synced</p>
            <small class="text-muted text-truncate d-block mx-auto" style="max-width: 180px;">{{ profile.resume }}</small>
          </div>
          <div v-else class="mb-3 text-danger opacity-50">
            <i class="fas fa-file-upload fa-3x mb-2"></i>
            <p class="small fw-bold mb-0">No Resume Found</p>
          </div>
          <input type="file" ref="quickResume" class="d-none" accept=".pdf" @change="uploadResume">
          <button class="btn btn-outline-primary rounded-pill w-100 fw-bold" @click="profile.resume ? setTab('profile') : $refs.quickResume.click()">
            <span v-if="loadingResume" class="spinner-border spinner-border-sm me-2"></span>
            {{ profile.resume ? 'Manage Portfolio' : 'Upload Now' }}
          </button>
        </div>

        <!-- Global Stats -->
        <div class="card border-0 shadow-sm rounded-4 p-4 bg-white border-start border-info border-4 mb-3">
          <h6 class="text-muted small fw-bold text-uppercase mb-1">Applications</h6>
          <h2 class="fw-bold mb-0">{{ history.length }}</h2>
        </div>
        <div class="card border-0 shadow-sm rounded-4 p-4 bg-white border-start border-success border-4 mb-3">
          <h6 class="text-muted small fw-bold text-uppercase mb-1">Offer Letters</h6>
          <h2 class="fw-bold mb-0">{{ history.filter(a => a.status === 'Selected').length }}</h2>
        </div>
      </div>
    </div>

    <!-- 2. JOB BOARD -->
    <div v-if="activeTab === 'drives'" class="fade-in">
      <div class="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <h3 class="fw-bold mb-0">Institutional Job Board</h3>
        <input v-model="searchQuery" @input="fetchDrives" type="text" class="form-control rounded-pill px-4 border-0 shadow-sm w-auto" placeholder="Search positions...">
      </div>
      <div class="row g-4">
        <div v-if="availableDrives.length === 0" class="col-12 text-center py-5">
            <div class="card border-0 shadow-sm rounded-4 p-5 bg-white text-muted">No eligible drives found matching your profile.</div>
        </div>
        <div v-for="drive in availableDrives" :key="drive.drive_id" class="col-md-6 col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 h-100 bg-white p-4 drive-card shadow-hover">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <small class="text-muted d-block extra-small fw-bold text-uppercase mb-1">Company</small>
                <span class="badge bg-primary-subtle text-primary rounded-pill px-3 py-2">{{ drive.company }}</span>
              </div>
              <div class="text-end">
                <small class="text-muted d-block extra-small fw-bold text-uppercase mb-1">CTC (LPA)</small>
                <span class="fw-bold text-success h5 mb-0">{{ drive.ctc }}</span>
              </div>
            </div>
            <div class="mb-3">
              <small class="text-muted d-block extra-small fw-bold text-uppercase mb-1">Job Role</small>
              <h5 class="fw-bold text-dark mb-0">{{ drive.position }}</h5>
            </div>
            <div class="mb-4">
              <small class="text-muted d-block extra-small fw-bold text-uppercase mb-1">Description</small>
              <p class="text-muted small mb-0 text-truncate-2">{{ drive.description }}</p>
            </div>
            <div class="pt-3 border-top d-flex justify-content-between align-items-center">
              <div><small class="text-muted d-block extra-small fw-bold text-uppercase">Min GPA: {{ drive.min_cgpa }}</small></div>
              <button class="btn btn-primary btn-sm rounded-pill px-4 fw-bold shadow-sm" @click="applyForDrive(drive.drive_id)">Apply Now</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. HISTORY TAB (APPLICATION JOURNEY & OFFERS) -->
    <div v-if="activeTab === 'history'" class="fade-in">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h3 class="fw-bold mb-0">Application Journey</h3>
        <button class="btn btn-outline-dark rounded-pill px-4" @click="triggerExport">Export CSV</button>
      </div>

      <!-- Action Required (Interviews) -->
      <div v-if="pendingInterviews.length > 0" class="mb-4">
        <h6 class="text-muted fw-bold text-uppercase extra-small mb-3"><i class="fas fa-calendar-alt me-2 text-warning"></i> Action Required: Interview Invitations</h6>
        <div v-for="invitation in pendingInterviews" :key="invitation.id" class="card border-0 shadow-sm rounded-4 mb-3 bg-warning-subtle border-start border-warning border-4">
          <div class="card-body p-4 d-flex flex-column flex-md-row justify-content-between align-items-center">
            <div class="mb-3 mb-md-0">
              <h6 class="fw-bold mb-1">{{ invitation.company }} — {{ invitation.drive }}</h6>
              <p class="mb-0 text-dark opacity-75">Proposed Schedule: <strong>{{ invitation.time }}</strong></p>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-success rounded-pill px-4 btn-sm fw-bold" @click="handleInterviewResponse(invitation.id, 'confirmed')" :disabled="loading">Accept Time</button>
              <button class="btn btn-outline-danger rounded-pill px-4 btn-sm fw-bold" @click="openRescheduleModal(invitation)" :disabled="loading">Reschedule</button>
            </div>
          </div>
        </div>
      </div>

      <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="bg-light">
              <tr class="small text-muted fw-bold text-uppercase">
                <th class="ps-4 py-3">Campaign</th>
                <th>Partner</th>
                <th>Status</th>
                <th class="text-end pe-4">Applied</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="app in history" :key="app.id">
                <td class="ps-4">
                  <div class="fw-bold">{{ app.drive }}</div>
                  <!-- Interview Slots -->
                  <div v-for="interview in app.interviews" :key="interview.id" class="extra-small mt-1">
                    <span :class="['badge rounded-pill px-2 py-1', getInterviewStatusClass(interview.status)]">
                      <i class="fas fa-clock me-1"></i> {{ interview.status.replace('_', ' ') }}: {{ interview.time }}
                    </span>
                  </div>
                </td>
                <td>{{ app.company }}</td>
                <td>
                  <div class="d-flex align-items-center gap-2">
                    <span :class="['badge rounded-pill px-3 py-2', getStatusClass(app.status)]">{{ app.status }}</span>
                    
                    <!-- OFFER DOWNLOAD BUTTON -->
                    <a v-if="app.status === 'Selected' && app.offer_url" 
                       :href="app.offer_url" 
                       download 
                       class="btn btn-sm btn-success rounded-pill px-3 py-1 fw-bold extra-small text-white text-decoration-none">
                      <i class="fas fa-file-download me-1"></i> Download Offer
                    </a>
                  </div>
                </td>
                <td class="text-end pe-4 small text-muted">{{ app.applied_on }}</td>
              </tr>
              <tr v-if="history.length === 0">
                <td colspan="4" class="text-center py-5 text-muted">No applications found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 4. PROFILE SECTION -->
    <div v-if="activeTab === 'profile'" class="fade-in">
      <div class="row g-4">
        <div class="col-lg-7">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
            <h5 class="fw-bold mb-4">Identity Metadata</h5>
            <div class="mb-3"><label class="small fw-bold text-muted">Full Official Name</label><input v-model="profile.full_name" class="form-control rounded-pill px-3"></div>
            <div class="row g-3 mb-4">
              <div class="col-md-6"><label class="small fw-bold text-muted">Academic Dept</label><input v-model="profile.department" class="form-control rounded-pill px-3"></div>
              <div class="col-md-6"><label class="small fw-bold text-muted">Enrollment ID</label><input v-model="profile.enrollment" class="form-control rounded-pill px-3" disabled></div>
            </div>
            <button class="btn btn-primary rounded-pill px-5 fw-bold" @click="updateProfile" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span> Save Changes
            </button>
          </div>
        </div>
        <div class="col-lg-5">
          <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100 text-center">
            <h5 class="fw-bold mb-4">Portfolio (PDF)</h5>
            <div class="upload-zone p-4 border border-dashed rounded-4 mb-3" @click="$refs.resumeInput.click()" style="cursor:pointer">
              <i class="fas fa-cloud-upload-alt fa-3x text-primary mb-3"></i>
              <p class="small text-muted">Click to select verified PDF resume</p>
              <input type="file" ref="resumeInput" class="d-none" accept=".pdf" @change="uploadResume">
            </div>
            <div v-if="profile.resume" class="badge bg-info-subtle text-info p-2 w-100">Current: {{ profile.resume }}</div>
            <small v-else class="text-danger d-block mt-2">Resume is required for applications.</small>
          </div>
        </div>
      </div>
    </div>

    <!-- 5. ATS SCANNER -->
    <div v-if="activeTab === 'ats'" class="fade-in">
        <div class="row g-4">
            <div class="col-lg-5">
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100">
                    <h5 class="fw-bold mb-3">ATS Intelligence Scorer</h5>
                    <p class="small text-muted mb-4">Compare your synchronized institutional portfolio against target job descriptions.</p>
                    <div class="mb-4">
                        <label class="small fw-bold text-muted mb-2">Job Description</label>
                        <textarea v-model="ats.jd" class="form-control rounded-4 p-3" rows="8" placeholder="Paste requirements..."></textarea>
                    </div>
                    <button class="btn btn-primary w-100 rounded-pill py-2 fw-bold" @click="runAtsScan" :disabled="ats.loading || !profile.resume">
                        <i class="fas fa-microchip me-2"></i> Run Optimization Scan
                    </button>
                </div>
            </div>
            <div class="col-lg-7">
                <div v-if="ats.score === null" class="card border-0 shadow-sm rounded-4 p-5 bg-white h-100 d-flex align-items-center justify-content-center text-center opacity-50">
                    <i class="fas fa-robot fa-4x mb-4 text-primary"></i>
                    <h5 class="fw-bold">Ready for Analysis</h5>
                </div>
                <div v-else class="card border-0 shadow-sm rounded-4 p-4 bg-white h-100 animate-entrance">
                    <div class="text-center mb-4">
                        <div class="display-4 fw-bold" :class="ats.score > 70 ? 'text-success' : 'text-warning'">{{ ats.score }}%</div>
                        <p class="text-muted fw-bold text-uppercase small">Institutional Match Score</p>
                    </div>
                    <h6 class="fw-bold mb-3">Key Insight Analysis</h6>
                    <div class="mb-4">
                        <div v-for="match in ats.matches" :key="match" class="badge bg-success-subtle text-success rounded-pill px-3 py-2 me-2 mb-2">{{ match }}</div>
                        <div v-for="miss in ats.missing" :key="miss" class="badge bg-danger-subtle text-danger rounded-pill px-3 py-2 me-2 mb-2">Missing: {{ miss }}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL: RESCHEDULE -->
    <div v-if="rescheduleModal.show" class="modal show d-block" style="background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 1060;">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 border-0 shadow-lg p-4">
          <h5 class="fw-bold mb-3">Request Timing Change</h5>
          <div class="mb-4">
            <label class="small fw-bold text-muted mb-1">Remarks / Availability</label>
            <textarea v-model="rescheduleModal.remarks" class="form-control rounded-4 p-3" rows="3" placeholder="Suggest a better time..."></textarea>
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-primary rounded-pill w-100 fw-bold py-2" @click="handleInterviewResponse(rescheduleModal.id, 'reschedule_requested')" :disabled="loading">Send Request</button>
            <button class="btn btn-light rounded-pill w-100 py-2" @click="rescheduleModal.show = false">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StudentDashboard',
  props: ['currentTab'],
  data() {
    return {
      activeTab: this.currentTab || 'dashboard',
      loading: false,
      loadingResume: false,
      searchQuery: '',
      profile: { full_name: '', cgpa: 0, department: '', enrollment: '', resume: null },
      history: [],
      availableDrives: [],
      notifications: [],
      rescheduleModal: { show: false, id: null, remarks: '' },
      ats: { jd: '', score: null, matches: [], missing: [], feedback: '', loading: false }
    }
  },
  computed: {
    pendingInterviews() {
      const pending = [];
      this.history.forEach(app => {
        if (app.interviews) {
          app.interviews.forEach(i => { if (i.status === 'invited') pending.push({ ...i, company: app.company, drive: app.drive }); });
        }
      });
      return pending;
    }
  },
  watch: {
    currentTab(newVal) {
      this.activeTab = newVal || 'dashboard';
      this.syncData();
    }
  },
  methods: {
    setTab(t) { this.$emit('update:current-tab', t); },
    async syncData() {
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` };
      const [p, his, n] = await Promise.all([
        fetch('/api/v1/candidate/profile', { headers: h }),
        fetch('/api/v1/candidate/application-tracking', { headers: h }),
        fetch('/api/v1/candidate/notifications', { headers: h })
      ]);
      if(p.ok) this.profile = await p.json();
      if(his.ok) this.history = await his.json();
      if(n.ok) this.notifications = await n.json();
      if(this.activeTab === 'drives') this.fetchDrives();
    },
    async fetchDrives() {
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` };
      const res = await fetch(`/api/v1/candidate/available-drives?q=${this.searchQuery}`, { headers: h });
      if(res.ok) this.availableDrives = await res.json();
    },
    async applyForDrive(driveId) {
      if(!this.profile.resume) { alert("Please upload a resume before applying."); return; }
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
      const res = await fetch('/api/v1/candidate/submit-application', { 
        method: 'POST', headers: h, body: JSON.stringify({ drive_id: driveId }) 
      });
      if(res.ok) { this.setTab('history'); this.syncData(); }
      else { const d = await res.json(); alert(d.error || "Application failed."); }
    },
    async updateProfile() {
      this.loading = true;
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
      try {
        const res = await fetch('/api/v1/candidate/update-profile', { 
          method: 'PATCH', headers: h, body: JSON.stringify({ fullname: this.profile.full_name, department: this.profile.department }) 
        });
        if(res.ok) { alert("Profile updated."); this.syncData(); }
      } finally { this.loading = false; }
    },
    async uploadResume(e) {
      const file = e.target.files[0];
      if(!file) return;
      this.loadingResume = true;
      const formData = new FormData();
      formData.append('resume', file);
      try {
        const res = await fetch('/api/v1/candidate/upload-resume', { 
          method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` }, body: formData 
        });
        const d = await res.json();
        if(res.ok) {
          this.profile.resume = d.filename;
          await fetch('/api/v1/candidate/update-profile', { 
            method: 'PATCH', headers: { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ resume_name: d.filename }) 
          });
          this.syncData();
        }
      } finally { this.loadingResume = false; }
    },
    async handleInterviewResponse(id, action) {
      this.loading = true;
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
      try {
        const res = await fetch('/api/v1/candidate/interviews/respond', { 
          method: 'POST', headers: h, body: JSON.stringify({ id, action, remarks: this.rescheduleModal.remarks }) 
        });
        if(res.ok) { this.rescheduleModal.show = false; this.syncData(); }
      } finally { this.loading = false; }
    },
    openRescheduleModal(invitation) {
      this.rescheduleModal = { show: true, id: invitation.id, remarks: '' };
    },
    runAtsScan() {
        this.ats.loading = true;
        const keywords = ['python', 'javascript', 'vue', 'sql', 'rest api', 'flask', 'git'];
        const jdLower = this.ats.jd.toLowerCase();
        this.ats.matches = keywords.filter(k => jdLower.includes(k));
        this.ats.missing = ['docker', 'kubernetes', 'aws'].filter(k => jdLower.includes(k));
        this.ats.score = Math.round((this.ats.matches.length / (this.ats.matches.length + this.ats.missing.length)) * 100);
        setTimeout(() => { this.ats.loading = false; }, 800);
    },
    getStatusClass(s) {
      const c = { 'Selected': 'bg-success', 'Rejected': 'bg-danger', 'Interviewing': 'bg-primary', 'Shortlisted': 'bg-info text-dark' };
      return c[s] || 'bg-warning text-dark';
    },
    getInterviewStatusClass(s) {
      const c = { 'confirmed': 'bg-success', 'reschedule_requested': 'bg-warning text-dark', 'invited': 'bg-info text-dark' };
      return c[s] || 'bg-light text-dark';
    }
  },
  mounted() { this.syncData(); }
}
</script>

<style scoped>
.extra-small { font-size: 0.65rem; }
.bg-warning-subtle { background-color: #fff9db; }
.rounded-4 { border-radius: 1.25rem !important; }
.fade-in { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
.drive-card { transition: all 0.3s ease; border: 1px solid rgba(0,0,0,0.05); }
.shadow-hover:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(13, 110, 253, 0.1) !important; border-color: #0d6efd; }
.upload-zone { border-style: dashed !important; background: #f8fafd; }
.text-truncate-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>