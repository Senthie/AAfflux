/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 12:15:18
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 15:23:25
 * @FilePath: /web/src/stores/user-store.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */

import { defineStore } from 'pinia'
import { v1_auth_login, v1_auth_register } from 'src/apis/AuthApi'
import type { ILogin, ILoginRes, IRegister } from 'src/interfaces/IAuth'

export const useUserStore = defineStore('user', {
    state: (): ILoginRes => {
        return {
            user: {
                id: '',
                email: '',
                name: '',
                avatar_url: '',
                created_at: 0,
                updated_at: 0,
            },
            tokens: {
                access_token: '',
                refresh_token: '',
                token_type: '',
                expires_in: 0,
            },
        }
    },
    actions: {
        async register(user: IRegister) {
            const res = await v1_auth_register(user)
            if (res.code === 200) {
                this.user = res.data.user
                this.tokens = res.data.tokens
            }
        },
        async login(user: ILogin) {
            const res = await v1_auth_login(user)
            if (res.code === 200) {
                this.user = res.data.user
                this.tokens = res.data.tokens
            }
        },
    },
})
