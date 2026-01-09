/**
 * 错误处理工具函数
 */
import type { AxiosError } from 'axios'

/**
 * API 错误响应接口
 */
interface ApiErrorResponse {
    msg?: string
    message?: string
}

/**
 * 检查是否是 Axios 错误
 */
function isAxiosError(error: unknown): error is AxiosError<ApiErrorResponse> {
    return (
        error !== null &&
        typeof error === 'object' &&
        'isAxiosError' in error &&
        (error as AxiosError).isAxiosError === true
    )
}

/**
 * 从错误对象中提取错误消息
 * @param error 错误对象
 * @param defaultMessage 默认错误消息
 * @returns 错误消息字符串
 */
export function extractErrorMessage(
    error: unknown,
    defaultMessage = '网络请求失败'
): string {
    // 检查是否是 Axios 错误
    if (isAxiosError(error)) {
        // 优先使用后端返回的错误消息
        if (error.response?.data?.msg) {
            return error.response.data.msg
        }
        // 其次使用 Axios 错误消息
        if (error.message) {
            return error.message
        }
    }

    // 检查是否是标准 Error 对象
    if (error instanceof Error) {
        return error.message
    }

    // 如果是字符串类型的错误
    if (typeof error === 'string') {
        return error
    }

    return defaultMessage
}
