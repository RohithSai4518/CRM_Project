/**
 * CRM System - Client-Side API Communication Library
 * Zero external dependencies
 */

const API = {
  getToken() {
    return localStorage.getItem("crm_token");
  },

  setToken(token) {
    localStorage.setItem("crm_token", token);
  },

  clearToken() {
    localStorage.removeItem("crm_token");
    localStorage.removeItem("crm_user");
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem("crm_user") || "null");
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("crm_user", JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : endpoint;
    const headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    if (config.body && typeof config.body === "object" && !(config.body instanceof FormData)) {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401 && !endpoint.includes("/login") && !endpoint.includes("/forgot-password") && !endpoint.includes("/reset-password")) {
          this.clearToken();
          window.location.reload();
        }
        throw new Error(data.message || `Request failed with status ${response.status}`);
      }

      return data;
    } catch (err) {
      console.error("API Error:", err);
      throw err;
    }
  },

  // Authentication & Users
  login(email, password) {
    return this.request("/api/auth/login", {
      method: "POST",
      body: { email, password }
    });
  },

  register(data) {
    return this.request("/api/auth/register", {
      method: "POST",
      body: data
    });
  },

  forgotPassword(email) {
    return this.request("/api/auth/forgot-password", {
      method: "POST",
      body: { email }
    });
  },

  resetPassword(token, newPassword) {
    return this.request("/api/auth/reset-password", {
      method: "POST",
      body: { token, new_password: newPassword }
    });
  },

  getMe() {
    return this.request("/api/auth/me");
  },

  listUsers() {
    return this.request("/api/auth/users");
  },

  updateUserRole(userId, role) {
    return this.request(`/api/auth/users/${userId}/role`, {
      method: "POST",
      body: { role }
    });
  },

  toggleUserStatus(userId, status) {
    return this.request(`/api/auth/users/${userId}/status`, {
      method: "POST",
      body: { status }
    });
  },

  // Analytics
  getExecutiveSummary() {
    return this.request("/api/analytics/summary");
  },

  getPipelineStageSummary() {
    return this.request("/api/analytics/pipeline-by-stage");
  },

  getLeadsBySource() {
    return this.request("/api/analytics/leads-by-source");
  },

  // Accounts & Customers
  listAccounts(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/accounts?${qs}`);
  },

  getAccount(id) {
    return this.request(`/api/accounts/${id}`);
  },

  createAccount(data) {
    return this.request("/api/accounts", {
      method: "POST",
      body: data
    });
  },

  updateAccount(id, data) {
    return this.request(`/api/accounts/${id}`, {
      method: "PUT",
      body: data
    });
  },

  addCustomerNote(accountId, noteText) {
    return this.request(`/api/accounts/${accountId}/notes`, {
      method: "POST",
      body: { note_text: noteText }
    });
  },

  addCustomerAttachment(accountId, data) {
    return this.request(`/api/accounts/${accountId}/attachments`, {
      method: "POST",
      body: data
    });
  },

  setCustomerStatus(accountId, status) {
    return this.request(`/api/accounts/${accountId}/status`, {
      method: "POST",
      body: { status }
    });
  },

  deleteAccount(id) {
    return this.request(`/api/accounts/${id}`, {
      method: "DELETE"
    });
  },

  // Contacts
  listContacts(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/contacts?${qs}`);
  },

  createContact(data) {
    return this.request("/api/contacts", {
      method: "POST",
      body: data
    });
  },

  // Leads
  listLeads(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/leads?${qs}`);
  },

  createLead(data) {
    return this.request("/api/leads", {
      method: "POST",
      body: data
    });
  },

  convertLead(id, opportunityName) {
    return this.request(`/api/leads/${id}/convert`, {
      method: "POST",
      body: { opportunity_name: opportunityName }
    });
  },

  // Opportunities & Deals
  listOpportunities(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/opportunities?${qs}`);
  },

  getKanbanPipeline() {
    return this.request("/api/opportunities/kanban");
  },

  createOpportunity(data) {
    return this.request("/api/opportunities", {
      method: "POST",
      body: data
    });
  },

  setOpportunityStage(id, stage, lossReason) {
    return this.request(`/api/opportunities/${id}/stage`, {
      method: "POST",
      body: { stage, loss_reason: lossReason }
    });
  },

  // Tickets
  listTickets(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/tickets?${qs}`);
  },

  getTicket(id) {
    return this.request(`/api/tickets/${id}`);
  },

  createTicket(data) {
    return this.request("/api/tickets", {
      method: "POST",
      body: data
    });
  },

  addTicketComment(id, text, isInternal) {
    return this.request(`/api/tickets/${id}/comments`, {
      method: "POST",
      body: { comment_text: text, is_internal: isInternal }
    });
  },

  // Marketing Campaigns
  listCampaigns(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/campaigns?${qs}`);
  },

  createCampaign(data) {
    return this.request("/api/campaigns", {
      method: "POST",
      body: data
    });
  },

  // Activities & Tasks
  listActivities(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/activities?${qs}`);
  },

  createActivity(data) {
    return this.request("/api/activities", {
      method: "POST",
      body: data
    });
  },

  setActivityStatus(id, status) {
    return this.request(`/api/activities/${id}/status`, {
      method: "POST",
      body: { status }
    });
  },

  // Audit Logs
  listAuditLogs(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/api/audit?${qs}`);
  }
};
