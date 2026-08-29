/**
 * CRM System - Enterprise Client Dashboard Application
 * Zero framework dependencies (Pure Vanilla ES6+)
 */

const App = {
  currentTab: "dashboard",
  user: null,
  permissions: [],

  async init() {
    this.bindEvents();
    
    // Check if token exists
    const token = API.getToken();
    if (!token) {
      this.showLoginView();
      return;
    }

    try {
      const res = await API.getMe();
      this.user = res.data.user;
      this.permissions = res.data.permissions || [];
      this.renderUserProfile();
      this.showMainApp();
      this.switchTab("dashboard");
    } catch (err) {
      console.warn("Session check failed, prompting login:", err);
      API.clearToken();
      this.showLoginView();
    }
  },

  toast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.innerText = message;
    container.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  },

  bindEvents() {
    // Navigation items
    document.querySelectorAll(".nav-link").forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const tab = link.dataset.tab;
        if (tab) this.switchTab(tab);
      });
    });

    // Login Form Submit
    const loginForm = document.getElementById("form-login");
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value;
        const password = document.getElementById("login-password").value;
        await this.performLogin(email, password);
      });
    }
  },

  async performLogin(email, password) {
    try {
      const res = await API.login(email, password);
      API.setToken(res.data.token);
      this.user = res.data.user;
      this.toast(`Welcome back, ${this.user.full_name}!`);
      this.renderUserProfile();
      this.showMainApp();
      this.switchTab("dashboard");
    } catch (err) {
      this.toast(err.message, "error");
    }
  },

  async quickLogin(email, password) {
    await this.performLogin(email, password);
  },

  async handleRoleSwitch(email) {
    await this.performLogin(email, "Password123!");
  },

  logout() {
    API.clearToken();
    this.user = null;
    this.showLoginView();
    this.toast("Logged out successfully");
  },

  showLoginView() {
    document.getElementById("login-container").classList.remove("hidden");
    document.getElementById("app-layout").classList.add("hidden");
  },

  showMainApp() {
    document.getElementById("login-container").classList.add("hidden");
    document.getElementById("app-layout").classList.remove("hidden");
    
    // Toggle Admin navigation item visibility based on role
    const adminNav = document.getElementById("nav-admin-console");
    if (adminNav) {
      if (this.user && (this.user.role === "Admin" || this.user.role === "SUPER_ADMIN" || this.user.role === "Sales Manager")) {
        adminNav.classList.remove("hidden");
      } else {
        adminNav.classList.add("hidden");
      }
    }

    // Sync header dropdown
    const roleSwitcher = document.getElementById("header-role-switcher");
    if (roleSwitcher && this.user) {
      roleSwitcher.value = this.user.email;
    }
  },

  renderUserProfile() {
    if (!this.user) return;
    const nameEl = document.getElementById("user-name-display");
    const roleEl = document.getElementById("user-role-display");
    const avatarEl = document.getElementById("user-avatar-img");

    if (nameEl) nameEl.innerText = this.user.full_name || this.user.email || "User";
    if (roleEl) roleEl.innerText = this.user.role || "Role";
    if (avatarEl) {
      const nameForAvatar = encodeURIComponent(this.user.full_name || this.user.email || "User");
      avatarEl.src = this.user.avatar_url || `https://ui-avatars.com/api/?name=${nameForAvatar}&background=0D8ABC&color=fff`;
    }
  },

  async switchTab(tab) {
    this.currentTab = tab;
    document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
    const activeLink = document.querySelector(`.nav-link[data-tab="${tab}"]`);
    if (activeLink) activeLink.classList.add("active");

    const pageTitle = document.getElementById("page-title");
    if (pageTitle) {
      pageTitle.innerText = tab.replace(/_/g, " ").replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    }

    const container = document.getElementById("tab-content");
    container.innerHTML = `<div style="padding: 40px; text-align: center; color: #94a3b8;">Loading ${tab}...</div>`;

    switch (tab) {
      case "dashboard":
        await this.loadDashboard(container);
        break;
      case "pipeline":
        await this.loadPipeline(container);
        break;
      case "accounts":
        await this.loadAccounts(container);
        break;
      case "contacts":
        await this.loadContacts(container);
        break;
      case "leads":
        await this.loadLeads(container);
        break;
      case "tickets":
        await this.loadTickets(container);
        break;
      case "marketing":
        await this.loadMarketing(container);
        break;
      case "activities":
        await this.loadActivities(container);
        break;
      case "admin_console":
      case "admin":
      case "admin-console":
        await this.loadAdminConsole(container);
        break;
      case "audit":
        await this.loadAudit(container);
        break;
      default:
        container.innerHTML = `<div class="card" style="padding: 20px; text-align: center;">Tab "${tab}" not found. <button class="btn btn-primary" onclick="App.switchTab('dashboard')">Go to Dashboard</button></div>`;
    }
  },

  // 1. Dashboard View
  async loadDashboard(container) {
    try {
      const summaryRes = await API.getExecutiveSummary();
      const s = summaryRes.data;

      container.innerHTML = `
        <div class="kpi-grid">
          <div class="kpi-card">
            <span class="kpi-title">Active Customers</span>
            <span class="kpi-value">${s.accounts.active_count}</span>
            <span class="kpi-subtext">Portfolio Rev: $${(s.accounts.total_portfolio_revenue / 1000000).toFixed(1)}M</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Active Pipeline</span>
            <span class="kpi-value">$${(s.pipeline.active_pipeline_value / 1000).toFixed(0)}k</span>
            <span class="kpi-subtext">Weighted: $${(s.pipeline.weighted_pipeline_value / 1000).toFixed(0)}k (${s.pipeline.win_rate_pct}% Win Rate)</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Lead Qualification</span>
            <span class="kpi-value">${s.leads.conversion_rate_pct}%</span>
            <span class="kpi-subtext">${s.leads.converted} of ${s.leads.total} Leads (Avg Score: ${s.leads.avg_score})</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Customer CSAT</span>
            <span class="kpi-value">★ ${s.support.avg_csat_score}</span>
            <span class="kpi-subtext">${s.support.resolved_tickets} Resolved / ${s.support.sla_breach_count} SLA Breaches</span>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
          <div class="card">
            <div class="card-header">
              <span class="card-title">Recent High-Value Opportunities</span>
              <button class="btn btn-primary" onclick="App.switchTab('pipeline')">View Kanban Funnel</button>
            </div>
            <div id="dashboard-opps-table">Loading...</div>
          </div>

          <div class="card">
            <div class="card-header">
              <span class="card-title">Lead Source Performance</span>
            </div>
            <div id="dashboard-sources-list">Loading...</div>
          </div>
        </div>
      `;

      const oppsRes = await API.listOpportunities({ limit: 5 });
      const oppsHtml = `
        <div class="table-responsive">
          <table class="crm-table">
            <thead>
              <tr>
                <th>Deal Name</th>
                <th>Account</th>
                <th>Amount</th>
                <th>Stage</th>
                <th>Probability</th>
              </tr>
            </thead>
            <tbody>
              ${oppsRes.data.items.map(o => `
                <tr>
                  <td><strong>${o.name}</strong></td>
                  <td>${o.account_name}</td>
                  <td style="color: #34d399; font-weight: 600;">$${Number(o.amount).toLocaleString()}</td>
                  <td><span class="badge badge-info">${o.stage}</span></td>
                  <td>${o.win_probability}%</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      document.getElementById("dashboard-opps-table").innerHTML = oppsHtml;

      const sourcesRes = await API.getLeadsBySource();
      const sourcesHtml = `
        <div style="display: flex; flex-direction: column; gap: 14px;">
          ${sourcesRes.data.map(src => `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 8px;">
              <div>
                <div style="font-weight: 600; font-size: 0.88rem;">${src.lead_source}</div>
                <div style="font-size: 0.74rem; color: #94a3b8;">Avg Score: ${Math.round(src.avg_score)}/100</div>
              </div>
              <span class="badge badge-success">${src.count} Leads</span>
            </div>
          `).join('')}
        </div>
      `;
      document.getElementById("dashboard-sources-list").innerHTML = sourcesHtml;

    } catch (err) {
      container.innerHTML = `
        <div class="card" style="color: #ef4444; padding: 20px;">
          <h3>⚠️ Unable to load dashboard metrics</h3>
          <p>${err.message}</p>
          <button class="btn btn-primary" style="margin-top: 12px;" onclick="App.logout()">Switch / Re-authenticate Account</button>
        </div>
      `;
    }
  },

  // 2. Customers / Accounts View (With 360 Profile Drawer & Status Controls)
  async loadAccounts(container) {
    try {
      const res = await API.listAccounts();
      const accounts = res.data.items;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <div>
              <span class="card-title">Customer & Account Management (${res.data.total})</span>
              <p style="color: #94a3b8; font-size: 0.82rem; margin-top: 4px;">Click any customer to open the 360° Profile, Interaction Timeline, and Notes</p>
            </div>
            <button class="btn btn-primary" onclick="App.openNewAccountModal()">+ Add Customer</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Customer / Company</th>
                  <th>Industry</th>
                  <th>Tier</th>
                  <th>Annual Revenue</th>
                  <th>Status</th>
                  <th>Account Owner</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${accounts.map(a => `
                  <tr>
                    <td>
                      <a href="#" style="color: #60a5fa; font-weight: 700; text-decoration: none;" onclick="App.openCustomer360Modal('${a.id}'); return false;">
                        🏢 ${a.name}
                      </a>
                    </td>
                    <td>${a.industry || '-'}</td>
                    <td><span class="badge badge-info">${a.tier}</span></td>
                    <td>$${Number(a.annual_revenue || 0).toLocaleString()}</td>
                    <td>
                      <span class="badge ${a.status === 'ACTIVE' ? 'badge-success' : (a.status === 'INACTIVE' ? 'badge-danger' : 'badge-warning')}">
                        ${a.status}
                      </span>
                    </td>
                    <td>${a.owner_name}</td>
                    <td>
                      <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" onclick="App.openCustomer360Modal('${a.id}')">View 360°</button>
                      <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" onclick="App.openEditCustomerModal('${a.id}')">Edit</button>
                      <button class="btn btn-danger" style="padding: 4px 8px; font-size: 0.75rem;" onclick="App.toggleCustomerStatusModal('${a.id}', '${a.name}', '${a.status}')">
                        ${a.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading accounts: ${err.message}</div>`;
    }
  },

  // Customer 360 Profile Modal
  async openCustomer360Modal(accountId) {
    try {
      const res = await API.getAccount(accountId);
      const acc = res.data;

      const profileHtml = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 16px;">
          <div>
            <h2 style="font-size: 1.4rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">
              🏢 ${acc.name}
              <span class="badge ${acc.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${acc.status}</span>
              <span class="badge badge-info">${acc.tier}</span>
            </h2>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
              Industry: ${acc.industry || 'Technology'} • Owner: ${acc.owner ? acc.owner.full_name : 'Unassigned'} • Revenue: $${Number(acc.annual_revenue || 0).toLocaleString()}
            </div>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary" onclick="App.quickAddNotePrompt('${acc.id}')">+ Log Note</button>
            <button class="btn btn-secondary" onclick="App.quickAddAttachmentPrompt('${acc.id}')">📎 Attach File</button>
          </div>
        </div>

        <!-- Tab Controls inside Profile -->
        <div style="display: flex; gap: 10px; border-bottom: 1px solid #334155; margin-bottom: 20px;">
          <button class="btn btn-secondary" id="tab-btn-timeline" style="border-bottom-left-radius: 0; border-bottom-right-radius: 0;" onclick="App.switchProfileTab('timeline')">📅 Interaction Timeline (${(acc.interaction_history || []).length})</button>
          <button class="btn btn-secondary" id="tab-btn-contacts" style="border-bottom-left-radius: 0; border-bottom-right-radius: 0;" onclick="App.switchProfileTab('contacts')">👥 Contacts (${(acc.contacts || []).length})</button>
          <button class="btn btn-secondary" id="tab-btn-notes" style="border-bottom-left-radius: 0; border-bottom-right-radius: 0;" onclick="App.switchProfileTab('notes')">📝 Notes & Files (${(acc.notes || []).length + (acc.attachments || []).length})</button>
          <button class="btn btn-secondary" id="tab-btn-deals" style="border-bottom-left-radius: 0; border-bottom-right-radius: 0;" onclick="App.switchProfileTab('deals')">🎯 Deals & Tickets (${(acc.opportunities || []).length + (acc.tickets || []).length})</button>
        </div>

        <!-- Profile Tab: Interaction Timeline -->
        <div id="p-tab-timeline">
          <h4 style="font-size: 0.95rem; margin-bottom: 12px; color: #94a3b8;">Chronological Customer Interaction History</h4>
          <div style="display: flex; flex-direction: column; gap: 14px; max-height: 400px; overflow-y: auto;">
            ${(acc.interaction_history || []).map(item => `
              <div style="display: flex; gap: 12px; background: #1e293b; padding: 12px; border-radius: 6px; border-left: 3px solid #3b82f6;">
                <div style="font-size: 1.4rem;">${item.icon}</div>
                <div style="flex: 1;">
                  <div style="display: flex; justify-content: space-between;">
                    <strong style="font-size: 0.9rem;">${item.title}</strong>
                    <small style="color: #94a3b8;">${item.timestamp || 'Recent'}</small>
                  </div>
                  <div style="font-size: 0.82rem; color: #cbd5e1; margin-top: 4px;">${item.description || 'No additional notes provided.'}</div>
                </div>
              </div>
            `).join('')}
            ${(!acc.interaction_history || acc.interaction_history.length === 0) ? '<div style="color: #94a3b8; text-align: center; padding: 20px;">No interaction logs recorded yet.</div>' : ''}
          </div>
        </div>

        <!-- Profile Tab: Contacts -->
        <div id="p-tab-contacts" class="hidden">
          <h4 style="font-size: 0.95rem; margin-bottom: 12px; color: #94a3b8;">Key Stakeholders & Contacts</h4>
          <div class="table-responsive">
            <table class="crm-table">
              <thead><tr><th>Name</th><th>Title</th><th>Email</th><th>Phone</th><th>Primary</th></tr></thead>
              <tbody>
                ${(acc.contacts || []).map(c => `
                  <tr>
                    <td><strong>${c.first_name} ${c.last_name}</strong></td>
                    <td>${c.job_title || '-'}</td>
                    <td>${c.email}</td>
                    <td>${c.phone || '-'}</td>
                    <td>${c.is_primary ? '<span class="badge badge-success">Primary</span>' : '-'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Profile Tab: Notes & Files -->
        <div id="p-tab-notes" class="hidden">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <div>
              <h4 style="font-size: 0.95rem; margin-bottom: 8px; color: #94a3b8;">Internal Team Notes (${(acc.notes || []).length})</h4>
              <div style="display: flex; flex-direction: column; gap: 10px; max-height: 300px; overflow-y: auto;">
                ${(acc.notes || []).map(n => `
                  <div style="background: #1e293b; padding: 10px; border-radius: 6px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #94a3b8;">
                      <span>👤 ${n.author_name || 'Team Member'}</span>
                      <span>${n.created_at}</span>
                    </div>
                    <div style="font-size: 0.85rem; margin-top: 6px;">${n.note_text}</div>
                  </div>
                `).join('')}
                ${(!acc.notes || acc.notes.length === 0) ? '<div style="color: #64748b; font-size: 0.8rem;">No notes recorded.</div>' : ''}
              </div>
            </div>
            <div>
              <h4 style="font-size: 0.95rem; margin-bottom: 8px; color: #94a3b8;">Attachments & Contracts (${(acc.attachments || []).length})</h4>
              <div style="display: flex; flex-direction: column; gap: 10px; max-height: 300px; overflow-y: auto;">
                ${(acc.attachments || []).map(att => `
                  <div style="background: #1e293b; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                      <div style="font-size: 0.88rem; font-weight: 600;">📎 ${att.filename}</div>
                      <small style="color: #94a3b8;">${att.file_type} • ${Math.round(att.file_size/1024)} KB</small>
                    </div>
                    <span class="badge badge-neutral">Stored</span>
                  </div>
                `).join('')}
                ${(!acc.attachments || acc.attachments.length === 0) ? '<div style="color: #64748b; font-size: 0.8rem;">No attachments uploaded.</div>' : ''}
              </div>
            </div>
          </div>
        </div>

        <!-- Profile Tab: Deals & Tickets -->
        <div id="p-tab-deals" class="hidden">
          <h4 style="font-size: 0.95rem; margin-bottom: 8px; color: #94a3b8;">Active Opportunities</h4>
          <div class="table-responsive" style="margin-bottom: 16px;">
            <table class="crm-table">
              <thead><tr><th>Deal Name</th><th>Amount</th><th>Stage</th><th>Win Prob</th></tr></thead>
              <tbody>
                ${(acc.opportunities || []).map(o => `
                  <tr>
                    <td><strong>${o.name}</strong></td>
                    <td style="color: #34d399; font-weight: 600;">$${Number(o.amount).toLocaleString()}</td>
                    <td><span class="badge badge-info">${o.stage}</span></td>
                    <td>${o.win_probability}%</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
          <h4 style="font-size: 0.95rem; margin-bottom: 8px; color: #94a3b8;">Support Tickets</h4>
          <div class="table-responsive">
            <table class="crm-table">
              <thead><tr><th>Ticket Title</th><th>Priority</th><th>Status</th></tr></thead>
              <tbody>
                ${(acc.tickets || []).map(t => `
                  <tr>
                    <td><strong>${t.title}</strong></td>
                    <td><span class="badge ${t.priority === 'URGENT' || t.priority === 'HIGH' ? 'badge-danger' : 'badge-warning'}">${t.priority}</span></td>
                    <td><span class="badge badge-info">${t.status}</span></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;

      this.renderModal(`Customer 360° Profile`, profileHtml, "max-width: 850px;");
    } catch (err) {
      this.toast(err.message, "error");
    }
  },

  switchProfileTab(tabName) {
    ["timeline", "contacts", "notes", "deals"].forEach(t => {
      const el = document.getElementById(`p-tab-${t}`);
      const btn = document.getElementById(`tab-btn-${t}`);
      if (el) el.classList.add("hidden");
      if (btn) btn.style.borderBottom = "none";
    });

    const activeEl = document.getElementById(`p-tab-${tabName}`);
    const activeBtn = document.getElementById(`tab-btn-${tabName}`);
    if (activeEl) activeEl.classList.remove("hidden");
    if (activeBtn) activeBtn.style.borderBottom = "2px solid #3b82f6";
  },

  quickAddNotePrompt(accountId) {
    const text = prompt("Enter internal customer note:");
    if (!text || !text.trim()) return;
    API.addCustomerNote(accountId, text).then(() => {
      this.toast("Customer note recorded!");
      this.openCustomer360Modal(accountId);
    }).catch(err => this.toast(err.message, "error"));
  },

  quickAddAttachmentPrompt(accountId) {
    const filename = prompt("Enter document attachment filename (e.g. Master_Services_Agreement_2026.pdf):");
    if (!filename || !filename.trim()) return;
    API.addCustomerAttachment(accountId, {
      filename: filename.trim(),
      file_size: 245000,
      file_type: "PDF Document",
      storage_path: `/storage/contracts/${filename}`
    }).then(() => {
      this.toast("Attachment recorded!");
      this.openCustomer360Modal(accountId);
    }).catch(err => this.toast(err.message, "error"));
  },

  toggleCustomerStatusModal(accountId, customerName, currentStatus) {
    const newStatus = currentStatus === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    if (confirm(`Are you sure you want to change status of '${customerName}' to ${newStatus}?`)) {
      API.setCustomerStatus(accountId, newStatus).then(() => {
        this.toast(`Customer status updated to ${newStatus}`);
        this.loadAccounts(document.getElementById("tab-content"));
      }).catch(err => this.toast(err.message, "error"));
    }
  },

  // 3. Admin Console (Manage Users & Roles)
  async loadAdminConsole(container) {
    try {
      const res = await API.listUsers();
      const users = res.data;

      // Compute quick user statistics
      const adminCount = users.filter(u => u.role === 'Admin' || u.role === 'SUPER_ADMIN').length;
      const salesCount = users.filter(u => u.role === 'Sales Manager' || u.role === 'Sales Representative').length;
      const supportCount = users.filter(u => u.role === 'Support Agent').length;
      const activeCount = users.filter(u => u.status === 'ACTIVE').length;

      container.innerHTML = `
        <div class="kpi-grid" style="margin-bottom: 20px;">
          <div class="kpi-card">
            <span class="kpi-title">Total Staff</span>
            <span class="kpi-value">${users.length} Users</span>
            <span class="kpi-subtext">${activeCount} Active / ${users.length - activeCount} Inactive</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Administrators</span>
            <span class="kpi-value">${adminCount}</span>
            <span class="kpi-subtext">Full Root Permissions</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Sales Department</span>
            <span class="kpi-value">${salesCount}</span>
            <span class="kpi-subtext">Managers & Representatives</span>
          </div>
          <div class="kpi-card">
            <span class="kpi-title">Helpdesk Support</span>
            <span class="kpi-value">${supportCount}</span>
            <span class="kpi-subtext">Support & SLA Agents</span>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <span class="card-title">🛡️ Admin Console - User & Role Management</span>
              <p style="color: #94a3b8; font-size: 0.82rem; margin-top: 4px;">Assign user roles (Admin, Sales Manager, Sales Representative, Support Agent, Marketing Executive) and toggle active status.</p>
            </div>
            <button class="btn btn-primary" onclick="App.openNewUserModal()">+ Add New Team Member</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Team Member</th>
                  <th>Email</th>
                  <th>Assigned Role</th>
                  <th>Status</th>
                  <th>Created Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${users.map(u => `
                  <tr>
                    <td><strong>${u.full_name}</strong></td>
                    <td>${u.email}</td>
                    <td>
                      <select class="form-control" style="padding: 4px 8px; font-size: 0.82rem; width: auto;" onchange="App.changeUserRole('${u.id}', this.value)">
                        <option value="Admin" ${u.role === 'Admin' || u.role === 'SUPER_ADMIN' ? 'selected' : ''}>Admin</option>
                        <option value="Sales Manager" ${u.role === 'Sales Manager' ? 'selected' : ''}>Sales Manager</option>
                        <option value="Sales Representative" ${u.role === 'Sales Representative' ? 'selected' : ''}>Sales Representative</option>
                        <option value="Support Agent" ${u.role === 'Support Agent' ? 'selected' : ''}>Support Agent</option>
                        <option value="Marketing Executive" ${u.role === 'Marketing Executive' ? 'selected' : ''}>Marketing Executive</option>
                      </select>
                    </td>
                    <td>
                      <span class="badge ${u.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${u.status}</span>
                    </td>
                    <td>${u.created_at}</td>
                    <td>
                      <button class="btn ${u.status === 'ACTIVE' ? 'btn-danger' : 'btn-success'}" style="padding: 4px 8px; font-size: 0.75rem;" onclick="App.toggleUserStatus('${u.id}', '${u.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'}')">
                        ${u.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444; padding: 20px;">Error loading admin console: ${err.message}</div>`;
    }
  },

  async changeUserRole(userId, newRole) {
    try {
      await API.updateUserRole(userId, newRole);
      this.toast(`User role updated to ${newRole}`);
    } catch (err) {
      this.toast(err.message, "error");
    }
  },

  async toggleUserStatus(userId, status) {
    try {
      await API.toggleUserStatus(userId, status);
      this.toast(`User status set to ${status}`);
      this.loadAdminConsole(document.getElementById("tab-content"));
    } catch (err) {
      this.toast(err.message, "error");
    }
  },

  openNewUserModal() {
    this.renderModal("Register New Team Member", `
      <form id="modal-register-user-form">
        <div class="form-group">
          <label class="form-label">Full Name *</label>
          <input class="form-control" name="full_name" required>
        </div>
        <div class="form-group">
          <label class="form-label">Work Email *</label>
          <input type="email" class="form-control" name="email" required>
        </div>
        <div class="form-group">
          <label class="form-label">Temporary Password *</label>
          <input type="password" class="form-control" name="password" value="Password123!" required>
        </div>
        <div class="form-group">
          <label class="form-label">Assign Role *</label>
          <select class="form-control" name="role">
            <option value="Sales Representative">Sales Representative</option>
            <option value="Sales Manager">Sales Manager</option>
            <option value="Support Agent">Support Agent</option>
            <option value="Marketing Executive">Marketing Executive</option>
            <option value="Admin">Admin</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Create Team Member Account</button>
      </form>
    `);

    document.getElementById("modal-register-user-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      try {
        await API.register({
          full_name: form.full_name.value,
          email: form.email.value,
          password: form.password.value,
          role: form.role.value
        });
        this.closeModal();
        this.toast("New team member added successfully!");
        this.loadAdminConsole(document.getElementById("tab-content"));
      } catch (err) {
        this.toast(err.message, "error");
      }
    });
  },

  // Forgot / Reset Password Modal
  openForgotPasswordModal() {
    this.renderModal("Forgot Password Assistance", `
      <form id="modal-forgot-form">
        <p style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 16px;">
          Enter your registered work email. The system will generate a secure reset token.
        </p>
        <div class="form-group">
          <label class="form-label">Registered Work Email</label>
          <input type="email" id="forgot-email-input" class="form-control" placeholder="user@omnicrm.com" required>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Request Password Reset</button>
      </form>
      <div id="reset-token-display-area" class="hidden" style="margin-top: 20px; border-top: 1px solid #334155; padding-top: 16px;">
        <p style="font-size: 0.85rem; color: #34d399; margin-bottom: 8px;">Reset token issued! Enter your new password below:</p>
        <div class="form-group">
          <label class="form-label">Reset Token</label>
          <input type="text" id="reset-token-input" class="form-control" readonly>
        </div>
        <div class="form-group">
          <label class="form-label">New Password</label>
          <input type="password" id="reset-new-password" class="form-control" placeholder="Min 6 characters" required>
        </div>
        <button class="btn btn-success" style="width: 100%;" onclick="App.submitPasswordReset()">Confirm & Update Password</button>
      </div>
    `);

    document.getElementById("modal-forgot-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("forgot-email-input").value;
      try {
        const res = await API.forgotPassword(email);
        if (res.data && res.data.reset_token) {
          document.getElementById("reset-token-display-area").classList.remove("hidden");
          document.getElementById("reset-token-input").value = res.data.reset_token;
          this.toast("Reset token generated! Enter new password below.");
        } else {
          this.toast(res.data.message || "Reset request dispatched.");
        }
      } catch (err) {
        this.toast(err.message, "error");
      }
    });
  },

  async submitPasswordReset() {
    const token = document.getElementById("reset-token-input").value;
    const newPassword = document.getElementById("reset-new-password").value;
    try {
      const res = await API.resetPassword(token, newPassword);
      this.closeModal();
      this.toast(res.data.message || "Password updated! You can now log in.");
    } catch (err) {
      this.toast(err.message, "error");
    }
  },

  // 4. Contacts View
  async loadContacts(container) {
    try {
      const res = await API.listContacts();
      const contacts = res.data.items;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Contacts Directory (${res.data.total})</span>
            <button class="btn btn-primary" onclick="App.openNewContactModal()">+ Add Contact</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Full Name</th>
                  <th>Company</th>
                  <th>Job Title</th>
                  <th>Email</th>
                  <th>Phone</th>
                </tr>
              </thead>
              <tbody>
                ${contacts.map(c => `
                  <tr>
                    <td><strong>${c.first_name} ${c.last_name}</strong> ${c.is_primary ? '<span class="badge badge-success">Primary</span>' : ''}</td>
                    <td>${c.account_name}</td>
                    <td>${c.job_title || '-'}</td>
                    <td>${c.email}</td>
                    <td>${c.phone || '-'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading contacts: ${err.message}</div>`;
    }
  },

  // 5. Leads View
  async loadLeads(container) {
    try {
      const res = await API.listLeads();
      const leads = res.data.items;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Inbound Leads & Qualification (${res.data.total})</span>
            <button class="btn btn-primary" onclick="App.openNewLeadModal()">+ New Lead</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Company</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Est. Value</th>
                  <th>Source</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${leads.map(l => `
                  <tr>
                    <td><strong>${l.first_name} ${l.last_name}</strong><br><small style="color: #94a3b8;">${l.email}</small></td>
                    <td>${l.company_name || '-'}</td>
                    <td>
                      <span class="badge ${l.lead_score >= 65 ? 'badge-success' : 'badge-warning'}">
                        ${l.lead_score} / 100
                      </span>
                    </td>
                    <td><span class="badge badge-info">${l.status}</span></td>
                    <td>$${Number(l.estimated_value || 0).toLocaleString()}</td>
                    <td>${l.lead_source}</td>
                    <td>
                      ${l.status !== 'CONVERTED' ? `
                        <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.76rem;" onclick="App.convertLeadModal('${l.id}', '${l.first_name} ${l.last_name}')">Convert Lead</button>
                      ` : '<span style="color: #34d399; font-size: 0.8rem;">Converted ✓</span>'}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading leads: ${err.message}</div>`;
    }
  },

  // 6. Pipeline View
  async loadPipeline(container) {
    try {
      const res = await API.getKanbanPipeline();
      const data = res.data;

      let boardColsHtml = '';
      data.stages.forEach(st => {
        const deals = data.board[st.id] || [];
        const colTotal = data.totals[st.id] || 0;

        boardColsHtml += `
          <div class="kanban-column" data-stage="${st.id}">
            <div class="kanban-column-header">
              <div>
                <div class="kanban-column-title">
                  <span>${st.name}</span>
                  <span class="badge badge-neutral">${deals.length}</span>
                </div>
                <div class="kanban-column-total">$${colTotal.toLocaleString()}</div>
              </div>
            </div>
            <div class="kanban-cards">
              ${deals.map(d => `
                <div class="deal-card" onclick="App.openDealModal('${d.id}')">
                  <div class="deal-title">${d.name}</div>
                  <div class="deal-amount">$${Number(d.amount).toLocaleString()}</div>
                  <div class="deal-account">🏢 ${d.account_name || 'Independent'}</div>
                  <div style="margin-top: 8px; display: flex; justify-content: space-between; font-size: 0.75rem; color: #94a3b8;">
                    <span>Win Prob: ${d.win_probability}%</span>
                    <span>👤 ${d.owner_id ? 'Assigned' : 'Open'}</span>
                  </div>
                </div>
              `).join('')}
              ${deals.length === 0 ? `<div style="text-align: center; color: #64748b; padding: 20px; font-size: 0.8rem;">No deals in this stage</div>` : ''}
            </div>
          </div>
        `;
      });

      container.innerHTML = `
        <div class="card-header" style="margin-bottom: 16px;">
          <div>
            <span style="font-size: 1.1rem; font-weight: 700;">Opportunity Stage Funnel</span>
            <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 12px;">Active Pipeline Value: $${data.total_active_pipeline.toLocaleString()}</span>
          </div>
          <button class="btn btn-primary" onclick="App.openNewDealModal()">+ New Opportunity</button>
        </div>
        <div class="kanban-board">${boardColsHtml}</div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Failed to load sales pipeline: ${err.message}</div>`;
    }
  },

  // 7. Tickets View
  async loadTickets(container) {
    try {
      const res = await API.listTickets();
      const tickets = res.data.items;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Support & Helpdesk SLA Queue (${res.data.total})</span>
            <button class="btn btn-primary" onclick="App.openNewTicketModal()">+ Open Ticket</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Ticket Subject</th>
                  <th>Account</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>SLA Deadline</th>
                  <th>Assigned Agent</th>
                </tr>
              </thead>
              <tbody>
                ${tickets.map(t => `
                  <tr style="cursor: pointer;" onclick="App.openTicketModal('${t.id}')">
                    <td><strong>${t.title}</strong></td>
                    <td>${t.account_name}</td>
                    <td><span class="badge ${t.priority === 'URGENT' || t.priority === 'HIGH' ? 'badge-danger' : 'badge-warning'}">${t.priority}</span></td>
                    <td><span class="badge badge-info">${t.status}</span></td>
                    <td>${t.sla_resolution_deadline || '-'} ${t.sla_resolution_breached ? '<span class="badge badge-danger">Breached</span>' : ''}</td>
                    <td>${t.agent_name}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading tickets: ${err.message}</div>`;
    }
  },

  // 8. Marketing View
  async loadMarketing(container) {
    try {
      const res = await API.listCampaigns();
      const campaigns = res.data.items;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Marketing Campaigns & Lead Gen (${res.data.total})</span>
            <button class="btn btn-primary" onclick="App.openNewCampaignModal()">+ New Campaign</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Campaign Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Budget</th>
                  <th>Open Rate</th>
                  <th>Conversions</th>
                </tr>
              </thead>
              <tbody>
                ${campaigns.map(cmp => `
                  <tr>
                    <td><strong>${cmp.name}</strong></td>
                    <td><span class="badge badge-neutral">${cmp.type}</span></td>
                    <td><span class="badge badge-success">${cmp.status}</span></td>
                    <td>$${Number(cmp.budget || 0).toLocaleString()}</td>
                    <td>${cmp.open_rate_pct}%</td>
                    <td><strong style="color: #34d399;">${cmp.conversion_count}</strong></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading campaigns: ${err.message}</div>`;
    }
  },

  // 9. Activities View
  async loadActivities(container) {
    try {
      const res = await API.listActivities();
      const activities = res.data.items;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Upcoming Tasks, Calls & Meetings (${res.data.total})</span>
            <button class="btn btn-primary" onclick="App.openNewActivityModal()">+ Add Activity</button>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Activity</th>
                  <th>Type</th>
                  <th>Due Date</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Assigned To</th>
                </tr>
              </thead>
              <tbody>
                ${activities.map(act => `
                  <tr>
                    <td><strong>${act.subject}</strong></td>
                    <td><span class="badge badge-neutral">${act.activity_type}</span></td>
                    <td>${act.due_date || '-'}</td>
                    <td><span class="badge ${act.priority === 'HIGH' ? 'badge-danger' : 'badge-warning'}">${act.priority}</span></td>
                    <td><span class="badge badge-info">${act.status}</span></td>
                    <td>${act.assigned_name}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading activities: ${err.message}</div>`;
    }
  },

  // 10. Audit Logs View
  async loadAudit(container) {
    try {
      const res = await API.listAuditLogs();
      const logs = res.data;

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <span class="card-title">Immutable Audit Trail & Compliance Vault</span>
          </div>
          <div class="table-responsive">
            <table class="crm-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Audit Summary</th>
                </tr>
              </thead>
              <tbody>
                ${logs.map(lg => `
                  <tr>
                    <td><small style="color: #94a3b8;">${lg.created_at}</small></td>
                    <td>${lg.user_email}</td>
                    <td><span class="badge badge-neutral">${lg.action}</span></td>
                    <td><strong>${lg.entity_type}</strong> (${lg.entity_id})</td>
                    <td>${lg.change_summary}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card" style="color: #ef4444;">Error loading audit logs: ${err.message}</div>`;
    }
  },

  // Modal helpers
  openNewAccountModal() {
    this.renderModal("Create New Customer Account", `
      <form id="modal-account-form">
        <div class="form-group">
          <label class="form-label">Company / Customer Name *</label>
          <input class="form-control" name="name" required>
        </div>
        <div class="form-group">
          <label class="form-label">Industry</label>
          <input class="form-control" name="industry" value="Technology">
        </div>
        <div class="form-group">
          <label class="form-label">Annual Revenue ($)</label>
          <input type="number" class="form-control" name="annual_revenue" value="1000000">
        </div>
        <div class="form-group">
          <label class="form-label">Tier</label>
          <select class="form-control" name="tier">
            <option value="STANDARD">Standard</option>
            <option value="PREMIUM">Premium</option>
            <option value="ENTERPRISE">Enterprise</option>
            <option value="STRATEGIC">Strategic</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Customer Status</label>
          <select class="form-control" name="status">
            <option value="ACTIVE">Active</option>
            <option value="PROSPECT">Prospect</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Save Customer</button>
      </form>
    `);

    document.getElementById("modal-account-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      try {
        await API.createAccount({
          name: form.name.value,
          industry: form.industry.value,
          annual_revenue: parseFloat(form.annual_revenue.value) || 0,
          tier: form.tier.value,
          status: form.status.value
        });
        this.closeModal();
        this.toast("Customer account created!");
        this.loadAccounts(document.getElementById("tab-content"));
      } catch (err) {
        this.toast(err.message, "error");
      }
    });
  },

  openEditCustomerModal(accountId) {
    API.getAccount(accountId).then(res => {
      const a = res.data;
      this.renderModal(`Edit Customer: ${a.name}`, `
        <form id="modal-edit-account-form">
          <div class="form-group">
            <label class="form-label">Company Name *</label>
            <input class="form-control" name="name" value="${a.name}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Industry</label>
            <input class="form-control" name="industry" value="${a.industry || ''}">
          </div>
          <div class="form-group">
            <label class="form-label">Annual Revenue ($)</label>
            <input type="number" class="form-control" name="annual_revenue" value="${a.annual_revenue || 0}">
          </div>
          <div class="form-group">
            <label class="form-label">Tier</label>
            <select class="form-control" name="tier">
              <option value="STANDARD" ${a.tier === 'STANDARD' ? 'selected' : ''}>Standard</option>
              <option value="PREMIUM" ${a.tier === 'PREMIUM' ? 'selected' : ''}>Premium</option>
              <option value="ENTERPRISE" ${a.tier === 'ENTERPRISE' ? 'selected' : ''}>Enterprise</option>
              <option value="STRATEGIC" ${a.tier === 'STRATEGIC' ? 'selected' : ''}>Strategic</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Status</label>
            <select class="form-control" name="status">
              <option value="ACTIVE" ${a.status === 'ACTIVE' ? 'selected' : ''}>Active</option>
              <option value="PROSPECT" ${a.status === 'PROSPECT' ? 'selected' : ''}>Prospect</option>
              <option value="INACTIVE" ${a.status === 'INACTIVE' ? 'selected' : ''}>Inactive</option>
              <option value="CHURNED" ${a.status === 'CHURNED' ? 'selected' : ''}>Churned</option>
            </select>
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%;">Save Changes</button>
        </form>
      `);

      document.getElementById("modal-edit-account-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const form = e.target;
        try {
          await API.updateAccount(accountId, {
            name: form.name.value,
            industry: form.industry.value,
            annual_revenue: parseFloat(form.annual_revenue.value) || 0,
            tier: form.tier.value,
            status: form.status.value
          });
          this.closeModal();
          this.toast("Customer details updated!");
          this.loadAccounts(document.getElementById("tab-content"));
        } catch (err) {
          this.toast(err.message, "error");
        }
      });
    });
  },

  openNewLeadModal() {
    this.renderModal("Create New Lead", `
      <form id="modal-lead-form">
        <div class="form-group">
          <label class="form-label">First Name *</label>
          <input class="form-control" name="first_name" required>
        </div>
        <div class="form-group">
          <label class="form-label">Last Name *</label>
          <input class="form-control" name="last_name" required>
        </div>
        <div class="form-group">
          <label class="form-label">Company Name</label>
          <input class="form-control" name="company_name">
        </div>
        <div class="form-group">
          <label class="form-label">Email Address *</label>
          <input type="email" class="form-control" name="email" required>
        </div>
        <div class="form-group">
          <label class="form-label">Estimated Deal Value ($)</label>
          <input type="number" class="form-control" name="estimated_value" value="25000">
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Create Lead</button>
      </form>
    `);

    document.getElementById("modal-lead-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      try {
        await API.createLead({
          first_name: form.first_name.value,
          last_name: form.last_name.value,
          company_name: form.company_name.value,
          email: form.email.value,
          estimated_value: parseFloat(form.estimated_value.value) || 0
        });
        this.closeModal();
        this.toast("Lead created and scored!");
        this.switchTab("leads");
      } catch (err) {
        this.toast(err.message, "error");
      }
    });
  },

  convertLeadModal(leadId, leadName) {
    this.renderModal(`Convert Lead: ${leadName}`, `
      <form id="modal-convert-form">
        <p style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 16px;">
          Converting this lead will automatically create an Account, a primary Contact, and open a new Deal in the Qualification stage.
        </p>
        <div class="form-group">
          <label class="form-label">Opportunity / Deal Name</label>
          <input class="form-control" name="opp_name" value="${leadName} - Enterprise Contract">
        </div>
        <button type="submit" class="btn btn-success" style="width: 100%;">Confirm & Convert Lead</button>
      </form>
    `);

    document.getElementById("modal-convert-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const oppName = e.target.opp_name.value;
      try {
        await API.convertLead(leadId, oppName);
        this.closeModal();
        this.toast("Lead successfully converted to Account, Contact & Opportunity!");
        this.switchTab("pipeline");
      } catch (err) {
        this.toast(err.message, "error");
      }
    });
  },

  renderModal(title, bodyHtml, customStyle = "") {
    let overlay = document.getElementById("modal-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "modal-overlay";
      overlay.className = "modal-overlay";
      document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
      <div class="modal-content" style="${customStyle}">
        <div class="modal-header">
          <span style="font-weight: 700; font-size: 1.1rem;">${title}</span>
          <button style="background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer;" onclick="App.closeModal()">✕</button>
        </div>
        <div class="modal-body">${bodyHtml}</div>
      </div>
    `;
    overlay.classList.remove("hidden");
  },

  closeModal() {
    const overlay = document.getElementById("modal-overlay");
    if (overlay) overlay.classList.add("hidden");
  }
};

window.addEventListener("DOMContentLoaded", () => App.init());
