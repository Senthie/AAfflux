import { Notify } from 'quasar'
import { api } from 'src/boot/axios'
import type { IResponse } from 'src/interfaces/IResponse'
import type { IWorkspaceResponse } from 'src/interfaces/IWorkspace'

export async function v1_get_workspaces(): Promise<
    IResponse<Array<IWorkspaceResponse>>
> {
    try {
        const response = await api.get<IResponse<Array<IWorkspaceResponse>>>(
            '/v1/workspaces'
        )

        // 无论成功还是失败都显示消息
        if (response.data.code !== 200) {
            Notify.create({
                type: 'negative',
                message: response.data.msg || '注册失败',
            })
        }

        return response.data
    } catch (error) {
        const errorMessage =
            error instanceof Error ? error.message : '网络请求失败'

        Notify.create({
            type: 'negative',
            message: errorMessage,
        })

        // 返回一个错误响应格式
        return {
            code: 500,
            msg: errorMessage,
            data: [],
            timestamp: new Date().toISOString(),
        }
    }
}
