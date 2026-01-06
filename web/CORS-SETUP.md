# CORS 跨域问题解决方案

## 问题描述

在开发环境中，前端应用运行在 `http://localhost:9001`，而后端 API 运行在 `http://14.12.0.212:8000`，由于浏览器的同源策略，会出现 CORS 跨域错误。

## 解决方案

### 1. 开发环境代理配置

在 `quasar.config.ts` 中配置了开发服务器代理：

```typescript
devServer: {
    open: true,
    proxy: {
        '/api': {
            target: 'http://14.12.0.212:8000',
            changeOrigin: true,
            secure: false,
            ws: true,
        }
    }
}
```

### 2. API 基础 URL 配置

在 `src/boot/axios.ts` 中配置了环境相关的 API 基础 URL：

```typescript
// 使用环境变量配置 API 基础 URL
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
const api = axios.create({ baseURL })
```

### 3. 环境变量配置

创建了环境变量文件：

**`.env.development`**:

```
VITE_API_BASE_URL=/api
VITE_API_TARGET=http://14.12.0.212:8000
```

**`.env.production`**:

```
VITE_API_BASE_URL=http://14.12.0.212:8000/api
```

### 4. API 路径调整

在 `src/apis/AuthApi.ts` 中，将 API 路径从 `/api/v1/auth/login` 改为 `/v1/auth/login`，避免重复的 `/api` 前缀。

## 工作原理

1. **开发环境**:
   - 前端请求 `/api/v1/auth/login`
   - 开发服务器代理将请求转发到 `http://14.12.0.212:8000/api/v1/auth/login`
   - 避免了跨域问题

2. **生产环境**:
   - 直接使用完整的 API URL `http://14.12.0.212:8000/api/v1/auth/login`

## 测试

重启开发服务器后，CORS 错误应该消失，API 请求能够正常工作。

```bash
npm run dev
```

## 注意事项

- 每次修改 `quasar.config.ts` 后需要重启开发服务器
- 生产环境部署时需要确保后端正确配置 CORS 头部
- 如果后端 API 地址发生变化，需要更新环境变量文件
