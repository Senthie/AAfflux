import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../user-store'
import * as AuthApi from 'src/apis/auth_api'
import type {
    ILogin,
    IRegister,
    ILoginRes,
    IRegisterRes,
} from 'src/interfaces/IAuth'

// Mock the AuthApi module
vi.mock('src/apis/AuthApi', () => ({
    v1_auth_register: vi.fn(),
    v1_auth_login: vi.fn(),
}))

describe('User Store', () => {
    let store: ReturnType<typeof useUserStore>

    beforeEach(() => {
        // Create a fresh pinia instance for each test
        setActivePinia(createPinia())
        store = useUserStore()

        // Clear all mocks before each test
        vi.clearAllMocks()
    })

    describe('Initial State', () => {
        it('should have correct initial state', () => {
            expect(store.user).toEqual({
                id: '',
                email: '',
                name: '',
                avatar_url: '',
                created_at: 0,
                updated_at: 0,
            })

            expect(store.tokens).toEqual({
                access_token: '',
                refresh_token: '',
                token_type: '',
                expires_in: 0,
            })
        })
    })

    describe('register method', () => {
        const mockRegisterData: IRegister = {
            email: 'test@example.com',
            password: 'password123',
            name: 'Test User',
        }

        const mockSuccessResponse = {
            code: 200,
            msg: '注册成功',
            data: {
                user: {
                    id: '123',
                    email: 'test@example.com',
                    name: 'Test User',
                    avatar_url: 'https://example.com/avatar.jpg',
                    created_at: 1641024000,
                    updated_at: 1641024000,
                },
                tokens: {
                    access_token: 'mock_access_token',
                    refresh_token: 'mock_refresh_token',
                    token_type: 'Bearer',
                    expires_in: 3600,
                },
            } as IRegisterRes,
            timestamp: '2026-01-06T12:00:00Z',
        }

        it('should register user successfully when API returns 200', async () => {
            // Mock successful API response
            vi.mocked(AuthApi.v1_auth_register).mockResolvedValue(
                mockSuccessResponse
            )

            await store.register(mockRegisterData)

            // Verify API was called with correct data
            expect(AuthApi.v1_auth_register).toHaveBeenCalledWith(
                mockRegisterData
            )
            expect(AuthApi.v1_auth_register).toHaveBeenCalledTimes(1)

            // Verify store state was updated
            expect(store.user).toEqual(mockSuccessResponse.data.user)
            expect(store.tokens).toEqual(mockSuccessResponse.data.tokens)
        })

        it('should not update store state when API returns non-200 code', async () => {
            const mockErrorResponse = {
                code: 400,
                msg: '注册失败',
                data: {} as IRegisterRes,
                timestamp: '2026-01-06T12:00:00Z',
            }

            // Store initial state for comparison
            const initialUser = { ...store.user }
            const initialTokens = { ...store.tokens }

            vi.mocked(AuthApi.v1_auth_register).mockResolvedValue(
                mockErrorResponse
            )

            await store.register(mockRegisterData)

            // Verify API was called
            expect(AuthApi.v1_auth_register).toHaveBeenCalledWith(
                mockRegisterData
            )

            // Verify store state was not updated
            expect(store.user).toEqual(initialUser)
            expect(store.tokens).toEqual(initialTokens)
        })

        it('should handle API errors gracefully', async () => {
            const initialUser = { ...store.user }
            const initialTokens = { ...store.tokens }

            // Mock API rejection
            vi.mocked(AuthApi.v1_auth_register).mockRejectedValue(
                new Error('Network error')
            )

            await expect(store.register(mockRegisterData)).rejects.toThrow(
                'Network error'
            )

            // Verify store state was not updated
            expect(store.user).toEqual(initialUser)
            expect(store.tokens).toEqual(initialTokens)
        })
    })

    describe('login method', () => {
        const mockLoginData: ILogin = {
            email: 'test@example.com',
            password: 'password123',
        }

        const mockSuccessResponse = {
            code: 200,
            msg: '登录成功',
            data: {
                user: {
                    id: '123',
                    email: 'test@example.com',
                    name: 'Test User',
                    avatar_url: 'https://example.com/avatar.jpg',
                    created_at: 1641024000,
                    updated_at: 1641024000,
                },
                tokens: {
                    access_token: 'mock_access_token',
                    refresh_token: 'mock_refresh_token',
                    token_type: 'Bearer',
                    expires_in: 3600,
                },
            } as ILoginRes,
            timestamp: '2026-01-06T12:00:00Z',
        }

        it('should login user successfully when API returns 200', async () => {
            // Mock successful API response
            vi.mocked(AuthApi.v1_auth_login).mockResolvedValue(
                mockSuccessResponse
            )

            await store.login(mockLoginData)

            // Verify API was called with correct data
            expect(AuthApi.v1_auth_login).toHaveBeenCalledWith(mockLoginData)
            expect(AuthApi.v1_auth_login).toHaveBeenCalledTimes(1)

            // Verify store state was updated
            expect(store.user).toEqual(mockSuccessResponse.data.user)
            expect(store.tokens).toEqual(mockSuccessResponse.data.tokens)
        })

        it('should not update store state when API returns non-200 code', async () => {
            const mockErrorResponse = {
                code: 401,
                msg: '登录失败',
                data: {} as ILoginRes,
                timestamp: '2026-01-06T12:00:00Z',
            }

            // Store initial state for comparison
            const initialUser = { ...store.user }
            const initialTokens = { ...store.tokens }

            vi.mocked(AuthApi.v1_auth_login).mockResolvedValue(
                mockErrorResponse
            )

            await store.login(mockLoginData)

            // Verify API was called
            expect(AuthApi.v1_auth_login).toHaveBeenCalledWith(mockLoginData)

            // Verify store state was not updated
            expect(store.user).toEqual(initialUser)
            expect(store.tokens).toEqual(initialTokens)
        })

        it('should handle API errors gracefully', async () => {
            const initialUser = { ...store.user }
            const initialTokens = { ...store.tokens }

            // Mock API rejection
            vi.mocked(AuthApi.v1_auth_login).mockRejectedValue(
                new Error('Network error')
            )

            await expect(store.login(mockLoginData)).rejects.toThrow(
                'Network error'
            )

            // Verify store state was not updated
            expect(store.user).toEqual(initialUser)
            expect(store.tokens).toEqual(initialTokens)
        })
    })

    describe('Integration scenarios', () => {
        it('should handle sequential register and login operations', async () => {
            const registerData: IRegister = {
                email: 'test@example.com',
                password: 'password123',
                name: 'Test User',
            }

            const loginData: ILogin = {
                email: 'test@example.com',
                password: 'password123',
            }

            const mockRegisterResponse = {
                code: 200,
                msg: '注册成功',
                data: {
                    user: {
                        id: '123',
                        email: 'test@example.com',
                        name: 'Test User',
                        avatar_url: 'https://example.com/avatar.jpg',
                        created_at: 1641024000,
                        updated_at: 1641024000,
                    },
                    tokens: {
                        access_token: 'register_access_token',
                        refresh_token: 'register_refresh_token',
                        token_type: 'Bearer',
                        expires_in: 3600,
                    },
                } as IRegisterRes,
                timestamp: '2026-01-06T12:00:00Z',
            }

            const mockLoginResponse = {
                code: 200,
                msg: '登录成功',
                data: {
                    user: {
                        id: '123',
                        email: 'test@example.com',
                        name: 'Test User',
                        avatar_url: 'https://example.com/avatar.jpg',
                        created_at: 1641024000,
                        updated_at: 1641024000,
                    },
                    tokens: {
                        access_token: 'login_access_token',
                        refresh_token: 'login_refresh_token',
                        token_type: 'Bearer',
                        expires_in: 3600,
                    },
                } as ILoginRes,
                timestamp: '2026-01-06T12:00:00Z',
            }

            // Mock register
            vi.mocked(AuthApi.v1_auth_register).mockResolvedValue(
                mockRegisterResponse
            )
            await store.register(registerData)

            expect(store.tokens.access_token).toBe('register_access_token')

            // Mock login
            vi.mocked(AuthApi.v1_auth_login).mockResolvedValue(
                mockLoginResponse
            )
            await store.login(loginData)

            expect(store.tokens.access_token).toBe('login_access_token')
            expect(AuthApi.v1_auth_register).toHaveBeenCalledTimes(1)
            expect(AuthApi.v1_auth_login).toHaveBeenCalledTimes(1)
        })
    })
})
