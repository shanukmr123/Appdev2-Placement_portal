<template>
  <div class="company-workspace container-fluid py-4 fade-in">
    <!-- Institutional Navigation -->
    <ul class="nav nav-pills mb-4 gap-2 bg-white p-2 rounded-pill shadow-sm d-inline-flex border">
      <li class="nav-item">
        <button :class="['nav-link rounded-pill px-4', activeTab === 'dashboard' ? 'active' : '']" @click="activeTab = 'dashboard'">Dashboard</button>
      </li>
      <li class="nav-item">
        <button :class="['nav-link rounded-pill px-4', activeTab === 'profile' ? 'active' : '']" @click="activeTab = 'profile'">Profile Settings</button>
      </li>
    </ul>

    <!-- 1. DASHBOARD VIEW -->
    <div v-if="activeTab === 'dashboard'" class="fade-in">
      <div class="card border-0 shadow-sm rounded-4 p-4 mb-4 bg-white">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-center">
          <div>
            <h2 class="fw-bold text-dark mb-1">{{ company.name }}</h2>
            <div class="d-flex gap-2 align-items-center">
              <span :class="['badge rounded-pill px-3 py-2', company.status === 'approved' ? 'bg-success' : 'bg-warning text-dark']">
                {{ company.status === 'approved' ? 'VERIFIED PARTNER' : 'VERIFICATION PENDING' }}
              </span>
              <small class="text-muted">{{ company.industry }} Sector</small>
            </div>
          </div>
          <div class="mt-3 mt-md-0" v-if="company.status === 'approved'">
            <button class="btn btn-primary rounded-pill px-4 fw-bold shadow-sm" @click="showDriveModal = true">
              <i class="fas fa-plus me-2"></i> Launch New Drive
            </button>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div v-if="drives.length === 0" class="col-12 text-center py-5">
          <div class="card border-0 shadow-sm rounded-4 p-5 bg-white text-muted">
            <i class="fas fa-briefcase fa-3x mb-3 opacity-25"></i>
            <p>No active recruitment campaigns.</p>
          </div>
        </div>
        <div v-for="drive in drives" :key="drive.id" class="col-md-6 col-lg-4">
          <div class="card border-0 shadow-sm rounded-4 h-100 bg-white p-4 drive-card shadow-hover">
            <div class="d-flex justify-content-between mb-3">
              <span :class="['badge rounded-pill px-3 py-2 text-uppercase extra-small', drive.status === 'active' ? 'bg-success-subtle text-success' : 'bg-primary-subtle text-primary']">
                {{ drive.status }}
              </span>
              <span class="fw-bold text-success">{{ drive.package }}</span>
            </div>
            <h5 class="fw-bold text-dark mb-2">{{ drive.title }}</h5>
            <div class="d-flex justify-content-between align-items-center pt-3 border-top mt-3">
              <span class="small fw-bold text-primary">{{ drive.applicants }} Applicants</span>
              <button class="btn btn-sm btn-outline-primary rounded-pill px-3" @click="viewPipeline(drive)">Manage Pipeline</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. PIPELINE VIEW -->
    <div v-if="activeTab === 'pipeline'" class="fade-in">
        <div class="d-flex align-items-center mb-4 gap-3">
            <button class="btn btn-light rounded-circle shadow-sm" @click="activeTab = 'dashboard'">
                <i class="fas fa-arrow-left"></i>
            </button>
            <div>
                <h4 class="fw-bold mb-0">{{ selectedDrive.title }} Pipeline</h4>
                <p class="text-muted extra-small mb-0">Reviewing candidates for {{ selectedDrive.package }} package</p>
            </div>
        </div>

        <div class="card border-0 shadow-sm rounded-4 bg-white overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light">
                        <tr class="extra-small text-muted fw-bold text-uppercase">
                            <th class="ps-4 py-3">Candidate & Schedule</th>
                            <th>Current Stage</th>
                            <th>Eligibility</th>
                            <th class="text-end pe-4">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="app in applicants" :key="app.workflow_id">
                            <td class="ps-4 py-3">
                                <div class="fw-bold text-dark mb-1">{{ app.candidate_name }}</div>
                                
                                <!-- Interview Schedule Visibility -->
                                <div v-if="app.interviews && app.interviews.length > 0" class="mt-2">
                                  <div v-for="iv in app.interviews" :key="iv.id" class="mb-1">
                                    <span :class="['badge rounded-pill extra-small px-2 py-1', getIvBadgeClass(iv.status)]">
                                      <i class="fas fa-calendar-check me-1"></i> {{ iv.time }}
                                    </span>
                                    <div v-if="iv.student_notes" class="extra-small text-danger mt-1">
                                      <i class="fas fa-comment-dots me-1"></i> Note: {{ iv.student_notes }}
                                    </div>
                                  </div>
                                </div>
                                <div v-else class="extra-small text-muted">No interviews scheduled.</div>
                            </td>
                            <td>
                                <select class="form-select form-select-sm rounded-pill w-auto border-0 bg-light" 
                                    v-model="app.stage" @change="updateApplicantStatus(app.workflow_id, app.stage)">
                                    <option value="Applied">Applied</option>
                                    <option value="Shortlisted">Shortlisted</option>
                                    <option value="Interviewing">Interviewing</option>
                                    <option value="Selected">Selected</option>
                                    <option value="Rejected">Rejected</option>
                                </select>
                            </td>
                            <td><span class="badge bg-light text-dark border">{{ app.cgpa }} CGPA</span></td>
                            <td class="text-end pe-4">
                                <div class="d-flex justify-content-end gap-2">
                                  <button class="btn btn-sm btn-info text-white rounded-pill px-3 fw-bold" 
                                      @click="openInterviewModal(app)">
                                      <i class="fas fa-clock me-1"></i> {{ app.interviews.length > 0 ? 'Reschedule' : 'Schedule' }}
                                  </button>
                                  <button v-if="app.stage === 'Selected'" 
                                      class="btn btn-sm btn-success rounded-pill px-3 fw-bold"
                                      @click="openOfferModal(app)">
                                      <i class="fas fa-file-signature me-1"></i> Issue Offer
                                  </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 3. PROFILE VIEW -->
    <div v-if="activeTab === 'profile'" class="fade-in">
      <div class="card border-0 shadow-sm rounded-4 p-5 bg-white mx-auto" style="max-width: 800px;">
        <h4 class="fw-bold mb-4">Enterprise Identity Management</h4>
        <form @submit.prevent="updateProfile">
          <div class="mb-3">
            <label class="form-label small fw-bold text-muted">Legal Entity Name</label>
            <input v-model="profileForm.name" type="text" class="form-control rounded-pill px-3" required>
          </div>
          <div class="row g-3 mb-4">
            <div class="col-md-6">
              <label class="form-label small fw-bold text-muted">Industry Domain</label>
              <input v-model="profileForm.industry" type="text" class="form-control rounded-pill px-3" required>
            </div>
            <div class="col-md-6">
              <label class="form-label small fw-bold text-muted">Corporate Website</label>
              <input v-model="profileForm.website" type="url" class="form-control rounded-pill px-3" placeholder="https://company.com">
            </div>
          </div>
          <button type="submit" class="btn btn-primary rounded-pill px-5 fw-bold" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Synchronize Records
          </button>
        </form>
      </div>
    </div>

    <!-- MODALS -->
    <!-- Drive Creation Modal -->
    <div v-if="showDriveModal" class="modal show d-block" style="background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 1050;">
      <div class="modal-dialog modal-dialog-centered">
        <form @submit.prevent="submitDrive" class="modal-content rounded-4 p-4 border-0 shadow-lg">
          <h5 class="fw-bold mb-4">Launch Placement Campaign</h5>
          <div class="mb-3">
            <label class="small fw-bold text-muted">Job Title (Role)</label>
            <input v-model="driveForm.title" class="form-control rounded-pill px-3" required>
          </div>
          <div class="mb-3">
            <label class="small fw-bold text-muted">CTC (LPA)</label>
            <input v-model="driveForm.package" class="form-control rounded-pill px-3" required>
          </div>
          <div class="mb-4">
            <label class="small fw-bold text-muted">Eligibility (Min CGPA)</label>
            <input v-model="driveForm.eligibility" type="number" step="0.1" class="form-control rounded-pill px-3" required>
          </div>
          <div class="mb-4">
            <label class="small fw-bold text-muted">Description</label>
            <textarea v-model="driveForm.description" class="form-control rounded-4 px-3 py-2" rows="3" required></textarea>
          </div>
          <div class="d-flex gap-2">
            <button type="submit" class="btn btn-primary w-100 rounded-pill py-2 fw-bold" :disabled="loading">Submit for Review</button>
            <button type="button" class="btn btn-light w-100 rounded-pill py-2" @click="showDriveModal = false">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Interview Modal -->
    <div v-if="showInterviewModal" class="modal show d-block" style="background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 1060;">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content rounded-4 p-4 border-0 shadow-lg">
          <h5 class="fw-bold mb-4">Schedule Interview Slot</h5>
          <div class="mb-3">
            <label class="small fw-bold text-muted">Proposed Date & Time</label>
            <input v-model="interviewForm.time" type="datetime-local" class="form-control rounded-pill px-3" required>
          </div>
          <div class="mb-4">
            <label class="small fw-bold text-muted">Meeting Link / Instructions</label>
            <input v-model="interviewForm.link" type="text" class="form-control rounded-pill px-3" placeholder="Zoom/Google Meet Link" required>
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-info text-white w-100 rounded-pill py-2 fw-bold" @click="sendInterviewInvite" :disabled="loading">Dispatch Invite</button>
            <button class="btn btn-light w-100 rounded-pill py-2" @click="showInterviewModal = false">Cancel</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Offer Modal -->
    <div v-if="offerModal.show" class="modal show d-block" style="background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); z-index: 1060;">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content rounded-4 p-4 border-0 shadow-lg">
                <h5 class="fw-bold mb-4">Issue Offer Letter</h5>
                <p class="small text-muted mb-4">Generating for <strong>{{ offerModal.applicant?.candidate_name }}</strong>.</p>
                <div class="mb-3">
                    <label class="small fw-bold text-muted">Role</label>
                    <input v-model="offerModal.role" class="form-control rounded-pill px-3">
                </div>
                <div class="mb-4">
                    <label class="small fw-bold text-muted">Final CTC</label>
                    <input v-model="offerModal.package" class="form-control rounded-pill px-3">
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-success w-100 rounded-pill py-2 fw-bold" @click="generateOffer" :disabled="loading">Generate PDF</button>
                  <button class="btn btn-light w-100 rounded-pill py-2" @click="offerModal.show = false">Discard</button>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CompanyDashboard',
  data() {
    return {
      activeTab: 'dashboard',
      loading: false,
      showDriveModal: false,
      showInterviewModal: false,
      company: { name: '', status: '', industry: '', website: '' },
      drives: [],
      applicants: [],
      selectedDrive: {},
      selectedApplicant: {},
      profileForm: { name: '', industry: '', website: '' },
      driveForm: { title: '', package: '', description: '', eligibility: 6.0 },
      interviewForm: { time: '', link: '' },
      offerModal: { show: false, applicant: null, role: '', package: '' }
    }
  },
  methods: {
    getIvBadgeClass(status) {
      if (status === 'confirmed') return 'bg-success text-white';
      if (status === 'reschedule_requested') return 'bg-danger text-white';
      return 'bg-info text-white';
    },
    async syncData() {
      const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` };
      const res = await fetch('/api/v1/enterprise/profile-status', { headers: h });
      if(res.ok) {
        this.company = await res.json();
        this.profileForm = { ...this.company };
        const d = await fetch('/api/v1/enterprise/my-drives', { headers: h });
        if(d.ok) this.drives = await d.json();
      }
    },
    async viewPipeline(drive) {
        this.selectedDrive = drive;
        const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}` };
        const res = await fetch(`/api/v1/enterprise/pipeline/applicants/${drive.id}`, { headers: h });
        if(res.ok) {
            this.applicants = await res.json();
            this.activeTab = 'pipeline';
        }
    },
    async updateApplicantStatus(workflowId, stage) {
        const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
        await fetch('/api/v1/enterprise/pipeline/update-stage', {
            method: 'PATCH',
            headers: h,
            body: JSON.stringify({ workflow_id: workflowId, stage })
        });
    },
    async updateProfile() {
      this.loading = true;
      const res = await fetch('/api/v1/enterprise/update-profile', {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(this.profileForm)
      });
      if(res.ok) this.syncData();
      this.loading = false;
    },
    async submitDrive() {
      this.loading = true;
      const res = await fetch('/api/v1/enterprise/publish-drive', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(this.driveForm)
      });
      if(res.ok) { 
        this.showDriveModal = false; 
        this.syncData(); 
      }
      this.loading = false;
    },
    openInterviewModal(applicant) {
        this.selectedApplicant = applicant;
        this.showInterviewModal = true;
    },
    async sendInterviewInvite() {
        this.loading = true;
        const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
        const formattedTime = this.interviewForm.time.replace(' ', 'T');
        const res = await fetch('/api/v1/enterprise/interviews/schedule', {
            method: 'POST',
            headers: h,
            body: JSON.stringify({ 
                workflow_id: this.selectedApplicant.workflow_id,
                time: formattedTime,
                link: this.interviewForm.link
            })
        });
        if(res.ok) {
            this.showInterviewModal = false;
            this.viewPipeline(this.selectedDrive);
        } else {
            const d = await res.json();
            alert(d.error || "Invite failed.");
        }
        this.loading = false;
    },
    openOfferModal(app) {
        this.offerModal = { 
          show: true, 
          applicant: app, 
          role: this.selectedDrive.title, 
          package: this.selectedDrive.package 
        };
    },
    async generateOffer() {
        this.loading = true;
        const h = { 'Authorization': `Bearer ${localStorage.getItem('shaanu_token')}`, 'Content-Type': 'application/json' };
        const res = await fetch('/api/v1/enterprise/pipeline/generate-offer', {
            method: 'POST',
            headers: h,
            body: JSON.stringify({
                workflow_id: this.offerModal.applicant.workflow_id,
                role: this.offerModal.role,
                package: this.offerModal.package
            })
        });
        if(res.ok) {
            alert("Offer letter generated.");
            this.offerModal.show = false;
        }
        this.loading = false;
    }
  },
  mounted() { this.syncData(); }
}
</script>

<style scoped>
.rounded-4 { border-radius: 1.25rem !important; }
.extra-small { font-size: 0.65rem; }
.fade-in { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
.nav-link.active { background-color: #1e3c72; color: white; }
.drive-card { border: 1px solid rgba(0,0,0,0.05); transition: 0.3s; }
.shadow-hover:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important; border-color: #1e3c72; }
.bg-success-subtle { background-color: #d1e7dd; }
.bg-primary-subtle { background-color: #cfe2ff; }
</style>