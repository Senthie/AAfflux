# ComfyUI 工作流 API 测试文档

基于 `test_base_comfyui` 测试用例，本文档提供了完整的 API 请求测试和 curl 命令测试。

## 测试概述

该工作流实现了一个完整的 AI 图像生成流程：

1. **Chat Node**: 提供初始描述 "公交站里的女孩"
2. **Ollama Agent**: 将中文描述转换为 Stable Diffusion 英文提示词
3. **ComfyUI HTTP Node**: 调用 ComfyUI API 生成图像

## 环境配置

```bash
# 服务器配置
API_BASE_URL="http://localhost:8000"
OLLAMA_BASE_URL="http://14.12.0.172:19516"
COMFYUI_BASE_URL="http://14.12.0.172:9898"

# 认证信息
JWT_TOKEN="your_jwt_token_here"
API_KEY="your_api_key_here"
```

## 1. 工作流管理 API 测试

### 1.1 创建工作流

**API 请求:**

```http
POST /api/v1/workflows/
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "name": "ComfyUI Image Generation Workflow",
  "description": "AI图像生成工作流：中文描述 -> 英文提示词 -> ComfyUI生成图像",
  "input_schema": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "图像描述"
      }
    },
    "required": ["prompt"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "image_url": {
        "type": "string",
        "description": "生成的图像URL"
      },
      "prompt_id": {
        "type": "string",
        "description": "ComfyUI任务ID"
      }
    }
  }
}
```

**curl 命令:**

```bash
curl -X POST "${API_BASE_URL}/api/v1/workflows/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "name": "ComfyUI Image Generation Workflow",
    "description": "AI图像生成工作流：中文描述 -> 英文提示词 -> ComfyUI生成图像",
    "input_schema": {
      "type": "object",
      "properties": {
        "prompt": {
          "type": "string",
          "description": "图像描述"
        }
      },
      "required": ["prompt"]
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "image_url": {
          "type": "string",
          "description": "生成的图像URL"
        },
        "prompt_id": {
          "type": "string",
          "description": "ComfyUI任务ID"
        }
      }
    }
  }'
```

### 1.2 添加节点

#### 1.2.1 创建 Chat 节点

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/nodes
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "type": "CHAT",
  "name": "Test Chat Node",
  "config": {
    "prompt": "公交站里的女孩",
    "title": "Test Chat Node"
  },
  "position": {
    "x": 100,
    "y": 100
  }
}
```

**curl 命令:**

```bash
WORKFLOW_ID="your_workflow_id_here"

curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "CHAT",
    "name": "Test Chat Node",
    "config": {
      "prompt": "公交站里的女孩",
      "title": "Test Chat Node"
    },
    "position": {
      "x": 100,
      "y": 100
    }
  }'
```

#### 1.2.2 创建 Ollama Provider 节点

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/nodes
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "type": "OLLAMA",
  "name": "Real Ollama Provider",
  "config": {
    "title": "Real Ollama Provider",
    "base_url": "http://14.12.0.172:19516",
    "api_key": "ollama",
    "model": "qwen3:8b",
    "timeout": 120
  },
  "position": {
    "x": 300,
    "y": 100
  }
}
```

**curl 命令:**

```bash
curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "OLLAMA",
    "name": "Real Ollama Provider",
    "config": {
      "title": "Real Ollama Provider",
      "base_url": "http://14.12.0.172:19516",
      "api_key": "ollama",
      "model": "qwen3:8b",
      "timeout": 120
    },
    "position": {
      "x": 300,
      "y": 100
    }
  }'
```

#### 1.2.3 创建 Agent 节点

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/nodes
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "type": "AGENT",
  "name": "Math Agent",
  "config": {
    "title": "Math Agent",
    "agent_strategy_provider_name": "ollama",
    "agent_strategy_name": "math_chat",
    "agent_strategy_label": "Noe",
    "prompt_is_expr": true,
    "prompt": "你是一个 Stable Diffusion 绘画专家，我会提供给你画面描述，你将输出ai绘画提示词，只需要提供正向英文提示词，不需要输出Enhanced Notes和Positive Prompt。\n{{ $.outputs.Test Chat Node.outputs.prompt }}",
    "temperature": 0.1
  },
  "position": {
    "x": 500,
    "y": 100
  }
}
```

**curl 命令:**

```bash
curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "AGENT",
    "name": "Math Agent",
    "config": {
      "title": "Math Agent",
      "agent_strategy_provider_name": "ollama",
      "agent_strategy_name": "math_chat",
      "agent_strategy_label": "Noe",
      "prompt_is_expr": true,
      "prompt": "你是一个 Stable Diffusion 绘画专家，我会提供给你画面描述，你将输出ai绘画提示词，只需要提供正向英文提示词，不需要输出Enhanced Notes和Positive Prompt。\n{{ $.outputs.Test Chat Node.outputs.prompt }}",
      "temperature": 0.1
    },
    "position": {
      "x": 500,
      "y": 100
    }
  }'
```

#### 1.2.4 创建 ComfyUI HTTP 节点

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/nodes
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "type": "HTTP",
  "name": "Http Request",
  "config": {
    "title": "Http Request",
    "method": "POST",
    "url": "http://14.12.0.172:9898/prompt",
    "headers": {
      "Content-Type": "application/json"
    },
    "params": {},
    "body_is_expr": true,
    "body": {
      "client_id": "533ef3a3-39c0-4e39-9ced-37d290f371f8",
      "prompt": {
        "9": {
          "inputs": {
            "ckpt_name": "XL\\sd_xl_base_1.0.safetensors",
            "config_name": "Default",
            "vae_name": "sdxl_vae.safetensors",
            "clip_skip": -2,
            "lora_name": "None",
            "lora_model_strength": 1,
            "lora_clip_strength": 1,
            "resolution": "1024 x 1024",
            "empty_latent_width": 512,
            "empty_latent_height": 512,
            "positive": "{{ $.outputs.Math Agent.outputs.content }}",
            "positive_token_normalization": "length+mean",
            "positive_weight_interpretation": "A1111",
            "negative": " text, watermark, nsfw",
            "negative_token_normalization": "length+mean",
            "negative_weight_interpretation": "A1111",
            "batch_size": 1,
            "a1111_prompt_style": false
          },
          "class_type": "easy fullLoader",
          "_meta": {
            "title": "EasyLoader (Full)"
          }
        },
        "10": {
          "inputs": {
            "steps": 20,
            "cfg": 8,
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "denoise": 1,
            "image_output": "Preview",
            "link_id": 0,
            "save_prefix": "ComfyUI",
            "seed": 12345678,
            "pipe": ["9", 0]
          },
          "class_type": "easy fullkSampler",
          "_meta": {
            "title": "EasyKSampler (Full)"
          }
        },
        "11": {
          "inputs": {
            "images": ["10", 1]
          },
          "class_type": "PreviewImage",
          "_meta": {
            "title": "Preview Image"
          }
        }
      }
    },
    "timeout": 30,
    "follow_redirects": true
  },
  "position": {
    "x": 700,
    "y": 100
  }
}
```

**curl 命令:**

```bash
curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "HTTP",
    "name": "Http Request",
    "config": {
      "title": "Http Request",
      "method": "POST",
      "url": "http://14.12.0.172:9898/prompt",
      "headers": {
        "Content-Type": "application/json"
      },
      "params": {},
      "body_is_expr": true,
      "body": {
        "client_id": "533ef3a3-39c0-4e39-9ced-37d290f371f8",
        "prompt": {
          "9": {
            "inputs": {
              "ckpt_name": "XL\\sd_xl_base_1.0.safetensors",
              "config_name": "Default",
              "vae_name": "sdxl_vae.safetensors",
              "clip_skip": -2,
              "lora_name": "None",
              "lora_model_strength": 1,
              "lora_clip_strength": 1,
              "resolution": "1024 x 1024",
              "empty_latent_width": 512,
              "empty_latent_height": 512,
              "positive": "{{ $.outputs.Math Agent.outputs.content }}",
              "positive_token_normalization": "length+mean",
              "positive_weight_interpretation": "A1111",
              "negative": " text, watermark, nsfw",
              "negative_token_normalization": "length+mean",
              "negative_weight_interpretation": "A1111",
              "batch_size": 1,
              "a1111_prompt_style": false
            },
            "class_type": "easy fullLoader",
            "_meta": {
              "title": "EasyLoader (Full)"
            }
          },
          "10": {
            "inputs": {
              "steps": 20,
              "cfg": 8,
              "sampler_name": "dpmpp_2m",
              "scheduler": "karras",
              "denoise": 1,
              "image_output": "Preview",
              "link_id": 0,
              "save_prefix": "ComfyUI",
              "seed": 12345678,
              "pipe": ["9", 0]
            },
            "class_type": "easy fullkSampler",
            "_meta": {
              "title": "EasyKSampler (Full)"
            }
          },
          "11": {
            "inputs": {
              "images": ["10", 1]
            },
            "class_type": "PreviewImage",
            "_meta": {
              "title": "Preview Image"
            }
          }
        }
      },
      "timeout": 30,
      "follow_redirects": true
    },
    "position": {
      "x": 700,
      "y": 100
    }
  }'
```

### 1.3 创建节点连接

#### 1.3.1 连接 Ollama Provider 到 Agent

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/connections
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "source_node_id": "{ollama_node_id}",
  "target_node_id": "{agent_node_id}",
  "source_output": "output",
  "target_input": "input"
}
```

**curl 命令:**

```bash
OLLAMA_NODE_ID="your_ollama_node_id"
AGENT_NODE_ID="your_agent_node_id"

curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "source_node_id": "'${OLLAMA_NODE_ID}'",
    "target_node_id": "'${AGENT_NODE_ID}'",
    "source_output": "output",
    "target_input": "input"
  }'
```

#### 1.3.2 连接 Chat Node 到 Agent

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/connections
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "source_node_id": "{chat_node_id}",
  "target_node_id": "{agent_node_id}",
  "source_output": "output",
  "target_input": "input"
}
```

**curl 命令:**

```bash
CHAT_NODE_ID="your_chat_node_id"

curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "source_node_id": "'${CHAT_NODE_ID}'",
    "target_node_id": "'${AGENT_NODE_ID}'",
    "source_output": "output",
    "target_input": "input"
  }'
```

#### 1.3.3 连接 Agent 到 ComfyUI HTTP Node

**API 请求:**

```http
POST /api/v1/workflows/{workflow_id}/connections
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "source_node_id": "{agent_node_id}",
  "target_node_id": "{http_node_id}",
  "source_output": "output",
  "target_input": "input"
}
```

**curl 命令:**

```bash
HTTP_NODE_ID="your_http_node_id"

curl -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "source_node_id": "'${AGENT_NODE_ID}'",
    "target_node_id": "'${HTTP_NODE_ID}'",
    "source_output": "output",
    "target_input": "input"
  }'
```

## 2. 应用运行时 API 测试

### 2.1 创建应用

**API 请求:**

```http
POST /api/v1/applications/
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "name": "ComfyUI Image Generator",
  "description": "基于ComfyUI的AI图像生成应用",
  "workflow_id": "{workflow_id}",
  "config": {
    "max_concurrent_executions": 5,
    "timeout_seconds": 300
  }
}
```

**curl 命令:**

```bash
curl -X POST "${API_BASE_URL}/api/v1/applications/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "name": "ComfyUI Image Generator",
    "description": "基于ComfyUI的AI图像生成应用",
    "workflow_id": "'${WORKFLOW_ID}'",
    "config": {
      "max_concurrent_executions": 5,
      "timeout_seconds": 300
    }
  }'
```

### 2.2 发布应用

**API 请求:**

```http
PUT /api/v1/applications/{application_id}/publish
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}

{
  "is_published": true
}
```

**curl 命令:**

```bash
APPLICATION_ID="your_application_id"

curl -X PUT "${API_BASE_URL}/api/v1/applications/${APPLICATION_ID}/publish" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "is_published": true
  }'
```

### 2.3 执行应用

**API 请求:**

```http
POST /api/v1/runtime/apps/{application_id}/execute
Content-Type: application/json
Authorization: Bearer {API_KEY}

{
  "inputs": {
    "prompt": "公交站里的女孩"
  }
}
```

**curl 命令:**

```bash
curl -X POST "${API_BASE_URL}/api/v1/runtime/apps/${APPLICATION_ID}/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "inputs": {
      "prompt": "公交站里的女孩"
    }
  }'
```

### 2.4 查询执行状态

**API 请求:**

```http
GET /api/v1/runtime/apps/{application_id}/executions/{execution_id}
Authorization: Bearer {API_KEY}
```

**curl 命令:**

```bash
EXECUTION_ID="your_execution_id"

curl -X GET "${API_BASE_URL}/api/v1/runtime/apps/${APPLICATION_ID}/executions/${EXECUTION_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

## 3. 直接 ComfyUI API 测试

### 3.1 直接调用 ComfyUI

**API 请求:**

```http
POST http://14.12.0.172:9898/prompt
Content-Type: application/json

{
  "client_id": "533ef3a3-39c0-4e39-9ced-37d290f371f8",
  "prompt": {
    "9": {
      "inputs": {
        "ckpt_name": "XL\\sd_xl_base_1.0.safetensors",
        "config_name": "Default",
        "vae_name": "sdxl_vae.safetensors",
        "clip_skip": -2,
        "lora_name": "None",
        "lora_model_strength": 1,
        "lora_clip_strength": 1,
        "resolution": "1024 x 1024",
        "empty_latent_width": 512,
        "empty_latent_height": 512,
        "positive": "a young girl waiting at a bus stop, beautiful detailed eyes, beautiful detailed lips, extremely detailed eyes and face, long eyelashes, casual clothing, urban background, natural lighting, photorealistic, 8k, high quality",
        "positive_token_normalization": "length+mean",
        "positive_weight_interpretation": "A1111",
        "negative": "text, watermark, nsfw",
        "negative_token_normalization": "length+mean",
        "negative_weight_interpretation": "A1111",
        "batch_size": 1,
        "a1111_prompt_style": false
      },
      "class_type": "easy fullLoader",
      "_meta": {
        "title": "EasyLoader (Full)"
      }
    },
    "10": {
      "inputs": {
        "steps": 20,
        "cfg": 8,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "denoise": 1,
        "image_output": "Preview",
        "link_id": 0,
        "save_prefix": "ComfyUI",
        "seed": 12345678,
        "pipe": ["9", 0]
      },
      "class_type": "easy fullkSampler",
      "_meta": {
        "title": "EasyKSampler (Full)"
      }
    },
    "11": {
      "inputs": {
        "images": ["10", 1]
      },
      "class_type": "PreviewImage",
      "_meta": {
        "title": "Preview Image"
      }
    }
  }
}
```

**curl 命令:**

```bash
curl -X POST "http://14.12.0.172:9898/prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "533ef3a3-39c0-4e39-9ced-37d290f371f8",
    "prompt": {
      "9": {
        "inputs": {
          "ckpt_name": "XL\\sd_xl_base_1.0.safetensors",
          "config_name": "Default",
          "vae_name": "sdxl_vae.safetensors",
          "clip_skip": -2,
          "lora_name": "None",
          "lora_model_strength": 1,
          "lora_clip_strength": 1,
          "resolution": "1024 x 1024",
          "empty_latent_width": 512,
          "empty_latent_height": 512,
          "positive": "a young girl waiting at a bus stop, beautiful detailed eyes, beautiful detailed lips, extremely detailed eyes and face, long eyelashes, casual clothing, urban background, natural lighting, photorealistic, 8k, high quality",
          "positive_token_normalization": "length+mean",
          "positive_weight_interpretation": "A1111",
          "negative": "text, watermark, nsfw",
          "negative_token_normalization": "length+mean",
          "negative_weight_interpretation": "A1111",
          "batch_size": 1,
          "a1111_prompt_style": false
        },
        "class_type": "easy fullLoader",
        "_meta": {
          "title": "EasyLoader (Full)"
        }
      },
      "10": {
        "inputs": {
          "steps": 20,
          "cfg": 8,
          "sampler_name": "dpmpp_2m",
          "scheduler": "karras",
          "denoise": 1,
          "image_output": "Preview",
          "link_id": 0,
          "save_prefix": "ComfyUI",
          "seed": 12345678,
          "pipe": ["9", 0]
        },
        "class_type": "easy fullkSampler",
        "_meta": {
          "title": "EasyKSampler (Full)"
        }
      },
      "11": {
        "inputs": {
          "images": ["10", 1]
        },
        "class_type": "PreviewImage",
        "_meta": {
          "title": "Preview Image"
        }
      }
    }
  }'
```

## 4. 测试脚本

### 4.1 完整测试脚本

```bash
#!/bin/bash

# 配置变量
API_BASE_URL="http://localhost:8000"
JWT_TOKEN="your_jwt_token_here"
WORKSPACE_ID="your_workspace_id_here"

echo "=== ComfyUI 工作流 API 测试 ==="

# 1. 创建工作流
echo "1. 创建工作流..."
WORKFLOW_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/workflows/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "name": "ComfyUI Image Generation Workflow",
    "description": "AI图像生成工作流：中文描述 -> 英文提示词 -> ComfyUI生成图像"
  }' \
  --url-query "workspace_id=${WORKSPACE_ID}")

WORKFLOW_ID=$(echo $WORKFLOW_RESPONSE | jq -r '.id')
echo "工作流ID: $WORKFLOW_ID"

# 2. 创建节点
echo "2. 创建节点..."

# Chat Node
CHAT_NODE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "CHAT",
    "name": "Test Chat Node",
    "config": {
      "prompt": "公交站里的女孩",
      "title": "Test Chat Node"
    },
    "position": {"x": 100, "y": 100}
  }')

CHAT_NODE_ID=$(echo $CHAT_NODE_RESPONSE | jq -r '.id')
echo "Chat节点ID: $CHAT_NODE_ID"

# Ollama Node
OLLAMA_NODE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "OLLAMA",
    "name": "Real Ollama Provider",
    "config": {
      "title": "Real Ollama Provider",
      "base_url": "http://14.12.0.172:19516",
      "api_key": "ollama",
      "model": "qwen3:8b",
      "timeout": 120
    },
    "position": {"x": 300, "y": 100}
  }')

OLLAMA_NODE_ID=$(echo $OLLAMA_NODE_RESPONSE | jq -r '.id')
echo "Ollama节点ID: $OLLAMA_NODE_ID"

# Agent Node
AGENT_NODE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "AGENT",
    "name": "Math Agent",
    "config": {
      "title": "Math Agent",
      "agent_strategy_provider_name": "ollama",
      "agent_strategy_name": "math_chat",
      "agent_strategy_label": "Noe",
      "prompt_is_expr": true,
      "prompt": "你是一个 Stable Diffusion 绘画专家，我会提供给你画面描述，你将输出ai绘画提示词，只需要提供正向英文提示词，不需要输出Enhanced Notes和Positive Prompt。\n{{ $.outputs.Test Chat Node.outputs.prompt }}",
      "temperature": 0.1
    },
    "position": {"x": 500, "y": 100}
  }')

AGENT_NODE_ID=$(echo $AGENT_NODE_RESPONSE | jq -r '.id')
echo "Agent节点ID: $AGENT_NODE_ID"

# HTTP Node (ComfyUI)
HTTP_NODE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/nodes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "type": "HTTP",
    "name": "Http Request",
    "config": {
      "title": "Http Request",
      "method": "POST",
      "url": "http://14.12.0.172:9898/prompt",
      "headers": {"Content-Type": "application/json"},
      "body_is_expr": true,
      "timeout": 30,
      "follow_redirects": true
    },
    "position": {"x": 700, "y": 100}
  }')

HTTP_NODE_ID=$(echo $HTTP_NODE_RESPONSE | jq -r '.id')
echo "HTTP节点ID: $HTTP_NODE_ID"

# 3. 创建连接
echo "3. 创建节点连接..."

# 连接 Ollama -> Agent
curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "source_node_id": "'${OLLAMA_NODE_ID}'",
    "target_node_id": "'${AGENT_NODE_ID}'",
    "source_output": "output",
    "target_input": "input"
  }' > /dev/null

# 连接 Chat -> Agent
curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "source_node_id": "'${CHAT_NODE_ID}'",
    "target_node_id": "'${AGENT_NODE_ID}'",
    "source_output": "output",
    "target_input": "input"
  }' > /dev/null

# 连接 Agent -> HTTP
curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "source_node_id": "'${AGENT_NODE_ID}'",
    "target_node_id": "'${HTTP_NODE_ID}'",
    "source_output": "output",
    "target_input": "input"
  }' > /dev/null

echo "连接创建完成"

# 4. 验证工作流
echo "4. 验证工作流..."
VALIDATION_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/v1/workflows/${WORKFLOW_ID}/validate" \
  -H "Authorization: Bearer ${JWT_TOKEN}")

IS_VALID=$(echo $VALIDATION_RESPONSE | jq -r '.is_valid')
echo "工作流验证结果: $IS_VALID"

if [ "$IS_VALID" = "true" ]; then
  echo "✅ 工作流创建成功！"
  echo "工作流ID: $WORKFLOW_ID"
else
  echo "❌ 工作流验证失败"
  echo $VALIDATION_RESPONSE | jq '.errors'
fi

echo "=== 测试完成 ==="
```

### 4.2 Python 测试脚本

```python
#!/usr/bin/env python3
"""
ComfyUI 工作流 API 测试脚本
"""

import requests
import json
import time
from typing import Dict, Any

class ComfyUIWorkflowTester:
    def __init__(self, api_base_url: str, jwt_token: str, workspace_id: str):
        self.api_base_url = api_base_url
        self.jwt_token = jwt_token
        self.workspace_id = workspace_id
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {jwt_token}'
        }
    
    def create_workflow(self) -> str:
        """创建工作流"""
        url = f"{self.api_base_url}/api/v1/workflows/"
        data = {
            "name": "ComfyUI Image Generation Workflow",
            "description": "AI图像生成工作流：中文描述 -> 英文提示词 -> ComfyUI生成图像",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图像描述"
                    }
                },
                "required": ["prompt"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "生成的图像URL"
                    },
                    "prompt_id": {
                        "type": "string",
                        "description": "ComfyUI任务ID"
                    }
                }
            }
        }
        
        params = {"workspace_id": self.workspace_id}
        response = requests.post(url, json=data, headers=self.headers, params=params)
        response.raise_for_status()
        
        workflow_data = response.json()
        return workflow_data['id']
    
    def create_node(self, workflow_id: str, node_config: Dict[str, Any]) -> str:
        """创建节点"""
        url = f"{self.api_base_url}/api/v1/workflows/{workflow_id}/nodes"
        response = requests.post(url, json=node_config, headers=self.headers)
        response.raise_for_status()
        
        node_data = response.json()
        return node_data['id']
    
    def create_connection(self, workflow_id: str, connection_config: Dict[str, Any]) -> str:
        """创建连接"""
        url = f"{self.api_base_url}/api/v1/workflows/{workflow_id}/connections"
        response = requests.post(url, json=connection_config, headers=self.headers)
        response.raise_for_status()
        
        connection_data = response.json()
        return connection_data['id']
    
    def validate_workflow(self, workflow_id: str) -> bool:
        """验证工作流"""
        url = f"{self.api_base_url}/api/v1/workflows/{workflow_id}/validate"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        
        validation_data = response.json()
        return validation_data['is_valid']
    
    def run_test(self):
        """运行完整测试"""
        print("=== ComfyUI 工作流 API 测试 ===")
        
        try:
            # 1. 创建工作流
            print("1. 创建工作流...")
            workflow_id = self.create_workflow()
            print(f"工作流ID: {workflow_id}")
            
            # 2. 创建节点
            print("2. 创建节点...")
            
            # Chat Node
            chat_node_config = {
                "type": "CHAT",
                "name": "Test Chat Node",
                "config": {
                    "prompt": "公交站里的女孩",
                    "title": "Test Chat Node"
                },
                "position": {"x": 100, "y": 100}
            }
            chat_node_id = self.create_node(workflow_id, chat_node_config)
            print(f"Chat节点ID: {chat_node_id}")
            
            # Ollama Node
            ollama_node_config = {
                "type": "OLLAMA",
                "name": "Real Ollama Provider",
                "config": {
                    "title": "Real Ollama Provider",
                    "base_url": "http://14.12.0.172:19516",
                    "api_key": "ollama",
                    "model": "qwen3:8b",
                    "timeout": 120
                },
                "position": {"x": 300, "y": 100}
            }
            ollama_node_id = self.create_node(workflow_id, ollama_node_config)
            print(f"Ollama节点ID: {ollama_node_id}")
            
            # Agent Node
            agent_node_config = {
                "type": "AGENT",
                "name": "Math Agent",
                "config": {
                    "title": "Math Agent",
                    "agent_strategy_provider_name": "ollama",
                    "agent_strategy_name": "math_chat",
                    "agent_strategy_label": "Noe",
                    "prompt_is_expr": True,
                    "prompt": "你是一个 Stable Diffusion 绘画专家，我会提供给你画面描述，你将输出ai绘画提示词，只需要提供正向英文提示词，不需要输出Enhanced Notes和Positive Prompt。\n{{ $.outputs.Test Chat Node.outputs.prompt }}",
                    "temperature": 0.1
                },
                "position": {"x": 500, "y": 100}
            }
            agent_node_id = self.create_node(workflow_id, agent_node_config)
            print(f"Agent节点ID: {agent_node_id}")
            
            # HTTP Node
            http_node_config = {
                "type": "HTTP",
                "name": "Http Request",
                "config": {
                    "title": "Http Request",
                    "method": "POST",
                    "url": "http://14.12.0.172:9898/prompt",
                    "headers": {"Content-Type": "application/json"},
                    "body_is_expr": True,
                    "timeout": 30,
                    "follow_redirects": True
                },
                "position": {"x": 700, "y": 100}
            }
            http_node_id = self.create_node(workflow_id, http_node_config)
            print(f"HTTP节点ID: {http_node_id}")
            
            # 3. 创建连接
            print("3. 创建节点连接...")
            
            # Ollama -> Agent
            conn1_config = {
                "source_node_id": ollama_node_id,
                "target_node_id": agent_node_id,
                "source_output": "output",
                "target_input": "input"
            }
            self.create_connection(workflow_id, conn1_config)
            
            # Chat -> Agent
            conn2_config = {
                "source_node_id": chat_node_id,
                "target_node_id": agent_node_id,
                "source_output": "output",
                "target_input": "input"
            }
            self.create_connection(workflow_id, conn2_config)
            
            # Agent -> HTTP
            conn3_config = {
                "source_node_id": agent_node_id,
                "target_node_id": http_node_id,
                "source_output": "output",
                "target_input": "input"
            }
            self.create_connection(workflow_id, conn3_config)
            
            print("连接创建完成")
            
            # 4. 验证工作流
            print("4. 验证工作流...")
            is_valid = self.validate_workflow(workflow_id)
            
            if is_valid:
                print("✅ 工作流创建成功！")
                print(f"工作流ID: {workflow_id}")
            else:
                print("❌ 工作流验证失败")
            
            print("=== 测试完成 ===")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API请求失败: {e}")
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    # 配置参数
    API_BASE_URL = "http://localhost:8000"
    JWT_TOKEN = "your_jwt_token_here"
    WORKSPACE_ID = "your_workspace_id_here"
    
    # 运行测试
    tester = ComfyUIWorkflowTester(API_BASE_URL, JWT_TOKEN, WORKSPACE_ID)
    tester.run_test()
```

## 5. 预期响应示例

### 5.1 工作流创建响应

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "ComfyUI Image Generation Workflow",
  "description": "AI图像生成工作流：中文描述 -> 英文提示词 -> ComfyUI生成图像",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440001",
  "input_schema": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "图像描述"
      }
    },
    "required": ["prompt"]
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "image_url": {
        "type": "string",
        "description": "生成的图像URL"
      },
      "prompt_id": {
        "type": "string",
        "description": "ComfyUI任务ID"
      }
    }
  },
  "created_at": "2025-01-02T10:00:00Z",
  "updated_at": "2025-01-02T10:00:00Z",
  "created_by": "550e8400-e29b-41d4-a716-446655440002",
  "is_deleted": false
}
```

### 5.2 ComfyUI 响应示例

```json
{
  "prompt_id": "12345678-1234-1234-1234-123456789012",
  "number": 1,
  "node_errors": {}
}
```

### 5.3 应用执行响应示例

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440003",
  "outputs": {
    "image_url": "http://14.12.0.172:9898/view?filename=ComfyUI_00001_.png",
    "prompt_id": "12345678-1234-1234-1234-123456789012"
  },
  "status": "COMPLETED",
  "started_at": "2025-01-02T10:00:00Z",
  "completed_at": "2025-01-02T10:02:30Z",
  "duration_ms": 150000,
  "error": null
}
```

## 6. 故障排除

### 6.1 常见错误

1. **401 Unauthorized**: 检查JWT token或API key是否正确
2. **404 Not Found**: 检查workflow_id、node_id等ID是否存在
3. **422 Unprocessable Entity**: 检查请求数据格式是否正确
4. **500 Internal Server Error**: 检查服务器日志，可能是配置问题

### 6.2 调试建议

1. 使用 `--verbose` 参数查看详细的curl输出
2. 检查服务器日志文件
3. 验证Ollama和ComfyUI服务是否正常运行
4. 确认网络连接和防火墙设置

---

**注意**: 请根据实际环境修改配置参数，包括服务器地址、端口、认证信息等。
