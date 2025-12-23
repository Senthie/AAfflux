"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:21:51
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 10:21:54
FilePath: : AAfflux: api: app: tasks: cleanup_tasks.py
Description:定期清理过期记录的celery任务
"""

import logging

from celery import shared_task

from app.core.database import get_session
from app.services.execution_record_service import ExecutionRecordService

logger = logging.getLogger(__name__)


@shared_task(name='cleanup_expired_execution_records')
def cleanup_expired_execution_records(days: int = 90):
    """清理过期的执行记录

    Args:
        days: 保留天数，默认90天
    """
    try:
        session = next(get_session())
        service = ExecutionRecordService(session)

        count = service.cleanup_expired_records(days)
        logger.info(f'清理了 {count} 条过期的执行记录（{days}天前）')

        return {'success': True, 'count': count}
    except Exception as e:
        logger.error(f'清理过期执行记录失败: {str(e)}')
        return {'success': False, 'error': str(e)}
    finally:
        session.close()


@shared_task(name='cleanup_failed_execution_records')
def cleanup_failed_execution_records(days: int = 30):
    """清理失败的执行记录

    Args:
        days: 保留天数，默认30天
    """
    try:
        session = next(get_session())
        service = ExecutionRecordService(session)

        count = service.cleanup_failed_records(days)
        logger.info(f'清理了 {count} 条失败的执行记录（{days}天前）')

        return {'success': True, 'count': count}
    except Exception as e:
        logger.error(f'清理失败执行记录失败: {str(e)}')
        return {'success': False, 'error': str(e)}
    finally:
        session.close()


@shared_task(name='archive_old_execution_records')
def archive_old_execution_records(days: int = 180):
    """归档旧的执行记录

    Args:
        days: 归档天数，默认180天

    注意：此功能需要配合外部存储系统实现
    """
    try:
        # TODO: 实现归档逻辑
        # 1. 查询需要归档的记录
        # 2. 导出到外部存储（如S3、OSS等）
        # 3. 删除已归档的记录

        logger.info('归档功能待实现')
        return {'success': True, 'message': '归档功能待实现'}
    except Exception as e:
        logger.error(f'归档执行记录失败: {str(e)}')
        return {'success': False, 'error': str(e)}


# Celery Beat 定时任务配置示例
# 在 celery 配置文件中添加以下内容：
"""
from celery.schedules import crontab

beat_schedule = {
    'cleanup-expired-records-daily': {
        'task': 'cleanup_expired_execution_records',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
        'args': (90,)  # 清理90天前的记录
    },
    'cleanup-failed-records-weekly': {
        'task': 'cleanup_failed_execution_records',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # 每周日凌晨3点执行
        'args': (30,)  # 清理30天前的失败记录
    },
    'archive-old-records-monthly': {
        'task': 'archive_old_execution_records',
        'schedule': crontab(day_of_month=1, hour=4, minute=0),  # 每月1号凌晨4点执行
        'args': (180,)  # 归档180天前的记录
    }
}
"""
