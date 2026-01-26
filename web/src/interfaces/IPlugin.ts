/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-19 14:51:12
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-26 14:32:36
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
    manifest: {
        internal: ManifestItem[]
        parameters: ManifestItem[]
    }
    source_url: string
    documentation_url: string
}
// 定义 Manifest 项的基础类型
export interface BaseManifestItem {
    type: string
    key: string
    label: string
    placeholder?: string
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    default?: any
    required?: boolean
    maxLength?: number
    validation?: {
        regex: string
        message: string
    }
}

// 扩展不同类型的具体定义
export interface TextInputManifestItem extends BaseManifestItem {
    type: 'textinput'
}

export interface TextAreaManifestItem extends BaseManifestItem {
    type: 'textarea'
}

export interface NumberManifestItem extends BaseManifestItem {
    type: 'number'
    min?: number
    max?: number
    step?: number
}

export interface ArrayManifestItem extends BaseManifestItem {
    type: 'array'
    itemType?: string
    items?: ManifestItem[]
}

export interface FileManifestItem extends BaseManifestItem {
    type: 'file'
    accept?: string
    multiple?: boolean
}

export interface BooleanManifestItem extends BaseManifestItem {
    type: 'boolean'
}

export interface SelectManifestItem extends BaseManifestItem {
    type: 'select'
    options: Array<{ label: string; value: string }>
}

// 联合类型
export type ManifestItem =
    | TextInputManifestItem
    | TextAreaManifestItem
    | NumberManifestItem
    | ArrayManifestItem
    | FileManifestItem
    | BooleanManifestItem
    | SelectManifestItem

// 根据 type 映射到对应的 TypeScript 类型
export type ManifestTypeMapping<T extends string> = T extends 'textinput'
    ? string
    : T extends 'textarea'
      ? string
      : T extends 'number'
        ? number
        : T extends 'array'
          ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
            any[]
          : T extends 'file'
            ? File | File[]
            : T extends 'boolean'
              ? boolean
              : T extends 'select'
                ? string
                : never

// 创建动态的 Record 类型
export type PluginConfigRecord = {
    [K in ManifestItem['key']]: ManifestTypeMapping<
        Extract<ManifestItem, { key: K }>['type']
    >
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
