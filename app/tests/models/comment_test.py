import pytest
from django.contrib.auth.models import User
from app.models import Article, Comment
from uuid import UUID


@pytest.fixture
def test_user(db):
    """テスト用ユーザーのフィクスチャ"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_article(db, test_user):
    """テスト用記事のフィクスチャ"""
    return Article.objects.create(
        title='テスト記事',
        content='これはテスト記事の本文です。',
        user=test_user
    )


@pytest.fixture
def test_comment(db, test_article, test_user):
    """テスト用コメントのフィクスチャ"""
    return Comment.objects.create(
        article=test_article,
        user=test_user,
        content='これはテストコメントです。'
    )


@pytest.mark.django_db
class TestCommentModel:
    """Commentモデルのテスト"""

    def test_comment_creation(self, test_comment):
        """コメントが正しく作成されることを確認"""
        assert isinstance(test_comment, Comment)
        assert test_comment.content == 'これはテストコメントです。'

    def test_comment_id_is_uuid(self, test_comment):
        """コメントのIDがUUIDであることを確認"""
        assert isinstance(test_comment.id, UUID)

    def test_comment_str_method(self, test_comment):
        """__str__メソッドが正しい形式を返すことを確認"""
        expected = f'{test_comment.user.username} - {test_comment.article.title}'
        assert str(test_comment) == expected

    def test_comment_has_timestamps(self, test_comment):
        """コメントが作成日時と更新日時を持つことを確認"""
        assert test_comment.created_at is not None
        assert test_comment.updated_at is not None

    def test_comment_content_is_text_field(self, test_comment):
        """コメント内容がTextFieldであることを確認"""
        field_type = test_comment._meta.get_field('content').get_internal_type()
        assert field_type == 'TextField'

    def test_comment_verbose_names(self, test_comment):
        """フィールドのverbose_nameが正しく設定されていることを確認"""
        assert test_comment._meta.get_field('article').verbose_name == '記事'
        assert test_comment._meta.get_field('user').verbose_name == '投稿者'
        assert test_comment._meta.get_field('content').verbose_name == 'コメント内容'
        assert test_comment._meta.get_field('created_at').verbose_name == '作成日時'
        assert test_comment._meta.get_field('updated_at').verbose_name == '更新日時'

    def test_comment_meta_verbose_name(self, test_comment):
        """Metaのverbose_nameが正しく設定されていることを確認"""
        assert test_comment._meta.verbose_name == 'コメント'
        assert test_comment._meta.verbose_name_plural == 'コメント'

    def test_comment_article_relationship(self, test_comment, test_article):
        """コメントと記事の関連が正しく設定されていることを確認"""
        assert test_comment.article == test_article
        assert test_comment in test_article.comments.all()

    def test_comment_user_relationship(self, test_comment, test_user):
        """コメントとユーザーの関連が正しく設定されていることを確認"""
        assert test_comment.user == test_user
        assert test_comment in test_user.comments.all()

    def test_comment_ordering(self, db, test_article, test_user):
        """コメントが作成日時の降順で並ぶことを確認"""
        comment1 = Comment.objects.create(
            article=test_article,
            user=test_user,
            content='コメント1'
        )
        comment2 = Comment.objects.create(
            article=test_article,
            user=test_user,
            content='コメント2'
        )
        comments = Comment.objects.all()
        assert comments[0] == comment2
        assert comments[1] == comment1

    def test_comment_cascade_delete_article(self, db, test_user):
        """記事が削除されたときにコメントも削除されることを確認"""
        article = Article.objects.create(
            title='削除テスト記事',
            content='内容',
            user=test_user
        )
        comment = Comment.objects.create(
            article=article,
            user=test_user,
            content='削除テストコメント'
        )
        comment_id = comment.id
        article.delete()
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_comment_cascade_delete_user(self, db):
        """ユーザーが削除されたときにコメントも削除されることを確認"""
        user = User.objects.create_user(
            username='deleteuser',
            email='delete@example.com',
            password='testpass123'
        )
        article = Article.objects.create(
            title='削除テスト記事',
            content='内容',
            user=user
        )
        comment = Comment.objects.create(
            article=article,
            user=user,
            content='削除テストコメント'
        )
        comment_id = comment.id
        user.delete()
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_multiple_comments_on_article(self, db, test_article, test_user):
        """1つの記事に複数のコメントを追加できることを確認"""
        comment1 = Comment.objects.create(
            article=test_article,
            user=test_user,
            content='1つ目のコメント'
        )
        comment2 = Comment.objects.create(
            article=test_article,
            user=test_user,
            content='2つ目のコメント'
        )
        assert test_article.comments.count() == 2
        assert comment1 in test_article.comments.all()
        assert comment2 in test_article.comments.all()
