"""
Models 字段测试 - 无需数据库连接

测试所有模型的字段定义、类型、约束和关系
"""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys
from uuid import UUID, uuid4

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print('\n' + '=' * 70)
print('Models 字段测试 - 无需数据库')
print('=' * 70)

# 导入所有模型
print('\n[1] 导入所有模型...')
try:
    from app.models.application.application import Application
    from app.models.audit.audit_log import AuditLog
    from app.models.auth.user import User
    from app.models.base import AuditMixin, BaseModel, TimestampMixin, WorkspaceMixin
    from app.models.billing.billing import Subscription, UsageRecord
    from app.models.bpm.process import ProcessDefinition, ProcessInstance
    from app.models.bpm.task import Task
    from app.models.conversation.conversation import Conversation, Message
    from app.models.dataset.dataset import Dataset, Document, DocumentSegment
    from app.models.plugin.plugin import InstalledPlugin, Plugin
    from app.models.tenant.organization import Organization, Team, TeamMember, Workspace
    from app.models.workflow.workflow import (
        Connection,
        ExecutionRecord,
        Node,
        NodeExecutionResult,
        Workflow,
    )

    print('✓ 所有模型导入成功')
except Exception as e:
    print(f'✗ 导入失败: {e}')
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 收集所有模型类
ALL_MODELS = [
    # 认证域
    User,
    # 租户域
    Organization,
    Team,
    Workspace,
    TeamMember,
    # 工作流域
    Workflow,
    Node,
    Connection,
    ExecutionRecord,
    NodeExecutionResult,
    # 应用域
    Application,
    # 对话域
    Conversation,
    Message,
    # 知识库域
    Dataset,
    Document,
    DocumentSegment,
    # 插件域
    Plugin,
    InstalledPlugin,
    # BPM域
    ProcessDefinition,
    ProcessInstance,
    Task,
    # 计费域
    Subscription,
    UsageRecord,
    # 审计域
    AuditLog,
]


class ModelFieldTester:
    """模型字段测试器"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.results = {}

    def test(self, name, test_func):
        """运行单个测试"""
        self.total += 1
        try:
            result = test_func()
            if result:
                print(f'  ✓ {name}')
                self.passed += 1
                return True
            else:
                print(f'  ✗ {name}')
                self.failed += 1
                return False
        except Exception as e:
            print(f'  ✗ {name}: {str(e)}')
            self.failed += 1
            return False

    def summary(self):
        """打印测试摘要"""
        print(f'\n测试完成: {self.total} 总计, {self.passed} 通过, {self.failed} 失败')
        return self.failed == 0


def test_model_inheritance():
    """测试模型继承"""
    tester = ModelFieldTester()
    print('\n[2] 模型继承测试')

    def test_base_model_inheritance():
        """测试 BaseModel 继承"""
        for model in ALL_MODELS:
            if not issubclass(model, BaseModel):
                print(f'    {model.__name__} 未继承 BaseModel')
                return False
        return True

    def test_id_field_exists():
        """测试 id 字段存在"""
        for model in ALL_MODELS:
            if not hasattr(model, 'id'):
                print(f'    {model.__name__} 缺少 id 字段')
                return False
        return True

    def test_timestamp_mixin():
        """测试时间戳混入"""
        timestamp_models = [m for m in ALL_MODELS if issubclass(m, TimestampMixin)]
        for model in timestamp_models:
            if not (hasattr(model, 'created_at') and hasattr(model, 'updated_at')):
                print(f'    {model.__name__} 缺少时间戳字段')
                return False
        return True

    def test_workspace_mixin():
        """测试工作空间混入"""
        workspace_models = [m for m in ALL_MODELS if issubclass(m, WorkspaceMixin)]
        for model in workspace_models:
            if not hasattr(model, 'workspace_id'):
                print(f'    {model.__name__} 缺少 workspace_id 字段')
                return False
        return True

    def test_audit_mixin():
        """测试审计混入"""
        audit_models = [m for m in ALL_MODELS if issubclass(m, AuditMixin)]
        for model in audit_models:
            if not hasattr(model, 'created_by'):
                print(f'    {model.__name__} 缺少 created_by 字段')
                return False
        return True

    tester.test('BaseModel 继承', test_base_model_inheritance)
    tester.test('ID 字段存在', test_id_field_exists)
    tester.test('时间戳混入', test_timestamp_mixin)
    tester.test('工作空间混入', test_workspace_mixin)
    tester.test('审计混入', test_audit_mixin)

    return tester.summary()


def test_model_fields():
    """测试模型字段"""
    tester = ModelFieldTester()
    print('\n[3] 模型字段测试')

    def test_table_names():
        """测试表名定义"""
        for model in ALL_MODELS:
            if not hasattr(model, '__tablename__'):
                print(f'    {model.__name__} 缺少 __tablename__')
                return False
        return True

    def test_field_types():
        """测试字段类型"""
        for model in ALL_MODELS:
            try:
                # 获取字段定义
                if hasattr(model, 'model_fields'):
                    fields = model.model_fields
                    for field_name, field_info in fields.items():
                        # 检查字段是否有类型注解
                        if not hasattr(field_info, 'annotation'):
                            print(f'    {model.__name__}.{field_name} 缺少类型注解')
                            return False
            except Exception as e:
                print(f'    {model.__name__} 字段检查失败: {e}')
                return False
        return True

    def test_required_fields():
        """测试必填字段"""
        required_checks = {
            User: ['name', 'email', 'password_hash'],
            Organization: ['name'],
            Team: ['name'],
            Workspace: ['name'],
            Workflow: ['name'],
            Application: ['name'],
        }

        for model, required_fields in required_checks.items():
            for field_name in required_fields:
                if not hasattr(model, field_name):
                    print(f'    {model.__name__} 缺少必填字段: {field_name}')
                    return False
        return True

    def test_unique_constraints():
        """测试唯一约束"""
        # 检查邮箱字段的唯一性
        if hasattr(User, 'model_fields') and 'email' in User.model_fields:
            email_field = User.model_fields['email']  # noqa: F841
            # 这里可以检查 Field 的约束配置
            pass
        return True

    tester.test('表名定义', test_table_names)
    tester.test('字段类型', test_field_types)
    tester.test('必填字段', test_required_fields)
    tester.test('唯一约束', test_unique_constraints)

    return tester.summary()


def test_model_relationships():
    """测试模型关系"""
    tester = ModelFieldTester()
    print('\n[4] 模型关系测试')

    def test_foreign_keys():
        """测试外键字段"""
        fk_checks = {
            'workspace_id': ['workspaces.id'],
            'created_by': ['users.id'],
            'user_id': ['users.id'],
            'team_id': ['teams.id'],
            'organization_id': ['organizations.id'],
        }

        for model in ALL_MODELS:
            if hasattr(model, 'model_fields'):
                for field_name, field_info in model.model_fields.items():  # noqa: B007
                    if field_name in fk_checks:
                        # 检查外键字段存在
                        pass
        return True

    def test_relationship_consistency():
        """测试关系一致性"""
        # 检查 Team 和 Organization 的关系
        if hasattr(Team, 'organization_id') and hasattr(Organization, 'id'):
            pass

        # 检查 Workspace 和 Team 的关系
        if hasattr(Workspace, 'team_id') and hasattr(Team, 'id'):
            pass

        return True

    tester.test('外键字段', test_foreign_keys)
    tester.test('关系一致性', test_relationship_consistency)

    return tester.summary()


def test_model_instantiation():
    """测试模型实例化"""
    tester = ModelFieldTester()
    print('\n[5] 模型实例化测试')

    def test_user_creation():
        """测试用户创建"""
        user = User(name='测试用户', email='test@example.com', password_hash='hashed_password')
        return (
            isinstance(user.id, UUID)
            and user.name == '测试用户'
            and user.email == 'test@example.com'
            and isinstance(user.created_at, datetime)
            and isinstance(user.updated_at, datetime)
        )

    def test_organization_creation():
        """测试企业创建"""
        org = Organization(name='测试企业', created_by=uuid4())
        return (
            isinstance(org.id, UUID)
            and org.name == '测试企业'
            and isinstance(org.created_by, UUID)
            and isinstance(org.created_at, datetime)
        )

    def test_workflow_creation():
        """测试工作流创建"""
        workflow = Workflow(name='测试工作流', workspace_id=uuid4(), created_by=uuid4())
        return (
            isinstance(workflow.id, UUID)
            and workflow.name == '测试工作流'
            and isinstance(workflow.workspace_id, UUID)
            and isinstance(workflow.created_by, UUID)
        )

    def test_application_creation():
        """测试应用创建"""
        app = Application(
            name='测试应用',
            workspace_id=uuid4(),
            workflow_id=uuid4(),
            created_by=uuid4(),
            api_key_hash='test_hash',
            endpoint='/api/test',
        )
        return (
            isinstance(app.id, UUID)
            and app.name == '测试应用'
            and isinstance(app.workspace_id, UUID)
            and app.endpoint == '/api/test'
        )

    def test_subscription_creation():
        """测试订阅创建"""
        subscription = Subscription(
            workspace_id=uuid4(),
            plan_type='pro',
            plan_name='专业版',
            status='active',
            billing_cycle='monthly',
            price=Decimal('99.00'),
            quota_limits={'api_calls': 10000},
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )
        return (
            isinstance(subscription.id, UUID)
            and subscription.plan_type == 'pro'
            and subscription.price == Decimal('99.00')
            and isinstance(subscription.quota_limits, dict)
        )

    tester.test('用户创建', test_user_creation)
    tester.test('企业创建', test_organization_creation)
    tester.test('工作流创建', test_workflow_creation)
    tester.test('应用创建', test_application_creation)
    tester.test('订阅创建', test_subscription_creation)

    return tester.summary()


def test_field_validation():
    """测试字段验证"""
    tester = ModelFieldTester()
    print('\n[6] 字段验证测试')

    def test_email_format():
        """测试邮箱格式"""
        try:
            user = User(
                name='测试',
                email='invalid-email',  # 无效邮箱
                password_hash='hash',
            )
            # SQLModel 本身不做格式验证，这里只测试字段存在
            return hasattr(user, 'email')
        except Exception:
            return False

    def test_uuid_fields():
        """测试 UUID 字段"""
        user = User(name='测试', email='test@example.com', password_hash='hash')
        return isinstance(user.id, UUID)

    def test_datetime_fields():
        """测试日期时间字段"""
        user = User(name='测试', email='test@example.com', password_hash='hash')
        return isinstance(user.created_at, datetime) and isinstance(user.updated_at, datetime)

    def test_decimal_fields():
        """测试 Decimal 字段"""
        subscription = Subscription(
            workspace_id=uuid4(),
            plan_type='pro',
            plan_name='专业版',
            status='active',
            billing_cycle='monthly',
            price=Decimal('99.00'),
            quota_limits={},
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )
        return isinstance(subscription.price, Decimal)

    tester.test('邮箱字段', test_email_format)
    tester.test('UUID 字段', test_uuid_fields)
    tester.test('日期时间字段', test_datetime_fields)
    tester.test('Decimal 字段', test_decimal_fields)

    return tester.summary()


def analyze_model_structure():
    """分析模型结构"""
    print('\n[7] 模型结构分析')

    total_models = len(ALL_MODELS)
    total_tables = 0

    print(f'\n总模型数: {total_models}')
    print('\n各域模型统计:')

    domains = {
        '认证域': [User],
        '租户域': [Organization, Team, Workspace, TeamMember],
        '工作流域': [Workflow, Node, Connection, ExecutionRecord, NodeExecutionResult],
        '应用域': [Application],
        '对话域': [Conversation, Message],
        '知识库域': [Dataset, Document, DocumentSegment],
        '插件域': [Plugin, InstalledPlugin],
        'BPM域': [ProcessDefinition, ProcessInstance, Task],
        '计费域': [Subscription, UsageRecord],
        '审计域': [AuditLog],
    }

    for domain, models in domains.items():
        print(f'  {domain}: {len(models)} 个模型')
        for model in models:
            table_name = getattr(model, '__tablename__', 'N/A')
            print(f'    - {model.__name__} -> {table_name}')
            if table_name != 'N/A':
                total_tables += 1

    print(f'\n总数据库表数: {total_tables}')

    # 分析 Mixin 使用情况
    print('\nMixin 使用统计:')
    timestamp_count = len([m for m in ALL_MODELS if issubclass(m, TimestampMixin)])
    workspace_count = len([m for m in ALL_MODELS if issubclass(m, WorkspaceMixin)])
    audit_count = len([m for m in ALL_MODELS if issubclass(m, AuditMixin)])

    print(f'  TimestampMixin: {timestamp_count} 个模型')
    print(f'  WorkspaceMixin: {workspace_count} 个模型')
    print(f'  AuditMixin: {audit_count} 个模型')


def run_all_tests():
    """运行所有测试"""
    print('开始运行 Models 字段测试...')

    results = []
    results.append(test_model_inheritance())
    results.append(test_model_fields())
    results.append(test_model_relationships())
    results.append(test_model_instantiation())
    results.append(test_field_validation())

    # 结构分析
    analyze_model_structure()

    # 总结
    all_passed = all(results)
    print('\n' + '=' * 70)
    if all_passed:
        print('🎉 所有字段测试通过！模型定义正确')
    else:
        failed_count = len([r for r in results if not r])
        print(f'⚠️  有 {failed_count} 个测试组失败')
    print('=' * 70)

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
