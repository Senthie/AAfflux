/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-19 14:49:12
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-30 15:13:29
 * @FilePath: /web/src/apis/plugin_api.ts
 * @Description: 请求 plugin 的接口 方法
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */

import { Notify } from 'quasar'
import { api } from 'src/boot/axios'
import type { IPageReq, IPageRes } from 'src/interfaces/Ipage'
import type { PluginResponse } from 'src/interfaces/IPlugin'
import type { IResponse } from 'src/interfaces/IResponse'
import { extractErrorMessage } from 'src/utils/errorHandler'

// TOOD: 缺少过滤的条件
export async function v1_plugins_list(
    request: IPageReq
): Promise<IResponse<IPageRes<PluginResponse>>> {
    try {
        const response = await api.post<IResponse<IPageRes<PluginResponse>>>(
            `/v1/plugins/list`,

            request
        )

        // 无论成功还是失败都显示消息
        if (response.data.code !== 200) {
            Notify.create({
                type: 'negative',
                message: response.data.msg || '创建工作流失败',
            })
        }

        return response.data
    } catch (error) {
        const errorMessage = extractErrorMessage(error)

        Notify.create({
            type: 'negative',
            message: errorMessage,
        })

        // 返回一个错误响应格式
        return {
            code: 500,
            msg: errorMessage,
            data: {} as IPageRes<PluginResponse>,
            timestamp: new Date().toISOString(),
        }
    }
}

export async function v1_plugins_id(
    id: string
): Promise<IResponse<PluginResponse>> {
    try {
        const response = await api.get<IResponse<PluginResponse>>(
            `/v1/plugins/${id}`
        )

        if (response.data.code !== 200) {
            Notify.create({
                type: 'negative',
                message: response.data.msg || '获取插件详情失败',
            })
        }

        return response.data
    } catch (error) {
        const errorMessage = extractErrorMessage(error)

        Notify.create({
            type: 'negative',
            message: errorMessage,
        })

        return {
            code: 500,
            msg: errorMessage,
            data: {} as PluginResponse,
            timestamp: new Date().toISOString(),
        }
    }
}
