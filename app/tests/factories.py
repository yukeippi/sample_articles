"""
Model factories using model_bakery and faker
テストデータ作成用のファクトリ関数
"""

from django.contrib.auth.models import User
from faker import Faker
from model_bakery import baker

from app.models import Article, Comment

fake = Faker('ja_JP')


class UserFactory:
    """ユーザーファクトリ"""

    @staticmethod
    def create(**kwargs):
        """ユーザーを作成"""
        defaults = {
            'username': fake.user_name(),
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
        }
        defaults.update(kwargs)
        return baker.make(User, **defaults)

    @staticmethod
    def create_batch(size=5, **kwargs):
        """複数のユーザーを作成"""
        return [UserFactory.create(**kwargs) for _ in range(size)]


class ArticleFactory:
    """記事ファクトリ"""

    @staticmethod
    def create(user=None, **kwargs):
        """記事を作成"""
        if user is None:
            user = UserFactory.create()

        defaults = {
            'title': fake.sentence(),
            'content': fake.text(max_nb_chars=500),
            'user': user,
        }
        defaults.update(kwargs)
        return baker.make(Article, **defaults)

    @staticmethod
    def create_batch(size=5, user=None, **kwargs):
        """複数の記事を作成"""
        if user is None:
            user = UserFactory.create()
        return [ArticleFactory.create(user=user, **kwargs) for _ in range(size)]


class CommentFactory:
    """コメントファクトリ"""

    @staticmethod
    def create(article=None, user=None, **kwargs):
        """コメントを作成"""
        if article is None:
            article = ArticleFactory.create()
        if user is None:
            user = UserFactory.create()

        defaults = {
            'article': article,
            'user': user,
            'content': fake.text(max_nb_chars=200),
        }
        defaults.update(kwargs)
        return baker.make(Comment, **defaults)

    @staticmethod
    def create_batch(size=3, article=None, user=None, **kwargs):
        """複数のコメントを作成"""
        if article is None:
            article = ArticleFactory.create()
        return [CommentFactory.create(article=article, user=user, **kwargs) for _ in range(size)]


def create_article_with_comments(num_comments=3):
    """コメント付きの記事を作成"""
    article = ArticleFactory.create()
    CommentFactory.create_batch(size=num_comments, article=article)
    return article
