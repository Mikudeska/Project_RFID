import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null)

    function setUser(data) {
        user.value = data
        localStorage.setItem('user', JSON.stringify(data))
    }

    function loadUser() {
        const saved = localStorage.getItem('user')
        if (saved) user.value = JSON.parse(saved)
    }

    function logout() {
        user.value = null
        localStorage.removeItem('user')
    }

    return { user, setUser, loadUser, logout }
})
