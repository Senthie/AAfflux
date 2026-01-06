/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 15:45:00
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 15:54:40
 * @FilePath: /web/src/examples/userStoreUsage.ts
 * @Description: 用户 Store 使用示例
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */

import { useUserStore } from 'src/stores/user-store'

// 使用示例
export function userStoreExamples() {
    const userStore = useUserStore()

    // 1. 用户注册
    async function registerUser() {
        try {
            const result = await userStore.register({
                email: 'user@example.com',
                password: 'password123',
                name: 'Test User',
            })

            if (result.code === 200) {
                console.log('注册成功，用户已登录')
                console.log('用户信息:', userStore.user)
                console.log('是否已认证:', userStore.isAuthenticated)
            }
        } catch (error) {
            console.error('注册失败:', error)
        }
    }

    // 2. 用户登录
    async function loginUser() {
        try {
            const result = await userStore.login({
                email: 'user@example.com',
                password: 'password123',
            })

            if (result.code === 200) {
                console.log('登录成功')
                console.log('Access Token:', userStore.accessToken)
                console.log('是否有刷新令牌:', userStore.hasRefreshToken)
            }
        } catch (error) {
            console.error('登录失败:', error)
        }
    }

    // 3. 检查认证状态
    function checkAuthStatus() {
        if (userStore.isAuthenticated) {
            console.log('用户已认证')
            console.log('用户ID:', userStore.user.id)
            console.log('用户邮箱:', userStore.user.email)
        } else {
            console.log('用户未认证')
        }
    }

    // 4. 刷新令牌
    async function refreshToken() {
        const success = await userStore.refreshTokenIfNeeded()
        if (success) {
            console.log('令牌刷新成功')
        } else {
            console.log('令牌刷新失败或不需要刷新')
        }
    }

    // 5. 用户登出
    function logoutUser() {
        userStore.logout()
        console.log('用户已登出')
        console.log('是否已认证:', userStore.isAuthenticated)
    }

    // 6. 从存储中恢复状态（应用启动时调用）
    function restoreUserState() {
        userStore.restoreFromStorage()
        console.log('用户状态已从存储中恢复')

        if (userStore.hasRefreshToken) {
            console.log('发现刷新令牌，可以尝试自动登录')
            // 可以在这里调用 refreshTokenIfNeeded 来验证令牌
        }
    }

    return {
        registerUser,
        loginUser,
        checkAuthStatus,
        refreshToken,
        logoutUser,
        restoreUserState,
    }
}

// 应用启动时的初始化示例
export function initializeApp() {
    const userStore = useUserStore()

    // 恢复用户状态
    userStore.restoreFromStorage()

    // 如果有刷新令牌，尝试刷新访问令牌
    if (userStore.hasRefreshToken) {
        void userStore.refreshTokenIfNeeded().then((success) => {
            if (success) {
                console.log('自动登录成功')
            } else {
                console.log('自动登录失败，需要重新登录')
            }
        })
    }
}
