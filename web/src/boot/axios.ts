/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2025-11-26 10:24:58
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-09 15:10:01
 * @FilePath: /web/src/boot/axios.ts
 * @Description: axios配置文件
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { defineBoot } from '#q-app/wrappers'
import axios, { type AxiosInstance } from 'axios'
import { TokenManager } from 'src/utils/tokenManager'

declare module 'vue' {
    interface ComponentCustomProperties {
        $axios: AxiosInstance
        $api: AxiosInstance
    }
}

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)

// 使用环境变量配置 API 基础 URL
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
    baseURL,
    headers: {
        Authorization: `Bearer ${TokenManager.getAccessToken()}`,
    },
})

export default defineBoot(({ app }) => {
    // for use inside Vue files (Options API) through this.$axios and this.$api

    app.config.globalProperties.$axios = axios
    // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
    //       so you won't necessarily have to import axios in each vue file

    app.config.globalProperties.$api = api
    // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
    //       so you can easily perform requests against your app's API
})

export { api }
