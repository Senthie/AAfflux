/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-19 14:51:12
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-20 14:50:03
 * @FilePath: /web/src/interfaces/IPlugin.ts
 * @Description: plugin 的请求和返回值的抽象
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
export interface IPluginBase {
    name: string
    displya_name: string
    desc: string
    version: string
    author: string
    icon: string
    category: string
    plugin_type: string
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    manifest: Record<string, any>
    source_url: string
    documentation_url: string
}

export interface PluginResponse extends IPluginBase {
    id: string
    install_count: number
    rating: number
    is_active: boolean
    is_verified: boolean
    created_at: string
    updated_at: string
}
