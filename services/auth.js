import api from './api';

export const authService = {
    async login(username, password) {
        const response = await api.post('/auth/login', { username, password });
        if (response.data.access_token) {
            localStorage.setItem('horizon_token', response.data.access_token);
        }
        return response.data;
    },

    async getCurrentUser() {
        const response = await api.get('/auth/me');
        return response.data;
    },

    async changePassword(currentPassword, newPassword) {
        const response = await api.patch('/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword
        });
        return response.data;
    },

    logout() {
        localStorage.removeItem('horizon_token');
        if (typeof window !== 'undefined') {
            window.location.href = '/connexion';
        }
    },

    isAuthenticated() {
        return !!localStorage.getItem('horizon_token');
    }
};
