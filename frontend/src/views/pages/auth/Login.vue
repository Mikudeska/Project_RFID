<script setup>
import FloatingConfigurator from '@/components/FloatingConfigurator.vue';
import { ref } from 'vue';

const email = ref('');
const password = ref('');
const checked = ref(false);
</script>

<template>
    <div>
        <FloatingConfigurator />
        <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden">
            <div class="flex flex-col items-center justify-center">
                <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                    <div class="w-full px-8 py-20 bg-surface-0 dark:bg-surface-900 sm:px-20" style="border-radius: 53px">
                        <div class="mb-8 text-center">
                            <svg viewBox="0 0 100 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <image href="https://ssru.ac.th/datafiles/loadimg/SSRU_LOGO1.png" x="40" y="0" height="30" width="20" />
                            </svg>
                            <div class="mb-4 text-3xl font-medium text-surface-900 dark:text-surface-0">SSRU_RFID</div>
                            <span class="font-medium text-muted-color">Sign in to continue</span>
                        </div>

                        <div>
                            <label for="email1" class="block mb-2 text-xl font-medium text-surface-900 dark:text-surface-0">Email</label>
                            <InputText id="email1" type="text" placeholder="Email address" class="w-full md:w-[30rem] mb-8" v-model="email" />

                            <label for="password1" class="block mb-2 text-xl font-medium text-surface-900 dark:text-surface-0">Password</label>
                            <Password id="password1" v-model="password" placeholder="Password" :toggleMask="true" class="mb-4" fluid :feedback="false" />

                            <div class="flex items-center justify-between gap-8 mt-2 mb-8">
                                <div class="flex items-center">
                                    <Checkbox v-model="checked" id="rememberme1" binary class="mr-2" />
                                    <label for="rememberme1">Remember me</label>
                                </div>
                                <span class="ml-2 font-medium text-right no-underline cursor-pointer text-primary">Forgot password?</span>
                            </div>
                            <Button label="Sign In" class="w-full" as="router-link" to="/" />
                        </div>

                        <div class="mb-1 text-center">Or</div>
                        <div class="flex items-center justify-between gap-5 mt-1 mb-7">
                            <Button label="Google sign in" class="w-full" as="router-link" to="/" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.pi-eye {
    transform: scale(1.6);
    margin-right: 1rem;
}

.pi-eye-slash {
    transform: scale(1.6);
    margin-right: 1rem;
}
</style>
