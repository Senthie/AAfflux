# 用户 Store 安全持久化实现

## 概述

已为用户 Store 添加了安全的 token 持久化功能，确保 `refresh_token` 的安全存储，同时保持良好的用户体验。

## 安全特性

### Token 存储策略

1. **Access Token**: 存储在 `localStorage` 中
   - 便于快速访问
   - 生命周期较短，安全风险相对较低

2. **Refresh Token**: 优先存储在 Cookie 中
   - 使用 `secure` 标志（HTTPS 环境）
   - 使用 `sameSite: 'strict'` 防止 CSRF 攻击
   - 30 天过期时间
   - 如果 Cookie 设置失败，降级到 `localStorage`

3. **用户信息**: 使用 Pinia 持久化插件存储在 `localStorage`
   - 不包含敏感的 token 信息
   - 仅持久化用户基本信息

## 主要功能

### 1. 用户认证

```typescript
const userStore = useUserStore()

// 注册
await userStore.register({
  email: 'user@example.com',
  password: 'password123',
  name: 'Test User'
})

// 登录
await userStore.login({
  email: 'user@example.com',
  password: 'password123'
})
```

### 2. 状态检查

```typescript
// 检查是否已认证
if (userStore.isAuthenticated) {
  console.log('用户已登录')
}

// 检查是否有刷新令牌
if (userStore.hasRefreshToken) {
  console.log('可以自动刷新令牌')
}

// 获取访问令牌
const token = userStore.accessToken
```

### 3. Token 刷新

```typescript
// 自动刷新令牌（如果需要）
const success = await userStore.refreshTokenIfNeeded()
if (success) {
  console.log('令牌刷新成功')
}
```

### 4. 用户登出

```typescript
// 清除所有用户数据和令牌
userStore.logout()
```

### 5. 状态恢复

```typescript
// 应用启动时恢复用户状态
userStore.restoreFromStorage()
```

## 应用初始化示例

```typescript
// main.ts 或应用入口文件
import { useUserStore } from 'src/stores/user-store'

export function initializeApp() {
  const userStore = useUserStore()
  
  // 恢复用户状态
  userStore.restoreFromStorage()
  
  // 如果有刷新令牌，尝试自动登录
  if (userStore.hasRefreshToken) {
    userStore.refreshTokenIfNeeded().then(success => {
      if (success) {
        console.log('自动登录成功')
      } else {
        console.log('自动登录失败，需要重新登录')
      }
    })
  }
}
```

## API 接口

### 新增的 API 方法

1. **v1_auth_refresh**: 刷新访问令牌

   ```typescript
   const response = await v1_auth_refresh({
     refresh_token: 'your_refresh_token'
   })
   ```

## TokenManager 工具类

提供了完整的 token 管理功能：

```typescript
import { TokenManager } from 'src/utils/tokenManager'

// 设置 tokens
TokenManager.setTokens(tokens)

// 获取 tokens
const tokens = TokenManager.getTokens()

// 获取访问令牌
const accessToken = TokenManager.getAccessToken()

// 获取刷新令牌
const refreshToken = TokenManager.getRefreshToken()

// 清除所有 tokens
TokenManager.clearTokens()

// 检查是否有有效的访问令牌
const hasToken = TokenManager.hasValidAccessToken()

// 检查是否有刷新令牌
const hasRefresh = TokenManager.hasRefreshToken()

// 更新访问令牌和刷新令牌
TokenManager.updateTokens('new_access_token', 'new_refresh_token', 3600)
```

## 安全考虑

1. **HTTPS 环境**: 在生产环境中确保使用 HTTPS，以启用 Cookie 的 `secure` 标志
2. **Cookie 限制**: 浏览器端 JavaScript 无法设置真正的 `httpOnly` Cookie，这需要服务端配合
3. **降级策略**: 如果 Cookie 设置失败，会自动降级到 localStorage 存储
4. **自动清理**: Token 刷新失败时会自动清除所有认证信息

## 测试

已包含完整的测试覆盖：

```bash
# 运行所有测试
pnpm test

# 运行测试一次
pnpm test:run

# 运行测试 UI
pnpm test:ui
```

测试覆盖了：

- 基本的注册/登录功能
- Token 管理功能
- 错误处理
- 状态持久化

## 依赖

- `pinia-plugin-persistedstate`: Pinia 状态持久化
- `js-cookie`: Cookie 操作
- `@types/js-cookie`: TypeScript 类型定义

## 使用建议

1. 在应用启动时调用 `initializeApp()` 来恢复用户状态
2. 在 HTTP 拦截器中使用 `userStore.accessToken` 获取当前访问令牌
3. 在 401 错误时调用 `userStore.refreshTokenIfNeeded()` 尝试刷新令牌
4. 定期检查令牌有效性，必要时主动刷新
