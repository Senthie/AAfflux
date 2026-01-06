import { describe, it, expect, vi, beforeEach } from 'vitest'
import { TokenManager } from '../tokenManager'
import Cookies from 'js-cookie'
import type { ITokenPair } from 'src/interfaces/IAuth'

// Mock js-cookie
vi.mock('js-cookie', () => ({
    default: {
        set: vi.fn(),
        get: vi.fn(() => undefined),
        remove: vi.fn(),
    },
}))

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
})

// Mock window.location
Object.defineProperty(window, 'location', {
    value: {
        protocol: 'https:',
    },
    writable: true,
})

describe('TokenManager', () => {
    const mockTokens: ITokenPair = {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'Bearer',
        expires_in: 3600,
    }

    beforeEach(() => {
        vi.clearAllMocks()
    })

    describe('setTokens', () => {
        it('should store access_token in localStorage', () => {
            TokenManager.setTokens(mockTokens)

            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'access_token',
                mockTokens.access_token
            )
            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'token_type',
                mockTokens.token_type
            )
            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'expires_in',
                mockTokens.expires_in.toString()
            )
        })
    })

    describe('updateTokens', () => {
        it('should update access token in localStorage', () => {
            TokenManager.updateTokens('new_access_token', undefined, 7200)

            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'access_token',
                'new_access_token'
            )
            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'expires_in',
                '7200'
            )
        })

        it('should update access token without expires_in', () => {
            TokenManager.updateTokens('new_access_token')

            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'access_token',
                'new_access_token'
            )
            expect(localStorageMock.setItem).not.toHaveBeenCalledWith(
                'expires_in',
                expect.anything()
            )
        })

        it('should update both access and refresh tokens', () => {
            TokenManager.updateTokens(
                'new_access_token',
                'new_refresh_token',
                7200
            )

            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'access_token',
                'new_access_token'
            )
            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'expires_in',
                '7200'
            )
            // eslint-disable-next-line @typescript-eslint/unbound-method
            expect(Cookies.set).toHaveBeenCalledWith(
                'refresh_token',
                'new_refresh_token',
                {
                    httpOnly: false,
                    secure: true,
                    sameSite: 'strict',
                    expires: 30,
                }
            )
        })

        it('should fallback to localStorage for refresh_token if cookie fails', () => {
            const consoleSpy = vi
                .spyOn(console, 'warn')
                .mockImplementation(() => {})
            // eslint-disable-next-line @typescript-eslint/unbound-method
            vi.mocked(Cookies.set).mockImplementation(() => {
                throw new Error('Cookie setting failed')
            })

            TokenManager.updateTokens('new_access_token', 'new_refresh_token')

            expect(localStorageMock.setItem).toHaveBeenCalledWith(
                'refresh_token',
                'new_refresh_token'
            )
            expect(consoleSpy).toHaveBeenCalledWith(
                '无法设置 refresh_token cookie:',
                expect.any(Error)
            )

            consoleSpy.mockRestore()
        })
    })
})
