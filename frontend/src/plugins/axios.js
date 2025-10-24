// api.js
import axios from 'axios';
import { API_BASE_URL } from '@/config';

const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

api.interceptors.request.use((config) => {
    const method = (config.method || 'get').toLowerCase();
    if (['post', 'put', 'patch', 'delete'].includes(method)) {
        const token = getCookie('csrftoken');
        if (token) config.headers['X-CSRFToken'] = token;
    }
    // Ensure credentials are included for all requests
    config.withCredentials = true;
    return config;
});

export default api;
