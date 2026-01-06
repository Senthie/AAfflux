/*
 * @Author: Senthie seemoon2077@gmail.com
 * @Date: 2026-01-06 11:29:13
 * @LastEditors: Senthie seemoon2077@gmail.com
 * @LastEditTime: 2026-01-06 12:07:56
 * @FilePath: /web/src/interfaces/IAuth.ts
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

interface ITokenPair {
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
}

interface IUserRes {
    id: string
    email: string
    name: string
    avatar_url: string
    created_at: number
    updated_at: number
}

interface IRegisterRes {
    user: IUserRes
    tokens: ITokenPair
}

interface ILoginRes {
    user: IUserRes
    tokens: ITokenPair
}
export type { IRegister, ILogin, ITokenPair, IRegisterRes, ILoginRes }
