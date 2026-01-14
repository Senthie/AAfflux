/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-13 12:13:35
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-13 12:15:05
 * @FilePath: /web/src/interfaces/Ipage.ts
 * @Description: 分页的接口对象
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
export interface IPageReq {
    total: number
    size: number
    current: number
    orders: string[]
    maxLimit: number
}

export interface IPageRes<T> {
    records: T[]
    total: number
    size: number
    current: number
    orders: string[]
    maxLimit: number
}
