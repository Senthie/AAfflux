# 软删除字段数据库迁移指南

## 📊 检查结果

### ✅ 已有软删除字段的表（12个）
```
- applications
- bpm_process_definitions
- datasets
- llm_providers
- organizations
- plugins
- prompt_templates
- subscriptions
- teams
- users
- workflows
- workspaces
```

### ❌ 需要添加软删除字段的表（10个）

#### 核心业务表
```
1. conversations          - 对话表
2. messages              - 消息表
3. end_users             - 终端用户表
4. documents             - 文档表
5. document_segments     - 文档段落表
6. file_references       - 文件引用表
7. nodes                 - 工作流节点表
8. installed_plugins     - 已安装插件表
9. bpm_form_definitions  - 表单定义表
10. prompt_template_versions - 提示词模板版本表
```

### ⚠️ 不需要软删除的表（18个）
```
临时数据：
- refresh_tokens
- password_resets
- api_keys
- team_invitations

关联关系：
- team_members
- dataset_application_joins
- connections

执行记录：
- execution_records
- node_execution_results
- bpm_process_instances
- bpm_tasks
- bpm_approvals
- bpm_form_data

系统数据：
- audit_logs
- usage_records
- message_annotations
- message_feedbacks

系统表：
- alembic_version
```

---

## 🚀 执行迁移

### 1. 检查当前数据库状态
```bash
cd api
python check_db_soft_delete.py
```

### 2. 执行迁移
```bash
# 查看待执行的迁移
alembic current
alembic history

# 执行迁移
alembic upgrade head

# 或指定版本
alembic upgrade add_soft_delete_001
```

### 3. 验证迁移结果
```bash
# 再次检查数据库
python check_db_soft_delete.py
```

### 4. 回滚（如需要）
```bash
alembic downgrade -1
```

---

## 📝 迁移内容

### 添加的字段
每个表将添加以下字段：
```sql
deleted_at TIMESTAMP WITH TIME ZONE NULL
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
```

### 添加的索引
为提高查询性能，每个表将添加：
```sql
CREATE INDEX ix_{table_name}_deleted_at ON {table_name}(deleted_at);
CREATE INDEX ix_{table_name}_is_deleted ON {table_name}(is_deleted);
```

---

## ⚠️ 注意事项

1. **备份数据库**
   ```bash
   pg_dump -U postgres -d lowcode_platform > backup_before_soft_delete.sql
   ```

2. **停止应用服务**
   - 迁移期间建议停止应用服务
   - 避免数据不一致

3. **测试环境先行**
   - 先在测试环境执行
   - 验证无误后再在生产环境执行

4. **监控性能**
   - 迁移后监控查询性能
   - 确保索引生效

---

## 🔍 验证清单

- [ ] 数据库已备份
- [ ] 应用服务已停止
- [ ] 迁移脚本已审查
- [ ] 测试环境已验证
- [ ] 执行 `alembic upgrade head`
- [ ] 运行 `check_db_soft_delete.py` 验证
- [ ] 检查索引是否创建成功
- [ ] 应用服务正常启动
- [ ] 软删除功能测试通过

---

## 📊 预期结果

迁移完成后：
- ✅ 10个核心业务表将拥有软删除字段
- ✅ 20个索引将被创建（每表2个）
- ✅ 所有需要软删除的表覆盖率达到 100%
- ✅ 不需要软删除的表保持原样
