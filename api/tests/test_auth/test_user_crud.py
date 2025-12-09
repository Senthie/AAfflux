"""用户 CRUD 测试"""

import pytest
from uuid import uuid4
from sqlalchemy import select
from app.models.auth.user import User


class TestUserCRUD:
    """用户 CRUD 操作测试"""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """测试创建用户"""
        user = User(
            id=uuid4(),
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password_123",
        )
        
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.is_deleted is False

    @pytest.mark.asyncio
    async def test_read_user(self, test_session):
        """测试读取用户"""
        # 创建用户
        user = User(
            id=uuid4(),
            name="Read User",
            email="read@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user)
        await test_session.commit()
        user_id = user.id
        
        # 读取用户
        result = await test_session.execute(
            select(User).where(User.id == user_id)
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.id == user_id
        assert found_user.name == "Read User"
        assert found_user.email == "read@example.com"

    @pytest.mark.asyncio
    async def test_read_user_by_email(self, test_session):
        """测试通过邮箱读取用户"""
        user = User(
            id=uuid4(),
            name="Email User",
            email="email@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user)
        await test_session.commit()
        
        # 通过邮箱查询
        result = await test_session.execute(
            select(User).where(User.email == "email@example.com")
        )
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.name == "Email User"

    @pytest.mark.asyncio
    async def test_update_user(self, test_session):
        """测试更新用户"""
        user = User(
            id=uuid4(),
            name="Original Name",
            email="update@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user)
        await test_session.commit()
        
        # 更新用户
        user.name = "Updated Name"
        user.email = "updated@example.com"
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.name == "Updated Name"
        assert user.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_soft_delete_user(self, test_session):
        """测试软删除用户"""
        user = User(
            id=uuid4(),
            name="Delete User",
            email="delete@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user)
        await test_session.commit()
        user_id = user.id
        
        # 软删除
        user.soft_delete()
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.is_deleted is True
        assert user.deleted_at is not None
        
        # 验证软删除后仍可查询
        result = await test_session.execute(
            select(User).where(User.id == user_id)
        )
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is not None
        assert deleted_user.is_deleted is True

    @pytest.mark.asyncio
    async def test_restore_user(self, test_session):
        """测试恢复软删除的用户"""
        user = User(
            id=uuid4(),
            name="Restore User",
            email="restore@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user)
        await test_session.commit()
        
        # 软删除
        user.soft_delete()
        await test_session.commit()
        assert user.is_deleted is True
        
        # 恢复
        user.restore()
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.is_deleted is False
        assert user.deleted_at is None

    @pytest.mark.asyncio
    async def test_list_users(self, test_session):
        """测试列表查询用户"""
        # 创建多个用户
        users = [
            User(
                id=uuid4(),
                name=f"User {i}",
                email=f"user{i}@example.com",
                password_hash="hashed_password",
            )
            for i in range(5)
        ]
        
        for user in users:
            test_session.add(user)
        await test_session.commit()
        
        # 查询所有用户
        result = await test_session.execute(select(User))
        all_users = result.scalars().all()
        
        assert len(all_users) >= 5

    @pytest.mark.asyncio
    async def test_list_active_users_only(self, test_session):
        """测试只查询未删除的用户"""
        # 创建用户
        active_user = User(
            id=uuid4(),
            name="Active User",
            email="active@example.com",
            password_hash="hashed_password",
        )
        deleted_user = User(
            id=uuid4(),
            name="Deleted User",
            email="deleted@example.com",
            password_hash="hashed_password",
        )
        
        test_session.add(active_user)
        test_session.add(deleted_user)
        await test_session.commit()
        
        # 软删除一个用户
        deleted_user.soft_delete()
        await test_session.commit()
        
        # 只查询未删除的用户
        result = await test_session.execute(
            select(User).where(User.is_deleted == False)
        )
        active_users = result.scalars().all()
        
        # 验证结果中不包含已删除用户
        active_emails = [u.email for u in active_users]
        assert "active@example.com" in active_emails
        assert "deleted@example.com" not in active_emails

    @pytest.mark.asyncio
    async def test_user_unique_email(self, test_session):
        """测试邮箱唯一性约束"""
        user1 = User(
            id=uuid4(),
            name="User 1",
            email="unique@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user1)
        await test_session.commit()
        
        # 尝试创建相同邮箱的用户
        user2 = User(
            id=uuid4(),
            name="User 2",
            email="unique@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user2)
        
        # 应该抛出异常
        with pytest.raises(Exception):  # IntegrityError
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_user_timestamps(self, test_session):
        """测试时间戳字段"""
        user = User(
            id=uuid4(),
            name="Timestamp User",
            email="timestamp@example.com",
            password_hash="hashed_password",
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        created_at = user.created_at
        updated_at = user.updated_at
        
        assert created_at is not None
        assert updated_at is not None
        assert created_at == updated_at
        
        # 手动更新 updated_at（模拟 touch 方法）
        import asyncio
        await asyncio.sleep(0.1)  # 确保时间差异
        user.name = "Updated Timestamp User"
        user.touch()  # 手动更新时间戳
        await test_session.commit()
        await test_session.refresh(user)
        
        # updated_at 应该更新
        assert user.updated_at >= updated_at
        assert user.created_at == created_at
