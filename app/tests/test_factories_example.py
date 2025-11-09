"""
ファクトリとfixturesの使用例
"""

import pytest
from django.contrib.auth.models import User

from app.models import Article, Comment
from app.tests.factories import (
    ArticleFactory,
    CommentFactory,
    UserFactory,
    create_article_with_comments,
)


@pytest.mark.django_db
class TestUserFactory:
    """UserFactoryのテスト"""

    def test_create_user(self):
        """ユーザーを作成できる"""
        user = UserFactory.create()
        assert user.id is not None
        assert user.username
        assert user.email

    def test_create_user_with_custom_values(self):
        """カスタム値でユーザーを作成できる"""
        user = UserFactory.create(username='test_user', email='test@example.com')
        assert user.username == 'test_user'
        assert user.email == 'test@example.com'

    def test_create_batch_users(self):
        """複数のユーザーを作成できる"""
        users = UserFactory.create_batch(size=3)
        assert len(users) == 3
        assert User.objects.count() == 3


@pytest.mark.django_db
class TestArticleFactory:
    """ArticleFactoryのテスト"""

    def test_create_article(self):
        """記事を作成できる"""
        article = ArticleFactory.create()
        assert article.id is not None
        assert article.title
        assert article.content
        assert article.user is not None

    def test_create_article_with_specific_user(self):
        """特定のユーザーで記事を作成できる"""
        user = UserFactory.create(username='author')
        article = ArticleFactory.create(user=user)
        assert article.user.username == 'author'

    def test_create_batch_articles(self):
        """複数の記事を作成できる"""
        articles = ArticleFactory.create_batch(size=5)
        assert len(articles) == 5
        assert Article.objects.count() == 5


@pytest.mark.django_db
class TestCommentFactory:
    """CommentFactoryのテスト"""

    def test_create_comment(self):
        """コメントを作成できる"""
        comment = CommentFactory.create()
        assert comment.id is not None
        assert comment.content
        assert comment.article is not None
        assert comment.user is not None

    def test_create_comment_with_specific_article(self):
        """特定の記事にコメントを作成できる"""
        article = ArticleFactory.create(title='Test Article')
        comment = CommentFactory.create(article=article)
        assert comment.article.title == 'Test Article'

    def test_create_batch_comments(self):
        """複数のコメントを作成できる"""
        article = ArticleFactory.create()
        comments = CommentFactory.create_batch(size=3, article=article)
        assert len(comments) == 3
        assert Comment.objects.count() == 3
        assert all(c.article == article for c in comments)


@pytest.mark.django_db
class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_create_article_with_comments(self):
        """コメント付きの記事を作成できる"""
        article = create_article_with_comments(num_comments=5)
        assert article.id is not None
        assert article.comments.count() == 5


@pytest.mark.django_db
class TestFixtures:
    """Fixturesの使用例"""

    def test_user_fixture(self, user):
        """userフィクスチャを使用"""
        assert user.id is not None
        assert isinstance(user, User)

    def test_users_fixture(self, users):
        """usersフィクスチャを使用"""
        assert len(users) == 3
        assert all(isinstance(u, User) for u in users)

    def test_article_fixture(self, article):
        """articleフィクスチャを使用"""
        assert article.id is not None
        assert isinstance(article, Article)

    def test_articles_fixture(self, articles):
        """articlesフィクスチャを使用"""
        assert len(articles) == 5
        assert all(isinstance(a, Article) for a in articles)

    def test_comment_fixture(self, comment):
        """commentフィクスチャを使用"""
        assert comment.id is not None
        assert isinstance(comment, Comment)

    def test_comments_fixture(self, comments):
        """commentsフィクスチャを使用"""
        assert len(comments) == 3
        assert all(isinstance(c, Comment) for c in comments)

    def test_article_with_comments_fixture(self, article_with_comments):
        """article_with_commentsフィクスチャを使用"""
        assert article_with_comments.id is not None
        assert article_with_comments.comments.count() == 3

    def test_custom_fixture_usage(self, user_factory, article_factory):
        """ファクトリフィクスチャを使用してカスタムデータを作成"""
        author = user_factory(username='custom_author')
        article = article_factory(user=author, title='Custom Title')

        assert article.user.username == 'custom_author'
        assert article.title == 'Custom Title'
