/**
 * 防抖工具函数
 * @param func 需要防抖的函数
 * @param delay 延迟时间（毫秒）
 * @returns 防抖后的函数，包含 flush 方法用于立即执行
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const debounce = <T extends (...args: any[]) => void>(
    func: T,
    delay: number
): ((...args: Parameters<T>) => void) & {
    flush: () => void
    cancel: () => void
} => {
    let timeoutId: NodeJS.Timeout | null = null
    let lastArgs: Parameters<T> | null = null

    const debouncedFunc = (...args: Parameters<T>) => {
        lastArgs = args
        if (timeoutId) {
            clearTimeout(timeoutId)
        }
        timeoutId = setTimeout(() => {
            func(...args)
            lastArgs = null
        }, delay)
    }

    // 立即执行函数
    debouncedFunc.flush = () => {
        if (timeoutId) {
            clearTimeout(timeoutId)
            timeoutId = null
        }
        if (lastArgs) {
            func(...lastArgs)
            lastArgs = null
        }
    }

    // 取消执行
    debouncedFunc.cancel = () => {
        if (timeoutId) {
            clearTimeout(timeoutId)
            timeoutId = null
        }
        lastArgs = null
    }

    return debouncedFunc
}

/**
 * 节流工具函数
 * @param func 需要节流的函数
 * @param delay 延迟时间（毫秒）
 * @returns 节流后的函数
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const throttle = <T extends (...args: any[]) => void>(
    func: T,
    delay: number
): ((...args: Parameters<T>) => void) => {
    let lastCall = 0
    return (...args: Parameters<T>) => {
        const now = Date.now()
        if (now - lastCall >= delay) {
            lastCall = now
            func(...args)
        }
    }
}
