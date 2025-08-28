import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '@/plugins/axios'; // ใช้ไฟล์ axios ที่ทำ CSRF ไว้แล้ว

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

    async function login(username, password) {
        try {
            await api.get('/api/get-csrf-token/'); // ให้ browser ได้ csrftoken
            const res = await api.post('/api/login/', { username, password });
            setUser(res.data); // data = { id, username } (จาก backend)
            await fetchUserProfile(); // โหลดข้อมูลเต็ม ๆ
        } catch (err) {
            console.error('Login error:', err);
            throw err;
        }
    }

    async function fetchUserProfile() {
        try {
            const res = await api.get('/api/profile/');
            setUser(res.data);
        } catch (err) {
            console.error('fetchUserProfile error:', err);
        }
    }

    async function logout() {
        user.value = null;
        localStorage.removeItem('user');
        await api.post('/api/logout/'); // backend clear session
    }

    return { user, setUser, loadUser, login, fetchUserProfile, logout };
});
