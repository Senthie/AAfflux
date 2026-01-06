<!--
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 11:20:16
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 17:58:22
 * @FilePath: /web/src/pages/LoginPage.vue
 * @Description: 登录页面
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
-->

<script setup lang="ts">
import { Notify } from 'quasar'
import type { ILogin } from 'src/interfaces/IAuth'
import { useUserStore } from 'src/stores/user-store'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
const user_store = useUserStore()
const router = useRouter()
const login = ref<ILogin>({
    email: '',
    password: '',
})

const loginHandle = async () => {
    const res = await user_store.login(login.value)
    if (res.code == 200) {
        Notify.create({
            message: `欢迎尊贵的VIP${res.data.user.name}回家`,
            color: 'positive',
            position: 'top',
        })
        // 如果 成功登录，跳转到首页
        void router.push('/main')
    }
}
</script>
<template>
    <div>
        <q-input v-model="login.email" label="Email" style="width: 200px" />
        <q-input
            v-model="login.password"
            label="Password"
            style="width: 200px"
        />
        <div>
            <q-btn color="primary" label="Login" @click="loginHandle" />
        </div>
    </div>
</template>
<style lang="scss" scoped></style>
