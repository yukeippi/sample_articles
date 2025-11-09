"""
pytest fixtures for testing
"""

import pytest
from django.contrib.auth.models import User
from faker import Faker
from model_bakery import baker

from app.models import Article, Comment

fake = Faker('ja_JP')  # 日本語のfakerを使用


@pytest.fixture
def user_factory():
    """ユーザーを作成するファクトリ"""

    def _create_user(**kwargs):
        defaults = {
            'username': fake.user_name(),
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
        }
        defaults.update(kwargs)
        return baker.make(User, **defaults)

    return _create_user


@pytest.fixture
def user(user_factory):
    """単一のテストユーザー"""
    return user_factory()


@pytest.fixture
def users(user_factory):
    """複数のテストユーザー（3人）"""
    return [user_factory() for _ in range(3)]


@pytest.fixture
def article_factory(user):
    """記事を作成するファクトリ"""

    def _create_article(**kwargs):
        defaults = {
            'title': fake.sentence(),
            'content': fake.text(),
            'user': user,
        }
        defaults.update(kwargs)
        return baker.make(Article, **defaults)

    return _create_article


@pytest.fixture
def article(article_factory):
    """単一のテスト記事"""
    return article_factory()


@pytest.fixture
def articles(article_factory):
    """複数のテスト記事（5件）"""
    return [article_factory() for _ in range(5)]


@pytest.fixture
def comment_factory(user, article):
    """コメントを作成するファクトリ"""

    def _create_comment(**kwargs):
        defaults = {
            'article': article,
            'user': user,
            'content': fake.text(max_nb_chars=200),
        }
        defaults.update(kwargs)
        return baker.make(Comment, **defaults)

    return _create_comment


@pytest.fixture
def comment(comment_factory):
    """単一のテストコメント"""
    return comment_factory()


@pytest.fixture
def comments(comment_factory):
    """複数のテストコメント（3件）"""
    return [comment_factory() for _ in range(3)]


@pytest.fixture
def article_with_comments(article_factory, user_factory):
    """コメント付きの記事"""
    article = article_factory()
    users = [user_factory() for _ in range(3)]

    for user in users:
        baker.make(Comment, article=article, user=user, content=fake.text(max_nb_chars=200))

    return article
