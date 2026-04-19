import api from './api';

export const adminService = {
    // Gestion des demandes de compte
    async listAccountRequests(status = 'PENDING') {
        const response = await api.get(`/accounts/requests?status=${status}`);
        return response.data;
    },
    async approveRequest(id, quotaPolicyId) {
        const response = await api.post(`/accounts/requests/${id}/approve`, { quota_policy_id: quotaPolicyId });
        return response.data;
    },
    async rejectRequest(id, reason) {
        const response = await api.post(`/accounts/requests/${id}/reject`, { reason });
        return response.data;
    },

    // Gestion des utilisateurs
    async listUsers() {
        const response = await api.get('/accounts');
        return response.data;
    },
    async getUser(id) {
        const response = await api.get(`/accounts/${id}`);
        return response.data;
    },
    async updateUser(id, data) {
        const response = await api.patch(`/accounts/${id}`, data);
        return response.data;
    },
    async suspendUser(id) {
        const response = await api.post(`/accounts/${id}/suspend`);
        return response.data;
    },
    async reactivateUser(id) {
        const response = await api.post(`/accounts/${id}/reactivate`);
        return response.data;
    },

    // Dashboard global
    async getAdminVms() {
        const response = await api.get('/admin/vms');
        return response.data;
    },
    async adminStopVm(vmId, reason = '') {
        const response = await api.post(`/admin/vms/${vmId}/stop`, { reason });
        return response.data;
    },
    async adminDeleteVm(vmId) {
        const response = await api.delete(`/admin/vms/${vmId}`);
        return response.data;
    },
    async getAuditLogs(params) {
        const response = await api.get('/admin/audit-logs', { params });
        return response.data;
    },
    async getIncidents() {
        const response = await api.get('/admin/incidents');
        return response.data;
    },

    // --- Gestion des Quotas & Violations ---
    async applyQuotaOverride(userId, quotaPolicyId, reason) {
        const response = await api.post('/admin/quota-override', {
            user_id: userId,
            quota_policy_id: quotaPolicyId,
            reason
        });
        return response.data;
    },
    async getQuotaViolations(resolved = null) {
        const params = resolved !== null ? { resolved } : {};
        const response = await api.get('/admin/violations', { params });
        return response.data;
    },

    // --- Opérations Proxmox Directes ---
    async proxmoxPauseVm(proxmoxVmid) {
        const response = await api.post(`/admin/proxmox/vms/${proxmoxVmid}/pause`);
        return response.data;
    },
    async proxmoxGetVmStatus(proxmoxVmid) {
        const response = await api.get(`/admin/proxmox/vms/${proxmoxVmid}/status`);
        return response.data;
    },
    async proxmoxListNodesQemu(nodeName) {
        const response = await api.get(`/admin/proxmox/node/${nodeName}/qemu`);
        return response.data;
    },

    // --- Configuration Infrastructure (Mappings) ---
    async listNodeMappings() {
        const response = await api.get('/admin/proxmox/node-mappings');
        return response.data;
    },
    async createNodeMapping(data) {
        const response = await api.post('/admin/proxmox/node-mappings', data);
        return response.data;
    },
    async updateNodeMapping(id, data) {
        const response = await api.patch(`/admin/proxmox/node-mappings/${id}`, data);
        return response.data;
    },
    async listIsoTemplates() {
        const response = await api.get('/admin/proxmox/iso-templates');
        return response.data;
    },
    async createIsoTemplate(data) {
        const response = await api.post('/admin/proxmox/iso-templates', data);
        return response.data;
    },
    async updateIsoTemplate(id, data) {
        const response = await api.patch(`/admin/proxmox/iso-templates/${id}`, data);
        return response.data;
    },
    async proxmoxGetSummary() {
        const response = await api.get('/admin/proxmox/summary');
        return response.data;
    },
    async listIsos() {
        const response = await api.get('/admin/isos');
        return response.data;
    },
    async createIso(data) {
        const response = await api.post('/admin/isos', data);
        return response.data;
    },
    async listIsoTemplates() {
        const response = await api.get('/admin/proxmox/iso-templates');
        return response.data;
    },
    async getProxmoxStorageIsos() {
        const response = await api.get('/admin/proxmox/storage-isos');
        return response.data;
    },
    async listReservations() {
        const response = await api.get('/admin/reservations');
        return response.data;
    }
};
