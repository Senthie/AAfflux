/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2025-11-26 10:24:58
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 18:02:19
 * @FilePath: /web/src/router/routes.ts
 * @Description: 路由配置页面
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        component: () => import('layouts/PortalLayout.vue'),
        children: [
            { path: '', component: () => import('pages/LoginPage.vue') },
        ],
    },
    {
        path: '/main',
        component: () => import('layouts/MainLayout.vue'),
        children: [
            { path: '', component: () => import('pages/IndexPage.vue') },
        ],
    },
    // Always leave this as last one,
    // but you can also remove it
    {
        path: '/:catchAll(.*)*',
        component: () => import('pages/ErrorNotFound.vue'),
    },
]

export default routes
