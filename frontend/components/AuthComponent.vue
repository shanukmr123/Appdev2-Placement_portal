<template>
  <div class="auth-portal min-vh-100 d-flex align-items-center justify-content-center bg-light">
    <div class="card border-0 shadow-lg rounded-4 overflow-hidden" style="max-width: 900px; width: 100%;">
      <div class="row g-0">
        <!-- Left Panel: Branding -->
        <div class="col-lg-5 bg-primary text-white p-5 d-none d-lg-flex flex-column justify-content-center">
          <h1 class="fw-bold mb-3">ShaanU</h1>
          <p class="lead opacity-75">Institutional Placement Gateway v1.0</p>
          <hr class="w-25 opacity-50 mb-4">
          <ul class="list-unstyled small opacity-75">
          
          </ul>
          <small class="opacity-50 mt-4">© 2024 ShaanU Academic Portal. Strictly for institutional use.</small>
        </div>
        
        <!-- Right Panel: Forms -->
        <div class="col-lg-7 p-5 bg-white">
          <div class="text-center mb-4">
            <h3 class="fw-bold text-dark">{{ mode === 'login' ? 'Institutional Access' : 'Create Identity' }}</h3>
            <p class="text-muted small">Verify your identity to enter the placement ecosystem.</p>
          </div>

          <form @submit.prevent="handleSubmit" :class="['form-body needs-validation', validated ? 'was-validated' : '']" novalidate>
            <!-- Email -->
            <div class="mb-3">
              <label class="form-label small fw-bold text-muted">Institutional Email</label>
              <input 
                v-model="form.email" 
                type="email" 
                class="form-control rounded-pill px-4 py-2 shadow-sm border-light" 
                required 
                placeholder="name@shaanu.edu"
              >
              <div class="invalid-feedback extra-small ps-3">Provide a valid @shaanu.edu email.</div>
            </div>

            <!-- Password -->
            <div class="mb-3">
              <label class="form-label small fw-bold text-muted">Access Secret</label>
              <input 
                v-model="form.password" 
                type="password" 
                class="form-control rounded-pill px-4 py-2 shadow-sm border-light" 
                required 
                minlength="6"
                placeholder="Min. 6 characters"
              >
            </div>

            <!-- Registration Logic -->
            <div v-if="mode === 'register'" class="registration-fields fade-in">
              <div class="mb-3">
                <label class="form-label small fw-bold text-muted">Username Handle</label>
                <input v-model="form.username" type="text" class="form-control rounded-pill px-4 py-2 border-light shadow-sm" required placeholder="e.g. shaanu_user">
              </div>

              <!-- Role Selector -->
              <div class="mb-4">
                <label class="form-label small fw-bold d-block mb-2 text-muted text-center">Identity Category</label>
                <div class="btn-group w-100 rounded-pill overflow-hidden border shadow-sm">
                  <input type="radio" class="btn-check" v-model="form.role" value="student" id="role-student">
                  <label class="btn btn-outline-primary border-0" for="role-student">Student</label>
                  
                  <input type="radio" class="btn-check" v-model="form.role" value="company" id="role-company">
                  <label class="btn btn-outline-primary border-0" for="role-company">Partner</label>
                </div>
              </div>

              <!-- Conditional Student Fields -->
              <div v-if="form.role === 'student'" class="row g-2 mb-3">
                <div class="col-12"><input v-model="form.fullname" class="form-control rounded-pill px-4 shadow-sm border-light" placeholder="Full Legal Name" required></div>
                <div class="col-md-6"><input v-model="form.enrollment" class="form-control rounded-pill px-4 shadow-sm border-light" placeholder="Enrollment ID" required></div>
                <div class="col-md-6"><input v-model="form.cgpa" type="number" step="0.01" class="form-control rounded-pill px-4 shadow-sm border-light" placeholder="CGPA (0-10)" required></div>
              </div>

              <!-- Conditional Company Fields -->
              <div v-if="form.role === 'company'" class="row g-2 mb-3">
                <div class="col-12"><input v-model="form.company_name" class="form-control rounded-pill px-4 shadow-sm border-light" placeholder="Legal Company Name" required></div>
                <div class="col-12"><input v-model="form.industry" class="form-control rounded-pill px-4 shadow-sm border-light" placeholder="Industry Domain" required></div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary w-100 rounded-pill py-2 fw-bold shadow-sm mb-3" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ mode === 'login' ? 'Validate Identity' : 'Enroll Identity' }}
            </button>
            
            <div class="text-center">
              <button type="button" class="btn btn-link text-decoration-none small text-muted" @click="toggleMode">
                {{ mode === 'login' ? "New candidate or partner? Enroll here" : "Already registered? Verify access" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AuthComponent',
  data() {
    return {
      mode: 'login',
      loading: false,
      validated: false,
      form: { 
        email: '', password: '', role: 'student', username: '', 
        fullname: '', enrollment: '', cgpa: '', 
        company_name: '', industry: '', department: 'Computer Science' 
      }
    }
  },
  methods: {
    toggleMode() {
      this.mode = this.mode === 'login' ? 'register' : 'login';
      this.validated = false;
    },
    async handleSubmit(event) {
      const form = event.target;
      this.validated = true;

      if (!form.checkValidity()) {
        event.stopPropagation();
        return;
      }

      this.loading = true;
      const baseUrl = window.location.origin.includes('localhost') ? '' : 'http://localhost:5010';
      const endpoint = this.mode === 'login' ? '/api/v1/gatekeeper/verify-access' : 
                       (this.form.role === 'student' ? '/api/v1/gatekeeper/enroll/candidate' : '/api/v1/gatekeeper/enroll/enterprise');
      
      try {
        const res = await fetch(`${baseUrl}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.form)
        });
        
        const data = await res.json();
        
        if (res.ok) {
          if (this.mode === 'login') {
            this.$emit('login-success', data);
          } else {
            alert("Institutional identity provisioned. Please sign in.");
            this.mode = 'login';
          }
        } else {
          alert(data.error || "Institutional access denied.");
        }
      } catch (err) {
        alert("Ecosystem link failure. Ensure the ShaanU Backend is active on port 5010.");
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.rounded-4 { border-radius: 1.25rem !important; }
.extra-small { font-size: 0.7rem; }
.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.btn-outline-primary { border-color: #dee2e6; color: #6c757d; }
.btn-check:checked + .btn-outline-primary { background-color: #0d6efd; color: white; border-color: #0d6efd; }
</style>