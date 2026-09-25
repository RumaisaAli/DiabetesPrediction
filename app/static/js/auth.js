/**
 * Auth Client Service
 * Manages JWT tokens, session states, and role-based client routing guards.
 */

const Auth = {
    TOKEN_KEY: "gluco_jwt_token",
    USER_KEY: "gluco_user_profile",

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    setToken(token) {
        localStorage.setItem(this.TOKEN_KEY, token);
        // Also set cookie for PDF downloads and browser navigations
        document.cookie = `access_token=Bearer ${token}; path=/; max-age=86400; SameSite=Lax`;
    },

    getUser() {
        const u = localStorage.getItem(this.USER_KEY);
        try {
            return u ? JSON.parse(u) : null;
        } catch {
            return null;
        }
    },

    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    clear() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        localStorage.clear();
        sessionStorage.clear();
        document.cookie = "access_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    },

    async fetchWithAuth(url, options = {}) {
        const token = this.getToken();
        options.headers = options.headers || {};
        if (token) {
            options.headers["Authorization"] = `Bearer ${token}`;
        }
        const res = await fetch(url, options);
        if (res.status === 401) {
            this.clear();
            window.location.replace("/login?msg=Session expired. Please log in again.");
            return res;
        }
        if (res.status === 403) {
            // Role access denied (TC-20)
            window.location.replace("/login?msg=Access denied: Administrative privileges required.");
            return res;
        }
        return res;
    },

    requireAuth(allowedRoles = []) {
        const token = this.getToken();
        const user = this.getUser();

        if (!token || !user) {
            this.clear();
            window.location.replace("/login?msg=Please log in to access this page.");
            return null;
        }

        if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
            // Access denied -> redirect to login (TC-20)
            window.location.replace(`/login?msg=Access denied: Page restricted to ${allowedRoles.join('/')} accounts.`);
            return null;
        }

        return user;
    },

    logout() {
        this.clear();
        try {
            fetch("/api/auth/logout", { method: "POST" });
        } catch (e) { }
        window.location.replace("/logout");
    },

    initPage(pageTitle, allowedRoles = []) {
        const user = this.requireAuth(allowedRoles);
        if (!user) return null;

        // Populate topbar if present
        const titleEl = document.getElementById("page-title-display");
        if (titleEl) titleEl.textContent = pageTitle;

        const userNameEl = document.getElementById("current-user-name");
        if (userNameEl) userNameEl.textContent = user.username;

        const roleBadgeEl = document.getElementById("current-user-role");
        if (roleBadgeEl) {
            roleBadgeEl.textContent = user.role.toUpperCase();
            roleBadgeEl.className = `role-pill ${user.role}`;
        }

        // Hide admin link for non-admins
        const adminNav = document.getElementById("nav-admin-link");
        if (adminNav) {
            if (user.role === "admin") {
                adminNav.style.display = "flex";
            } else {
                adminNav.style.display = "none";
            }
        }

        return user;
    }
};

const UI = {
    showToast(message, type = "info") {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            document.body.appendChild(container);
        }
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        const iconName = type === "success" ? "check_circle" : (type === "error" ? "error" : "info");
        toast.innerHTML = `
            <span class="material-symbols-outlined toast-icon">${iconName}</span>
            <span style="flex: 1;">${message}</span>
            <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;color:var(--text-muted);display:flex;align-items:center;">
                <span class="material-symbols-outlined" style="font-size: 16px;">close</span>
            </button>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(10px)";
            setTimeout(() => toast.remove(), 250);
        }, 4000);
    },

    openSupportModal() {
        let modal = document.getElementById("support-info-modal");
        if (!modal) {
            this.injectSupportModal();
            modal = document.getElementById("support-info-modal");
        }
        modal.classList.add("show");
    },

    closeSupportModal() {
        const modal = document.getElementById("support-info-modal");
        if (modal) modal.classList.remove("show");
    },

    openForgotPasswordModal() {
        let modal = document.getElementById("forgot-password-modal");
        if (!modal) {
            this.injectForgotPasswordModal();
            modal = document.getElementById("forgot-password-modal");
        }
        modal.classList.add("show");
    },

    closeForgotPasswordModal() {
        const modal = document.getElementById("forgot-password-modal");
        if (modal) modal.classList.remove("show");
    },

    injectSupportModal() {
        const div = document.createElement("div");
        div.id = "support-info-modal";
        div.className = "modal-backdrop";
        div.onclick = (e) => {
            if (e.target === div) UI.closeSupportModal();
        };
        div.innerHTML = `
            <div class="modal-card">
                <div class="modal-header">
                    <div class="modal-title-group">
                        <div class="modal-title-icon">
                            <span class="material-symbols-outlined">medical_information</span>
                        </div>
                        <div>
                            <div class="modal-title">Intelligent Diabetes Risk Predictor</div>
                            <div class="modal-subtitle">CS619 Final-Year Project • Clinical Decision Support</div>
                        </div>
                    </div>
                    <button class="modal-close-btn" onclick="UI.closeSupportModal()" title="Close">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>

                <div class="modal-tabs">
                    <button class="modal-tab active" id="tab-btn-sys" onclick="UI.switchSupportTab('sys')">System Overview</button>
                    <button class="modal-tab" id="tab-btn-ref" onclick="UI.switchSupportTab('ref')">Clinical References</button>
                    <button class="modal-tab" id="tab-btn-help" onclick="UI.switchSupportTab('help')">Support & FAQ</button>
                </div>

                <div class="modal-body" id="modal-tab-content-sys">
                    <div style="margin-bottom: 16px;">
                        <h4 style="font-size: 14px; font-weight: 700; color: var(--primary); margin-bottom: 6px;">Academic Context & Architecture</h4>
                        <p style="font-size: 13px; color: var(--text-muted); line-height: 1.6;">
                            This full-stack clinical platform predicts diabetic risk from non-invasive vital signs using machine learning. It was developed to fulfill the final-year software engineering requirements of CS619.
                        </p>
                    </div>
                    
                    <div style="background: var(--surface-low); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 14px 18px; margin-bottom: 16px;">
                        <div class="info-row"><span class="info-label">Project Title:</span><span class="info-value">Intelligent Diabetes Risk Predictor</span></div>
                        <div class="info-row"><span class="info-label">Group ID:</span><span class="info-value">S26PROJECTA7FFD</span></div>
                        <div class="info-row"><span class="info-label">Course:</span><span class="info-value">CS619 Software Engineering</span></div>
                        <div class="info-row"><span class="info-label">Backend:</span><span class="info-value">FastAPI + PostgreSQL (SQLAlchemy 2.0)</span></div>
                        <div class="info-row"><span class="info-label">ML Models:</span><span class="info-value">Logistic Reg, SVM, Decision Tree, Neural Net</span></div>
                        <div class="info-row" style="border-bottom: none;"><span class="info-label">Deployment Format:</span><span class="info-value" style="color: var(--success);">Pure Python Modules (Zero Runtime Pickle)</span></div>
                    </div>
                </div>

                <div class="modal-body" id="modal-tab-content-ref" style="display: none;">
                    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">
                        Clinical reference parameters adapted from the American Diabetes Association (ADA) diagnostic standards:
                    </p>
                    <table class="ref-table">
                        <thead>
                            <tr>
                                <th>Clinical Indicator</th>
                                <th>Optimal / Normal</th>
                                <th>Elevated / Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Plasma Glucose</strong></td>
                                <td>70 – 99 mg/dL</td>
                                <td>≥ 126 mg/dL (Diabetic Range)</td>
                            </tr>
                            <tr>
                                <td><strong>Blood Pressure (Diastolic)</strong></td>
                                <td>60 – 79 mm Hg</td>
                                <td>≥ 90 mm Hg (Hypertension)</td>
                            </tr>
                            <tr>
                                <td><strong>Body Mass Index (BMI)</strong></td>
                                <td>18.5 – 24.9 kg/m²</td>
                                <td>≥ 30.0 kg/m² (Obesity)</td>
                            </tr>
                            <tr>
                                <td><strong>Serum Insulin (Fasting)</strong></td>
                                <td>16 – 166 mu U/ml</td>
                                <td>> 200 mu U/ml (Hyperinsulinemia)</td>
                            </tr>
                            <tr>
                                <td><strong>Skin Thickness</strong></td>
                                <td>10 – 30 mm</td>
                                <td>> 35 mm</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="modal-body" id="modal-tab-content-help" style="display: none;">
                    <div style="margin-bottom: 14px;">
                        <h4 style="font-size: 13px; font-weight: 700; color: var(--primary);">Need Technical Assistance?</h4>
                        <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
                            For technical questions, training pipeline issues, or system bugs, contact the Project Administration Team or submit clinical observations through the <strong>Submit Feedback</strong> button on the dashboard.
                        </p>
                    </div>
                    <div style="background: var(--surface-low); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 14px; font-size: 13px;">
                        <div><strong>Project Lead:</strong> Rumaisa Ali</div>
                        <div style="margin-top: 4px;"><strong>Documentation:</strong> Available on Swagger at <a href="/docs" target="_blank" style="text-decoration: underline;">/docs</a></div>
                    </div>
                </div>

                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="UI.closeSupportModal()">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(div);
    },

    switchSupportTab(tabKey) {
        document.getElementById("modal-tab-content-sys").style.display = tabKey === 'sys' ? 'block' : 'none';
        document.getElementById("modal-tab-content-ref").style.display = tabKey === 'ref' ? 'block' : 'none';
        document.getElementById("modal-tab-content-help").style.display = tabKey === 'help' ? 'block' : 'none';

        document.getElementById("tab-btn-sys").className = 'modal-tab' + (tabKey === 'sys' ? ' active' : '');
        document.getElementById("tab-btn-ref").className = 'modal-tab' + (tabKey === 'ref' ? ' active' : '');
        document.getElementById("tab-btn-help").className = 'modal-tab' + (tabKey === 'help' ? ' active' : '');
    },

    injectForgotPasswordModal() {
        const div = document.createElement("div");
        div.id = "forgot-password-modal";
        div.className = "modal-backdrop";
        div.onclick = (e) => {
            if (e.target === div) UI.closeForgotPasswordModal();
        };
        div.innerHTML = `
            <div class="modal-card" style="max-width: 480px;">
                <div class="modal-header">
                    <div class="modal-title-group">
                        <div class="modal-title-icon" style="background: var(--warning-container); color: var(--warning);">
                            <span class="material-symbols-outlined">lock_reset</span>
                        </div>
                        <div>
                            <div class="modal-title">Password Assistance</div>
                            <div class="modal-subtitle">Clinical Evaluation Environment</div>
                        </div>
                    </div>
                    <button class="modal-close-btn" onclick="UI.closeForgotPasswordModal()">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <div class="modal-body">
                    <p style="font-size: 13px; color: var(--text-main); margin-bottom: 14px; line-height: 1.6;">
                        For demonstration and project examination purposes, external email dispatch is disabled. You can instantly access the portal using any of the pre-seeded demonstration accounts below:
                    </p>
                    <div style="background: var(--surface-low); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 12px 16px; font-size: 13px;">
                        <div style="padding: 4px 0;"><strong>👤 Patient:</strong> <code>sarah_jenkins</code> / <code>PatientPassword123!</code></div>
                        <div style="padding: 4px 0;"><strong>🩺 Provider:</strong> <code>dr_smith</code> / <code>ProviderPassword123!</code></div>
                        <div style="padding: 4px 0;"><strong>⚙️ Admin:</strong> <code>admin</code> / <code>AdminPassword123!</code></div>
                    </div>
                    <p style="font-size: 12px; color: var(--text-muted); margin-top: 14px;">
                        Alternatively, switch to the <strong>Register New Account</strong> tab to create a customized login profile.
                    </p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="UI.closeForgotPasswordModal()">Understood</button>
                </div>
            </div>
        `;
        document.body.appendChild(div);
    }
};

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        UI.closeSupportModal();
        UI.closeForgotPasswordModal();
    }
});

// Enforce authentication guards across back/forward navigation and cache restores
window.addEventListener("pageshow", (event) => {
    const path = window.location.pathname;
    const token = Auth.getToken();
    const user = Auth.getUser();

    if (path === "/dashboard" || path === "/input" || path === "/admin") {
        if (!token || !user) {
            Auth.clear();
            window.location.replace("/login?msg=Please log in to access this page.");
        } else if (path === "/admin" && user.role !== "admin") {
            window.location.replace("/login?msg=Access denied: Administrative privileges required.");
        }
    } else if (path === "/login") {
        if (token && user) {
            window.location.replace(user.role === "admin" ? "/admin" : "/dashboard");
        }
    }
});


