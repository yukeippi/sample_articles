import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db(transaction=True)
def test_view_article_list(page: Page, live_server):
    """記事一覧の表示テスト"""
    page.goto(f'{live_server.url}/')

    # ページタイトルを確認
    expect(page).to_have_title('記事一覧')

    # 見出しが表示されることを確認
    expect(page.locator('h1:has-text("記事一覧")')).to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_create_article(authenticated_page: Page, live_server):
    """記事作成のテスト"""
    # トップページの新規作成ボタンをクリック
    authenticated_page.goto(f'{live_server.url}/')

    with authenticated_page.expect_navigation():
        authenticated_page.click('a:has-text("新規作成")')

    expect(authenticated_page).to_have_title('新規記事作成')

    # フォームに入力
    authenticated_page.fill('input[name="title"]', 'E2Eテスト記事')
    authenticated_page.fill('textarea[name="content"]', 'これはE2Eテストで作成された記事です。')

    # 作成ボタンをクリックしてナビゲーションを待機
    with authenticated_page.expect_navigation():
        authenticated_page.click('button:has-text("作成")')

    # 詳細ページにリダイレクトされることを確認
    expect(authenticated_page.locator('h1')).to_contain_text('E2Eテスト記事')
    expect(authenticated_page.locator('.article-content')).to_contain_text(
        'これはE2Eテストで作成された記事です。'
    )

    # 投稿者が表示されることを確認
    expect(authenticated_page.locator('text=投稿者: testuser')).to_be_visible()


@pytest.mark.django_db(transaction=True)
def test_edit_article(authenticated_page: Page, live_server):
    """記事編集のテスト"""
    # まず記事を作成
    authenticated_page.goto(f'{live_server.url}/article/new/')
    authenticated_page.fill('input[name="title"]', '編集前のタイトル')
    authenticated_page.fill('textarea[name="content"]', '編集前の内容')

    with authenticated_page.expect_navigation():
        authenticated_page.click('button:has-text("作成")')

    # 詳細ページで編集ボタンをクリック
    with authenticated_page.expect_navigation():
        authenticated_page.click('a:has-text("編集")')

    # 編集ページに遷移
    expect(authenticated_page).to_have_title('記事の編集 - 編集前のタイトル')

    # フォームを編集
    authenticated_page.fill('input[name="title"]', '編集後のタイトル')
    authenticated_page.fill('textarea[name="content"]', '編集後の内容')

    # 保存ボタンをクリック
    with authenticated_page.expect_navigation():
        authenticated_page.click('button:has-text("保存")')

    # 詳細ページにリダイレクトされ、更新された内容が表示されることを確認
    expect(authenticated_page.locator('h1')).to_contain_text('編集後のタイトル')
    expect(authenticated_page.locator('.article-content')).to_contain_text('編集後の内容')


@pytest.mark.django_db(transaction=True)
def test_delete_article(authenticated_page: Page, live_server):
    """記事削除のテスト"""
    # まず記事を作成
    authenticated_page.goto(f'{live_server.url}/article/new/')
    authenticated_page.fill('input[name="title"]', '削除する記事')
    authenticated_page.fill('textarea[name="content"]', 'この記事は削除されます')

    with authenticated_page.expect_navigation():
        authenticated_page.click('button:has-text("作成")')

    # 詳細ページで削除ボタンをクリック
    with authenticated_page.expect_navigation():
        authenticated_page.click('a:has-text("削除")')

    # 削除確認ページに遷移
    expect(authenticated_page).to_have_title('記事の削除 - 削除する記事')
    expect(authenticated_page.locator('text=この操作は取り消せません')).to_be_visible()

    # 削除ボタンをクリック
    with authenticated_page.expect_navigation():
        authenticated_page.click('button:has-text("削除する")')

    # 一覧ページにリダイレクトされることを確認
    expect(authenticated_page).to_have_title('記事一覧')


@pytest.mark.django_db(transaction=True)
def test_cannot_edit_others_article(page: Page, live_server, db):
    """他のユーザーの記事を編集できないことを確認"""
    from django.contrib.auth import get_user_model
    user = get_user_model()

    # otheruser を作成
    user.objects.create_user(
        username="otheruser",
        email="otheruser@example.com",
        password="password"
    )

    # otheruser でログイン
    page.goto(f'{live_server.url}/login/')
    page.fill('input[name="username"]', 'otheruser')
    page.fill('input[name="password"]', 'password')

    with page.expect_navigation():
        page.click('button[type="submit"]')

    # 記事を作成
    page.goto(f'{live_server.url}/article/new/')
    page.fill('input[name="title"]', 'otheruserの記事')
    page.fill('textarea[name="content"]', 'この記事はotheruserが作成しました')

    with page.expect_navigation():
        page.click('button:has-text("作成")')

    # URLを保存
    article_url = page.url

    # ログアウト
    with page.expect_navigation():
        page.click('button:has-text("ログアウト")')

    # testuser を作成してログイン
    user.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="password"
    )

    page.goto(f'{live_server.url}/login/')
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', 'password')

    with page.expect_navigation():
        page.click('button[type="submit"]')

    # 他のユーザーの記事にアクセス
    page.goto(article_url)

    # 編集・削除ボタンが表示されないことを確認
    expect(page.locator('a:has-text("編集")')).not_to_be_visible()
    expect(page.locator('a:has-text("削除")')).not_to_be_visible()
