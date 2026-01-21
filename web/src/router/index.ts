/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-08 14:12:08
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-20 18:03:23
 * @FilePath: /web/src/router/index.ts
 * @Description: 注册历史路由
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { defineRouter } from '#q-app/wrappers'
import {
    createMemoryHistory,
    createRouter,
    createWebHashHistory,
    createWebHistory,
} from 'vue-router'
import routes from './routes'

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(function (/* { store, ssrContext } */) {
    const createHistory = process.env.SERVER
        ? createMemoryHistory
        : process.env.VUE_ROUTER_MODE === 'history'
          ? createWebHistory
          : createWebHashHistory

    const Router = createRouter({
        scrollBehavior: () => ({ left: 0, top: 0 }),
        routes,

        // Leave this as is and make changes in quasar.conf.js instead!
        // quasar.conf.js -> build -> vueRouterMode
        // quasar.conf.js -> build -> publicPath
        history: createHistory(process.env.VUE_ROUTER_BASE),
    })

    return Router
})
