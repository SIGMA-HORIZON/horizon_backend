import api from './api';

export const accountService = {
    async submitRequest(data) {
        const response = await api.post('/accounts/request', data);
        return response.data;
    },

    async listRequests(status = 'PENDING') {
        const response = await api.get(`/accounts/requests?status=${status}`);
        return response.data;
    },

    async approveRequest(requestId, quotaPolicyId) {
        const response = await api.post(`/accounts/requests/${requestId}/approve`, {
            quota_policy_id: quotaPolicyId
        });
        return response.data;
    },

    async rejectRequest(requestId, reason) {
        const response = await api.post(`/accounts/requests/${requestId}/reject`, {
            reason
        });
        return response.data;
    },

    async listUsers() {
        const response = await api.get('/accounts');
        return response.data;
    }
};

