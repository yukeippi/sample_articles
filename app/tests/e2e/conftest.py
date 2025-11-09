"""
E2Eテストの共通設定とフィクスチャ
"""
import os

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page

# Django の非同期警告を回避
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

User = get_user_model()


@pytest.fixture(scope="function")
def user(db):
    """テスト用ユーザーを作成"""
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123"
    )


@pytest.fixture(scope="function")
def authenticated_page(page: Page, live_server, user):
    """認証済みのページを提供"""
    # ログインページにアクセス
    page.goto(f"{live_server.url}/login/")

    # ログインフォームに入力
    page.fill('input[name="username"]', user.username)
    page.fill('input[name="password"]', "testpass123")

    # ログインボタンをクリック
    page.click('button[type="submit"]')

    # ログイン完了を待つ
    page.wait_for_url(f"{live_server.url}/")

    return page
