/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-15 11:46:19
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-15 11:46:34
 * @FilePath: /web/src/boot/context-menu.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { boot } from 'quasar/wrappers'
import ContextMenu from '@imengyu/vue3-context-menu'
import '@imengyu/vue3-context-menu/lib/vue3-context-menu.css'

export default boot(({ app }) => {
    app.use(ContextMenu)
})
