/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 11:29:13
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 11:33:41
 * @FilePath: /web/src/interfaces/request/IAuth.ts
 * @Description: 用户账号
 *
 * Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
 */

interface IRegister {
    email: string
    password: string
    name: string
}

interface ILogin {
    email: string
    password: string
}
export type { IRegister, ILogin }
