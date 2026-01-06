/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 12:15:18
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 17:43:56
 * @FilePath: /web/src/stores/user-store.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */

import { defineStore } from 'pinia'
import {
    v1_auth_login,
    v1_auth_register,
    v1_auth_refresh,
} from 'src/apis/AuthApi'
import type {
    ILogin,
    ILoginRes,
    IRegister,
    ITokenPair,
    IUserRes,
} from 'src/interfaces/IAuth'
import type { IResponse } from 'src/interfaces/IResponse'
import { TokenManager } from 'src/utils/tokenManager'

export const useUserStore = defineStore('user', {
    state: () => {
        // 从持久化存储中恢复 tokens
        const persistedTokens = TokenManager.getTokens()

        return {
            user: {
                id: '',
                email: '',
                name: '',
                avatar_url: '',
                created_at: 0,
                updated_at: 0,
            } as IUserRes,
            tokens: persistedTokens,
        }
    },

    getters: {
        isAuthenticated: (state): boolean => {
            return TokenManager.hasValidAccessToken() && state.user.id !== ''
        },

        hasRefreshToken: (): boolean => {
            return TokenManager.hasRefreshToken()
        },

        accessToken: (): string => {
            return TokenManager.getAccessToken()
        },
    },

    actions: {
        /**
         * 用户注册
         */
        async register(user: IRegister) {
            const res = await v1_auth_register(user)
            if (res.code === 200) {
                this.setUserData(res.data.user, res.data.tokens)
            }
            return res
        },

        /**
         * 用户登录
         */
        async login(user: ILogin): Promise<IResponse<ILoginRes>> {
            const res = await v1_auth_login(user)
            if (res.code === 200) {
                this.setUserData(res.data.user, res.data.tokens)
            }
            return res
        },

        /**
         * 设置用户数据和 tokens（内部方法）
         */
        setUserData(user: IUserRes, tokens: ITokenPair) {
            this.user = user
            this.tokens = tokens

            // 安全地存储 tokens
            TokenManager.setTokens(tokens)
        },

        /**
         * 更新 tokens（用于 token 刷新）
         */
        updateTokens(
            access_token: string,
            refresh_token?: string,
            expires_in?: number
        ) {
            this.tokens.access_token = access_token
            if (refresh_token) {
                this.tokens.refresh_token = refresh_token
            }
            if (expires_in) {
                this.tokens.expires_in = expires_in
            }

            TokenManager.updateTokens(access_token, refresh_token, expires_in)
        },

        /**
         * 用户登出
         */
        logout() {
            // 清除状态
            this.user = {
                id: '',
                email: '',
                name: '',
                avatar_url: '',
                created_at: 0,
                updated_at: 0,
            }
            this.tokens = {
                access_token: '',
                refresh_token: '',
                token_type: '',
                expires_in: 0,
            }

            // 清除持久化的 tokens
            TokenManager.clearTokens()
        },

        /**
         * 从持久化存储中恢复用户状态
         */
        restoreFromStorage() {
            const tokens = TokenManager.getTokens()
            this.tokens = tokens

            // TOOD: 如果有有效的 access token，可以考虑验证用户信息
            // TOOD: 这里可以添加一个 API 调用来获取当前用户信息
        },

        /**
         * 检查并刷新 token（如果需要）
         */
        async refreshTokenIfNeeded() {
            if (!TokenManager.hasRefreshToken()) {
                return false
            }

            try {
                const refreshToken = TokenManager.getRefreshToken()
                const res = await v1_auth_refresh({
                    refresh_token: refreshToken,
                })
                if (res.code === 200) {
                    this.updateTokens(
                        res.data.access_token,
                        res.data.refresh_token, // 后端刷新token后会将refresh_token也刷新
                        res.data.expires_in
                    )
                    return true
                }
                return false
            } catch (error) {
                console.error('Token refresh failed:', error)
                this.logout() // 刷新失败，清除所有数据
                return false
            }
        },
    },

    // 使用 pinia-plugin-persistedstate 持久化用户信息（不包括敏感的 tokens）
    persist: {
        key: 'user-store',
        storage: localStorage,
        pick: ['user'], // 只持久化用户信息，不持久化 tokens
    },
})
