import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '@/plugins/axios'; // ใช้ไฟล์ axios ที่ทำ CSRF ไว้แล้ว

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null);
    const status = ref('Staff');
    const isAuthenticated = ref(false); // เพิ่มสถานะการล็อกอิน

    function setUser(data) {
        user.value = { ...(user.value || {}), ...data }; // แก้ไขเล็กน้อยเพื่อ merge ข้อมูลเก่าและใหม่
        if (data.status) status.value = data.status;
        isAuthenticated.value = !!data; // ตั้งค่าสถานะให้ล็อกอิน
        if (data) {
            localStorage.setItem('user', JSON.stringify(user.value));
        }
    }

    function loadUser() {
        const saved = localStorage.getItem('user');
        if (saved) {
            const data = JSON.parse(saved);
            user.value = data;
            if (data.status) status.value = data.status;
            isAuthenticated.value = true; // ตั้งค่าสถานะให้ล็อกอิน
        } else {
            isAuthenticated.value = false; // หากไม่มีข้อมูลผู้ใช้ใน localStorage ให้ตั้งเป็น false
        }
    }

    async function login(username, password) {
        try {
            await api.get('/api/get-csrf-token/'); // ให้ browser ได้ csrftoken
            const res = await api.post('/api/login/', { username, password });
            
            // res.data คือข้อมูล user/profile ที่ส่งมาจาก login_view เลย
            setUser(res.data); // data = { id, username, status, ... }
            
            // await fetchUserProfile(); // 👈 ลบ หรือ Comment บรรทัดนี้ (ไม่จำเป็นแล้ว)
        
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

    async function updateUserProfile(newProfileData) {
        try {
            const response = await api.put('/api/profile/', newProfileData);
            setUser(response.data);

            console.log('Pinia store updated successfully!', user.value);
        } catch (error) {
            console.error('Failed to update profile:', error);
            // อาจจะมีการแจ้งเตือนผู้ใช้ว่าบันทึกไม่สำเร็จ
            throw error;
        }
    }

    async function changeUserPassword(newPassword) {
        try {
            await api.post('/api/change-password/', { new_password: newPassword });
        } catch (error) {
            console.error('Failed to change password:', error);
            throw error; // ส่ง error ต่อไปให้ component จัดการ
        }
    }

    async function logout() {
        user.value = null;
        isAuthenticated.value = false; // ตั้งค่าการล็อกเอาท์
        localStorage.removeItem('user');
        await api.post('/api/logout/'); // backend clear session
    }

    return {
        user,
        status,
        isAuthenticated,
        setUser,
        loadUser,
        login,
        fetchUserProfile,
        logout,
        updateUserProfile,
        changeUserPassword
    };
});
