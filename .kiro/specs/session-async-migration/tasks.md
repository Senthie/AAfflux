# Session异步迁移实施计划

- [ ] 1. 迁移BPM服务层
  - 将BPMTaskService、BPMProcessService、BPMApprovalService从同步Session迁移到AsyncSession
  - 更新所有数据库操作方法为异步方法
  - 修复导入语句和类型注解
  - _需求: 2.1, 2.2, 2.3, 2.5_

- [x] 1.1 迁移BPMTaskService到AsyncSession


  - 更新构造函数参数类型为AsyncSession
  - 将所有数据库操作方法改为async def
  - 更新session.execute()调用为await session.execute()
  - _需求: 2.1_

- [ ]* 1.2 为BPMTaskService编写属性测试
  - **属性2: BPM服务异步性**
  - **验证需求: 2.1, 2.2, 2.3, 2.4, 2.5**



- [ ] 1.3 迁移BPMProcessService到AsyncSession
  - 更新构造函数参数类型为AsyncSession
  - 将所有数据库操作方法改为async def


  - 更新ProcessExecutor的使用方式
  - _需求: 2.2_

- [ ] 1.4 迁移BPMApprovalService到AsyncSession
  - 更新构造函数参数类型为AsyncSession
  - 将所有数据库操作方法改为async def
  - 更新session调用为异步方式
  - _需求: 2.3_

- [x] 2. 迁移BPM引擎组件


  - 将TaskDispatcher和ProcessExecutor迁移到AsyncSession
  - 更新引擎组件的数据库操作为异步方式
  - 确保引擎组件接收AsyncSession参数
  - _需求: 2.4_



- [ ] 2.1 迁移TaskDispatcher到AsyncSession
  - 更新构造函数参数类型为AsyncSession
  - 将assign_task、claim_task、get_user_tasks方法改为async def
  - 更新session.get()为异步查询方式
  - 更新session.commit()为await session.commit()
  - _需求: 2.4_

- [ ] 2.2 迁移ProcessExecutor到AsyncSession
  - 更新构造函数参数类型为AsyncSession
  - 将所有流程执行方法改为async def


  - 更新数据库操作为异步方式
  - _需求: 2.4_

- [ ] 3. 迁移LLM提供商服务
  - 将LLMProviderService从同步Session迁移到AsyncSession
  - 更新所有CRUD操作为异步方法
  - 修复导入语句和类型注解
  - _需求: 3.1, 3.2, 3.3, 3.4_

- [ ] 3.1 迁移LLMProviderService到AsyncSession
  - 更新构造函数参数类型为AsyncSession
  - 将create_provider、get_provider、update_provider、delete_provider方法改为async def
  - 更新list_providers查询方法为异步方式
  - 更新所有session操作为await调用
  - _需求: 3.1, 3.2, 3.3_



- [ ]* 3.2 为LLMProviderService编写属性测试
  - **属性3: LLM服务异步性**
  - **验证需求: 3.1, 3.2, 3.3, 3.4**

- [ ] 4. 迁移权限检查服务
  - 将PermissionChecker从同步Session迁移到AsyncSession
  - 更新权限验证方法为异步方法
  - 修复导入语句和类型注解
  - _需求: 4.1, 4.2, 4.3, 4.4_

- [ ] 4.1 迁移PermissionChecker到AsyncSession
  - 更新构造函数参数类型为AsyncSession
  - 将check_permission、check_user_permission、check_team_permission方法改为async def
  - 更新用户和团队查询为异步方式


  - 更新所有数据库操作为await调用
  - _需求: 4.1, 4.2, 4.3_

- [ ]* 4.2 为PermissionChecker编写属性测试
  - **属性4: 权限服务异步性**


  - **验证需求: 4.1, 4.2, 4.3, 4.4**

- [ ] 5. 更新API路由和依赖调用
  - 更新所有API端点对迁移服务的调用方式
  - 确保所有服务调用使用await关键字
  - 验证依赖注入正确提供AsyncSession
  - _需求: 5.1, 5.4_

- [ ] 5.1 更新BPM相关API路由
  - 更新bpm_tasks.py中对BPMTaskService的调用
  - 更新bpm_processes.py中对BPMProcessService的调用
  - 更新bpm_approvals.py中对BPMApprovalService的调用
  - 确保所有服务方法调用使用await
  - _需求: 5.1_

- [ ] 5.2 更新应用相关API路由
  - 检查applications.py中对LLMProviderService的调用
  - 确保权限检查调用使用await
  - 验证依赖注入的正确性
  - _需求: 5.1, 5.4_

- [ ] 6. 更新测试文件
  - 将所有相关测试文件迁移到异步测试方法
  - 更新测试装饰器和session使用方式
  - 确保测试的异步一致性
  - _需求: 5.3_

- [ ] 6.1 更新BPM服务测试文件
  - 为BPM服务测试添加@pytest.mark.asyncio装饰器
  - 更新测试方法为async def
  - 使用async_session fixture
  - 更新所有服务方法调用为await调用
  - _需求: 5.3_



- [ ] 6.2 更新LLM和权限服务测试文件
  - 为LLM和权限服务测试添加异步装饰器
  - 更新测试方法签名和调用方式
  - 确保测试数据库会话的异步使用
  - _需求: 5.3_

- [x]* 6.3 编写系统集成异步一致性属性测试



  - **属性5: 系统集成异步一致性**
  - **验证需求: 5.1, 5.2, 5.3, 5.4, 5.5**

- [ ] 7. 验证和清理
  - 运行所有测试确保迁移成功
  - 检查代码中是否还有同步Session的使用
  - 清理未使用的导入和代码
  - _需求: 1.1, 1.3_

- [ ] 7.1 运行静态代码分析
  - 使用grep搜索项目中剩余的同步Session使用
  - 验证所有服务文件都正确导入AsyncSession
  - 检查所有数据库操作都使用await
  - _需求: 1.1, 1.3, 1.5_

- [ ]* 7.2 编写服务异步一致性属性测试
  - **属性1: 服务异步一致性**
  - **验证需求: 1.1, 1.2, 1.3, 1.4, 1.5**

- [ ] 8. 最终集成测试
  - 确保所有测试通过，询问用户是否有问题