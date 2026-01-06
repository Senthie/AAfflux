/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 11:49:34
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 11:53:23
 * @FilePath: /web/src/interfaces/IResponse.ts
 * @Description: 统一的返回格式
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */
export interface IResponse<T> {
    code: number
    msg: string
    data: T
    timestamp: string
}
