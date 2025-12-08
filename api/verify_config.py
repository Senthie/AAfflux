#!/usr/bin/env python3
"""Verify project configuration."""

import os
from dotenv import load_dotenv


def verify_config():
    """Verify all required configuration is present."""
    load_dotenv()

    print('🔧 Verifying project configuration...')
    print('=' * 50)

    # Required environment variables
    required_vars = {
        'DATABASE_URL': 'PostgreSQL database connection',
        'MONGODB_URL': 'MongoDB connection',
        'REDIS_URL': 'Redis connection',
        'JWT_SECRET_KEY': 'JWT secret key for authentication',
    }

    optional_vars = {
        'SENTRY_DSN': 'Sentry error tracking',
        'CELERY_BROKER_URL': 'Celery message broker',
        'CELERY_RESULT_BACKEND': 'Celery result backend',
    }

    print('📋 Required Configuration:')
    all_good = True

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'PASSWORD' in var or 'KEY' in var:
                display_value = f'{value[:8]}...' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f'  ✅ {var}: {display_value}')
        else:
            print(f'  ❌ {var}: Not set ({description})')
            all_good = False

    print('\n📋 Optional Configuration:')
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'PASSWORD' in var or 'KEY' in var:
                display_value = f'{value[:8]}...' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f'  ✅ {var}: {display_value}')
        else:
            print(f'  ⚪ {var}: Not set ({description})')

    print('\n📋 Database Configuration:')
    db_url = os.getenv('DATABASE_URL', '')
    if '14.12.0.102' in db_url:
        print('  ✅ Database server: 14.12.0.102 (Remote server)')
    elif 'localhost' in db_url:
        print('  ⚠️  Database server: localhost (Local development)')
    else:
        print('  ❓ Database server: Unknown')

    mongo_url = os.getenv('MONGODB_URL', '')
    if '14.12.0.102' in mongo_url:
        print('  ✅ MongoDB server: 14.12.0.102 (Remote server)')
    elif 'localhost' in mongo_url:
        print('  ⚠️  MongoDB server: localhost (Local development)')
    else:
        print('  ❓ MongoDB server: Unknown')

    redis_url = os.getenv('REDIS_URL', '')
    if '14.12.0.102' in redis_url:
        print('  ✅ Redis server: 14.12.0.102 (Remote server)')
    elif 'localhost' in redis_url:
        print('  ⚠️  Redis server: localhost (Local development)')
    else:
        print('  ❓ Redis server: Unknown')

    print('\n' + '=' * 50)
    if all_good:
        print('🎉 Configuration verification passed!')
        return True
    else:
        print('⚠️  Configuration verification failed. Please check missing variables.')
        return False


if __name__ == '__main__':
    success = verify_config()
    exit(0 if success else 1)
