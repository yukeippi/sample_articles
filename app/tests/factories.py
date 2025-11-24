"""
Model factories using model_bakery and faker
テストデータ作成用のファクトリ関数
"""

from django.contrib.auth.models import User
from faker import Faker
from model_bakery import baker

from app.models import Article, Comment, Employee, Organization

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


class OrganizationFactory:
    """組織ファクトリ"""

    @staticmethod
    def create(parent=None, **kwargs):
        """組織を作成"""
        defaults = {
            'name': fake.company(),
            'parent': parent,
        }
        defaults.update(kwargs)
        return baker.make(Organization, **defaults)

    @staticmethod
    def create_batch(size=5, parent=None, **kwargs):
        """複数の組織を作成"""
        return [OrganizationFactory.create(parent=parent, **kwargs) for _ in range(size)]


class EmployeeFactory:
    """社員ファクトリ"""

    @staticmethod
    def create(organization=None, **kwargs):
        """社員を作成"""
        defaults = {
            'name': fake.name(),
            'email': fake.email(),
            'organization': organization,
        }
        defaults.update(kwargs)
        return baker.make(Employee, **defaults)

    @staticmethod
    def create_batch(size=5, organization=None, **kwargs):
        """複数の社員を作成"""
        return [EmployeeFactory.create(organization=organization, **kwargs) for _ in range(size)]


def create_organization_hierarchy():
    """組織階層を作成（親組織→子組織→孫組織）"""
    parent = OrganizationFactory.create(name='本社')
    child1 = OrganizationFactory.create(name='営業部', parent=parent)
    child2 = OrganizationFactory.create(name='開発部', parent=parent)
    grandchild1 = OrganizationFactory.create(name='営業一課', parent=child1)
    grandchild2 = OrganizationFactory.create(name='営業二課', parent=child1)

    return {
        'parent': parent,
        'children': [child1, child2],
        'grandchildren': [grandchild1, grandchild2],
    }


def create_organization_with_employees(num_employees=3):
    """社員付きの組織を作成"""
    organization = OrganizationFactory.create()
    employees = EmployeeFactory.create_batch(size=num_employees, organization=organization)
    return organization, employees
