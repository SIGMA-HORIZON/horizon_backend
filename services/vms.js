import api from './api';

export const vmService = {
    async listVms() {
        const response = await api.get('/vms');
        return response.data;
    },

    async createVm(data) {
        const response = await api.post('/vms', data);
        return response.data;
    },

    async getVm(id) {
        const response = await api.get(`/vms/${id}`);
        return response.data;
    },

    async stopVm(id) {
        const response = await api.post(`/vms/${id}/stop`);
        return response.data;
    },

    async startVm(id) {
        const response = await api.post(`/vms/${id}/start`);
        return response.data;
    },

    async rebootVm(id) {
        const response = await api.post(`/vms/${id}/reboot`);
        return response.data;
    },

    async pauseVm(id) {
        const response = await api.post(`/vms/${id}/pause`);
        return response.data;
    },

    async deleteVm(id) {
        const response = await api.delete(`/vms/${id}`);
        return response.data;
    },

    async extendVm(id, additionalHours) {
        const response = await api.post(`/vms/${id}/extend`, { additional_hours: additionalHours });
        return response.data;
    },

    async getSshKey(id) {
        const response = await api.get(`/vms/${id}/ssh-key`);
        return response.data;
    },

    async updateVm(id, data) {
        const response = await api.patch(`/vms/${id}`, data);
        return response.data;
    },

    async listIsos() {
        const response = await api.get('/vms/available-isos');
        return response.data;
    },

    async getClusterStatus() {
        const response = await api.get('/vms/cluster/status');
        return response.data;
    }
};
