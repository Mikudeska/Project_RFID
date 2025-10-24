// config.js - Dynamic URL Configuration
const isDevelopment = import.meta.env.MODE === 'development';

const getApiUrl = () => {
    // ใน development mode ให้ชี้ไปที่ Django backend (localhost:8000)
    if (isDevelopment) {
        return 'http://localhost:8001/api/';
    }
    // ใน production ให้ใช้ host เดียวกัน
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const host = window.location.host;
    return `${protocol}//${host}/api/`;
};

const getWsUrl = () => {
    // ใน development mode ให้ชี้ไปที่ Django backend (localhost:8000)
    if (isDevelopment) {
        return 'ws://localhost:8001/ws/crud01/';
    }
    // ใน production ให้ใช้ host เดียวกัน
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/crud01/`;
};

// อนุญาตให้ override ด้วย environment variables ถ้ามี
const API_BASE_URL = import.meta.env.VITE_API_BASE || getApiUrl();
const WS_BASE_URL = import.meta.env.VITE_API_WS_BASE || getWsUrl();

export { getApiUrl, getWsUrl, API_BASE_URL, WS_BASE_URL, isDevelopment };
