import type { PluginConfigRecord, PluginResponse } from 'src/interfaces/IPlugin'

export class PluginUtil {
    // 读取 plugin manifest 并生成配置记录的方法
    static createPluginConfigRecord(
        plugin: PluginResponse
    ): PluginConfigRecord {
        // 合并所有 manifest 项
        const allManifestItems = [
            ...(plugin.manifest.internal || []),
            ...(plugin.manifest.parameters || []),
        ]

        // 创建初始配置对象
        const config: Record<string, any> = {}

        allManifestItems.forEach((item) => {
            const { key, type, default: defaultValue } = item

            // 根据类型设置默认值
            switch (type) {
                case 'textinput':
                case 'textarea':
                case 'select':
                    config[key] = defaultValue !== undefined ? defaultValue : ''
                    break
                case 'number':
                    config[key] =
                        defaultValue !== undefined ? Number(defaultValue) : 0
                    break
                case 'array':
                    config[key] = defaultValue !== undefined ? defaultValue : []
                    break
                case 'file':
                    config[key] =
                        defaultValue !== undefined ? defaultValue : null
                    break
                case 'boolean':
                    config[key] =
                        defaultValue !== undefined
                            ? Boolean(defaultValue)
                            : false
                    break
                default:
                    config[key] =
                        defaultValue !== undefined ? defaultValue : null
            }
        })

        return config as PluginConfigRecord
    }
    // 获取特定配置项的类型
    static getConfigValue<K extends keyof PluginConfigRecord>(
        config: PluginConfigRecord,
        key: K
    ): PluginConfigRecord[K] {
        return config[key]
    }

    // 设置配置值
    static setConfigValue<K extends keyof PluginConfigRecord>(
        config: PluginConfigRecord,
        key: K,
        value: PluginConfigRecord[K]
    ): void {
        config[key] = value
    }
    // 验证配置值
    static validateConfig(
        config: PluginConfigRecord,
        plugin: PluginResponse
    ): Record<string, string[]> {
        const errors: Record<string, string[]> = {}

        const allManifestItems = [
            ...(plugin.manifest.internal || []),
            ...(plugin.manifest.parameters || []),
        ]

        allManifestItems.forEach((item) => {
            const value = config[item.key]
            const itemErrors: string[] = []

            // 检查必填项
            if (
                item.required &&
                (value === undefined || value === null || value === '')
            ) {
                itemErrors.push(`${item.label} 是必填项`)
            }

            // 检查最大长度
            if (
                item.maxLength &&
                typeof value === 'string' &&
                value.length > item.maxLength
            ) {
                itemErrors.push(
                    `${item.label} 不能超过 ${item.maxLength} 个字符`
                )
            }

            // 检查正则表达式验证
            if (item.validation?.regex && typeof value === 'string') {
                const regex = new RegExp(item.validation.regex)
                if (!regex.test(value)) {
                    itemErrors.push(item.validation.message)
                }
            }

            // 检查数字范围
            if (item.type === 'number') {
                const numberItem = item
                const numValue = Number(value)

                if (numberItem.min !== undefined && numValue < numberItem.min) {
                    itemErrors.push(`${item.label} 不能小于 ${numberItem.min}`)
                }

                if (numberItem.max !== undefined && numValue > numberItem.max) {
                    itemErrors.push(`${item.label} 不能大于 ${numberItem.max}`)
                }
            }

            if (itemErrors.length > 0) {
                errors[item.key] = itemErrors
            }
        })

        return errors
    }
}
