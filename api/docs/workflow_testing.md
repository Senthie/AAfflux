# 工作流测试功能文档

## 概述

工作流测试功能为低代码平台的用户提供了在开发过程中测试和调试工作流的能力。这是一个关键功能，让用户能够：

- 🧪 **测试工作流**：在不影响生产环境的情况下测试工作流
- 🔍 **调试执行**：获得详细的执行步骤和性能信息
- ✅ **验证配置**：检查工作流结构和配置的有效性
- 📊 **性能分析**：识别性能瓶颈和优化机会

## API 端点

### 1. 测试工作流执行

**端点**: `POST /api/v1/workflows/{workflow_id}/test`

测试工作流并返回详细的执行结果。

#### 请求体

```json
{
  "inputs": {
    "user_message": "Hello, world!",
    "temperature": 0.7,
    "max_tokens": 100
  },
  "options": {
    "timeout_seconds": 300,
    "debug_mode": false,
    "save_results": false,
    "mock_external_calls": true
  }
}
```

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "test_id": "uuid",
    "workflow_id": "uuid",
    "status": "SUCCESS",
    "inputs": {...},
    "outputs": {...},
    "started_at": "2026-02-03T10:00:00Z",
    "completed_at": "2026-02-03T10:00:05Z",
    "duration_ms": 5000,
    "node_results": [
      {
        "node_id": "node-1",
        "node_type": "LLM",
        "node_name": "Chat Completion",
        "status": "SUCCESS",
        "inputs": {...},
        "outputs": {...},
        "duration_ms": 2000,
        "execution_order": 1
      }
    ],
    "performance_metrics": {
      "total_duration_ms": 5000,
      "average_node_duration_ms": 1666,
      "total_nodes": 3,
      "successful_nodes": 3,
      "failed_nodes": 0
    }
  }
}
```

### 2. 验证工作流配置

**端点**: `POST /api/v1/workflows/{workflow_id}/validate`

验证工作流的结构和配置。

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      {
        "type": "MISSING_INPUT_SCHEMA",
        "severity": "WARNING",
        "message": "Workflow has no input schema defined",
        "suggestions": ["Define input schema to validate workflow inputs"]
      }
    ],
    "info": [],
    "node_count": 5,
    "connection_count": 4,
    "has_cycles": false,
    "entry_points": ["start-node"],
    "exit_points": ["end-node"]
  }
}
```

### 3. 调试工作流执行

**端点**: `POST /api/v1/workflows/{workflow_id}/debug`

提供详细的步骤级调试信息。

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "debug_id": "uuid",
    "workflow_id": "uuid",
    "status": "SUCCESS",
    "steps": [
      {
        "step_number": 1,
        "node_id": "node-1",
        "node_type": "LLM",
        "action": "EXECUTE",
        "inputs": {...},
        "outputs": {...},
        "variables": {...},
        "started_at": "2026-02-03T10:00:00Z",
        "completed_at": "2026-02-03T10:00:02Z",
        "duration_ms": 2000,
        "logs": ["Starting LLM execution", "API call completed"],
        "error": null
      }
    ],
    "total_steps": 5,
    "successful_steps": 5,
    "failed_steps": 0,
    "skipped_steps": 0,
    "bottlenecks": [],
    "recommendations": [
      "Consider caching LLM responses for similar inputs",
      "Optimize node configuration for better performance"
    ]
  }
}
```

## 测试选项说明

### timeout_seconds

- **默认值**: 300
- **说明**: 测试执行的超时时间（秒）
- **用途**: 防止长时间运行的测试阻塞系统

### debug_mode

- **默认值**: false
- **说明**: 是否启用调试模式
- **用途**: 启用时会收集更详细的执行信息

### save_results

- **默认值**: false
- **说明**: 是否保存测试结果
- **用途**: 保存测试结果以供后续分析

### mock_external_calls

- **默认值**: true
- **说明**: 是否模拟外部API调用
- **用途**: 在测试环境中避免真实的外部调用

## 使用场景

### 1. 开发阶段测试

在开发工作流时，使用基本测试功能验证逻辑：

```bash
curl -X POST \
  http://localhost:8000/api/v1/workflows/{workflow_id}/test \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"message": "test"},
    "options": {"mock_external_calls": true}
  }'
```

### 2. 性能优化

使用调试模式识别性能瓶颈：

```bash
curl -X POST \
  http://localhost:8000/api/v1/workflows/{workflow_id}/debug \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"message": "performance test"},
    "options": {"debug_mode": true}
  }'
```

### 3. 配置验证

在部署前验证工作流配置：

```bash
curl -X POST \
  http://localhost:8000/api/v1/workflows/{workflow_id}/validate \
  -H "Authorization: Bearer your-token"
```

## 错误处理

### 常见错误类型

1. **MISSING_CONFIG**: 节点配置缺失
2. **INVALID_CONNECTION**: 无效的节点连接
3. **CYCLE_DETECTED**: 检测到循环依赖
4. **UNSUPPORTED_NODE_TYPE**: 不支持的节点类型
5. **TIMEOUT**: 执行超时

### 错误响应格式

```json
{
  "code": 400,
  "message": "Workflow test failed",
  "data": {
    "test_id": "uuid",
    "status": "FAILED",
    "error": "Node execution failed: Missing required input 'api_key'",
    "node_results": [...]
  }
}
```

## 最佳实践

### 1. 测试策略

- **渐进式测试**: 从简单的单节点工作流开始测试
- **边界测试**: 测试极端输入值和边界条件
- **错误场景**: 故意触发错误以验证错误处理

### 2. 性能优化

- **使用调试模式**: 识别慢节点和瓶颈
- **监控资源使用**: 关注内存和CPU使用情况
- **缓存策略**: 对重复计算使用缓存

### 3. 配置管理

- **定期验证**: 在修改工作流后立即验证
- **版本控制**: 跟踪工作流配置的变更
- **文档化**: 记录复杂工作流的设计决策

## 集成示例

### Python 客户端

```python
import asyncio
import httpx

async def test_workflow(workflow_id: str, inputs: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/workflows/{workflow_id}/test",
            headers={"Authorization": "Bearer your-token"},
            json={"inputs": inputs}
        )
        return response.json()

# 使用示例
result = asyncio.run(test_workflow(
    "workflow-id", 
    {"message": "Hello, world!"}
))
```

### JavaScript 客户端

```javascript
async function testWorkflow(workflowId, inputs) {
  const response = await fetch(
    `http://localhost:8000/api/v1/workflows/${workflowId}/test`,
    {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer your-token',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ inputs })
    }
  );
  
  return response.json();
}

// 使用示例
testWorkflow('workflow-id', { message: 'Hello, world!' })
  .then(result => console.log(result));
```

## 监控和日志

### 测试指标

系统会自动收集以下测试指标：

- 测试执行次数
- 成功/失败率
- 平均执行时间
- 节点性能分布

### 日志记录

测试执行会生成详细日志：

- 执行开始/结束时间
- 每个节点的输入/输出
- 错误信息和堆栈跟踪
- 性能指标

## 故障排除

### 常见问题

1. **测试超时**
   - 检查节点配置是否正确
   - 增加超时时间
   - 启用调试模式查看详细信息

2. **节点执行失败**
   - 验证输入数据格式
   - 检查节点配置
   - 查看错误日志

3. **性能问题**
   - 使用调试模式分析瓶颈
   - 优化慢节点配置
   - 考虑并行执行

### 调试技巧

1. **启用详细日志**: 设置 `debug_mode: true`
2. **分步测试**: 测试单个节点或小的工作流片段
3. **模拟外部调用**: 使用 `mock_external_calls: true` 隔离问题
4. **检查输入数据**: 确保输入数据符合预期格式

## 总结

工作流测试功能是低代码平台的重要组成部分，它提供了：

- 🔧 **开发工具**: 帮助用户在开发过程中验证工作流
- 🐛 **调试能力**: 提供详细的执行信息和错误诊断
- 📈 **性能洞察**: 识别优化机会和性能瓶颈
- ✅ **质量保证**: 确保工作流在部署前正常工作

通过合理使用这些测试功能，用户可以构建更可靠、更高效的工作流应用。
