/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-03-02 16:54:27
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-03-02 17:31:58
 * @FilePath: /web/src/apis/file_api.ts
 * @Description: 文件的api
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
import { api } from 'src/boot/axios'
import type {} from 'src/interfaces/IAuth'
import type { IResponse } from 'src/interfaces/IResponse'
import { Notify } from 'quasar'
import { extractErrorMessage } from 'src/utils/errorHandler'
import type { IFileUploadResponse } from 'src/interfaces/IFile'

/**
 * 文件上传
 * @param workspace_id 工作区id
 * @param file 原始文件类型
 * @returns Promise<IResponse<IRegisterRes>> 注册响应数据
 */
export async function v1_file_upload(
    workspace_id: string,
    file: File
): Promise<IResponse<IFileUploadResponse>> {
    try {
        // 创建 FormData 对象
        const formData = new FormData()
        formData.append('file', file)

        const response = await api.post<IResponse<IFileUploadResponse>>(
            '/v1/files/files/upload',
            formData,
            {
                params: {
                    workspace_id: workspace_id,
                },
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        )

        // 无论成功还是失败都显示消息
        if (response.data.code !== 200) {
            Notify.create({
                type: 'negative',
                message: response.data.msg || '上传失败',
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
            data: {} as IFileUploadResponse,
            timestamp: new Date().toISOString(),
        }
    }
}
