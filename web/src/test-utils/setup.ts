import { vi } from 'vitest'

// Mock Quasar Notify globally for tests
vi.mock('quasar', () => ({
    Notify: {
        create: vi.fn(),
    },
}))

// Global test utilities
export const createMockResponse = <T>(
    data: T,
    code = 200,
    msg = 'Success'
) => ({
    code,
    msg,
    data,
    timestamp: new Date().toISOString(),
})

export const createMockUser = (overrides = {}) => ({
    id: '123',
    email: 'test@example.com',
    name: 'Test User',
    avatar_url: 'https://example.com/avatar.jpg',
    created_at: 1641024000,
    updated_at: 1641024000,
    ...overrides,
})

export const createMockTokens = (overrides = {}) => ({
    access_token: 'mock_access_token',
    refresh_token: 'mock_refresh_token',
    token_type: 'Bearer',
    expires_in: 3600,
    ...overrides,
})
