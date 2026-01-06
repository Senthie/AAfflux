/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 15:25:00
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 15:45:11
 * @FilePath: /web/src/utils/tokenManager.ts
 * @Description: 安全的 Token 管理工具
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */

import Cookies from 'js-cookie'
import type { ITokenPair } from 'src/interfaces/IAuth'

const REFRESH_TOKEN_KEY = 'refresh_token'
const ACCESS_TOKEN_KEY = 'access_token'
const TOKEN_TYPE_KEY = 'token_type'
const EXPIRES_IN_KEY = 'expires_in'

export class TokenManager {
    /**
     * 设置 tokens，refresh_token 存储在 httpOnly cookie 中（如果可能）
     * access_token 存储在 localStorage 中
     */
    static setTokens(tokens: ITokenPair): void {
        // 存储 access_token 到 localStorage
        localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
        localStorage.setItem(TOKEN_TYPE_KEY, tokens.token_type)
        localStorage.setItem(EXPIRES_IN_KEY, tokens.expires_in.toString())

        // 尝试设置 refresh_token 到 secure cookie
        // 注意：在开发环境中，httpOnly 和 secure 可能需要调整
        try {
            Cookies.set(REFRESH_TOKEN_KEY, tokens.refresh_token, {
                httpOnly: false, // 浏览器端 JS 无法设置真正的 httpOnly，这需要服务端设置
                secure: window.location.protocol === 'https:', // 仅在 HTTPS 下使用 secure
                sameSite: 'strict',
                expires: 30, // 30 天过期
            })
        } catch (error) {
            console.warn('无法设置 refresh_token cookie:', error)
            // 降级到 localStorage（不推荐，但作为备选方案）
            localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
        }
    }

    /**
     * 获取完整的 token 对象
     */
    static getTokens(): ITokenPair {
        const access_token = localStorage.getItem(ACCESS_TOKEN_KEY) || ''
        const token_type = localStorage.getItem(TOKEN_TYPE_KEY) || ''
        const expires_in = parseInt(
            localStorage.getItem(EXPIRES_IN_KEY) || '0',
            10
        )

        // 优先从 cookie 获取 refresh_token
        let refresh_token = Cookies.get(REFRESH_TOKEN_KEY) || ''

        // 如果 cookie 中没有，尝试从 localStorage 获取（降级方案）
        if (!refresh_token) {
            refresh_token = localStorage.getItem(REFRESH_TOKEN_KEY) || ''
        }

        return {
            access_token,
            refresh_token,
            token_type,
            expires_in,
        }
    }

    /**
     * 获取 access_token
     */
    static getAccessToken(): string {
        return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
    }

    /**
     * 获取 refresh_token
     */
    static getRefreshToken(): string {
        // 优先从 cookie 获取
        let refresh_token = Cookies.get(REFRESH_TOKEN_KEY)

        // 如果 cookie 中没有，尝试从 localStorage 获取
        if (!refresh_token) {
            refresh_token = localStorage.getItem(REFRESH_TOKEN_KEY) || undefined
        }

        return refresh_token || ''
    }

    /**
     * 清除所有 tokens
     */
    static clearTokens(): void {
        // 清除 localStorage
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(TOKEN_TYPE_KEY)
        localStorage.removeItem(EXPIRES_IN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY) // 清除降级存储的 refresh_token

        // 清除 cookie
        Cookies.remove(REFRESH_TOKEN_KEY)
    }

    /**
     * 检查是否有有效的 access_token
     */
    static hasValidAccessToken(): boolean {
        const token = this.getAccessToken()
        return token.length > 0
    }

    /**
     * 检查是否有 refresh_token
     */
    static hasRefreshToken(): boolean {
        const token = this.getRefreshToken()
        return token.length > 0
    }

    /**
     * 更新 tokens（通常在刷新 token 后使用）
     */
    static updateTokens(
        access_token: string,
        refresh_token?: string,
        expires_in?: number
    ): void {
        localStorage.setItem(ACCESS_TOKEN_KEY, access_token)

        if (refresh_token) {
            // 更新 refresh_token，优先存储到 cookie
            try {
                Cookies.set(REFRESH_TOKEN_KEY, refresh_token, {
                    httpOnly: false,
                    secure: window.location.protocol === 'https:',
                    sameSite: 'strict',
                    expires: 30, // 30 天过期
                })
            } catch (error) {
                console.warn('无法设置 refresh_token cookie:', error)
                // 降级到 localStorage
                localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
            }
        }

        if (expires_in) {
            localStorage.setItem(EXPIRES_IN_KEY, expires_in.toString())
        }
    }
}
