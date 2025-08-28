// api.js
import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE,
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
    return config;
});

export default api;
