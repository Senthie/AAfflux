/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-08 14:12:08
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-12 11:43:33
 * @FilePath: /web/src/apis/workflow_api.ts
 * @Description:
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { Notify } from 'quasar'
import { api } from 'src/boot/axios'
import type { IResponse } from 'src/interfaces/IResponse'
import type {
    IWorkflowResponse,
    IWorkflowCreateRequest,
} from 'src/interfaces/IWorkflows'
import { extractErrorMessage } from 'src/utils/errorHandler'

export async function v1_create_workflow(
    request: IWorkflowCreateRequest,
    workspace_id: string
): Promise<IResponse<IWorkflowResponse>> {
    try {
        const response = await api.post<IResponse<IWorkflowResponse>>(
            `/v1/workflows/`,

            request,
            { params: { workspace_id: workspace_id } }
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
            data: {} as IWorkflowResponse,
            timestamp: new Date().toISOString(),
        }
    }
}
