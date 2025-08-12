import { defineStore } from 'pinia';
import { ref } from 'vue';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE;

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null);

    function setUser(data) {
        user.value = data;
        localStorage.setItem('user', JSON.stringify(data));
    }

    function loadUser() {
        const saved = localStorage.getItem('user');
        if (saved) user.value = JSON.parse(saved);
    }

    function logout() {
        user.value = null;
        localStorage.removeItem('user');
    }

    async function fetchUserProfile() {
        try {
            const res = await axios.get(`${API_BASE}/api/user-profile/`, { withCredentials: true });
            setUser(res.data);
        } catch (error) {
            console.error('fetchUserProfile error:', error);
            // กรณี error อาจ logout หรือจัดการอย่างอื่น
        }
    }

    return { user, setUser, loadUser, logout, fetchUserProfile };
});
