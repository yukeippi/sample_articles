import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db(transaction=True)
def test_login_success(page: Page, live_server, db):
    """ログイン成功のテスト"""
    from django.contrib.auth import get_user_model
    user = get_user_model()

    # テストユーザーを作成
    user.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="password"
    )

    # ログインページにアクセス
    page.goto(f'{live_server.url}/login/')

    # ページタイトルを確認
    expect(page).to_have_title('ログイン')

    # ログインフォームに入力
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', 'password')

    # ログインボタンをクリックしてナビゲーションを待機
    with page.expect_navigation():
        page.click('button[type="submit"]')

    # ナビゲーションバーにユーザー名が表示されることを確認
    expect(page.locator('text=ようこそ、testuser')).to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_login_failure(page: Page, live_server, db):
    """ログイン失敗のテスト"""
    from django.contrib.auth import get_user_model
    user = get_user_model()

    # テストユーザーを作成
    user.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="password"
    )

    # ログインページにアクセス
    page.goto(f'{live_server.url}/login/')

    # 間違った認証情報でログインを試みる
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', 'wrongpassword')
    page.click('button[type="submit"]')

    # ログインページに留まることを確認
    expect(page).to_have_url(f'{live_server.url}/login/')

    # エラーメッセージが表示されることを確認（フォームエラーが表示される）
    expect(page.locator('.alert-danger, .invalid-feedback')).to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_logout(authenticated_page: Page, live_server):
    """ログアウトのテスト"""
    # ログアウトボタンをクリックしてナビゲーションを待機
    with authenticated_page.expect_navigation():
        authenticated_page.click('button[type="submit"]:has-text("ログアウト")')

    # ログインボタンが表示されることを確認
    expect(authenticated_page.locator('a:has-text("ログイン")')).to_be_visible()

    # ユーザー名が表示されないことを確認
    expect(authenticated_page.locator('text=ようこそ、testuser')).not_to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_redirect_to_login_for_protected_page(page: Page, live_server):
    """保護されたページへのアクセス時にログインページにリダイレクトされることを確認"""
    # 未ログインで新規作成ページにアクセス
    page.goto(f'{live_server.url}/article/new/')

    # ログインページにリダイレクトされることを確認
    page.wait_for_url(f'{live_server.url}/login/?next=/article/new/')
    expect(page).to_have_title('ログイン')
