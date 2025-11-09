from uuid import UUID

import pytest

from app.models import Comment
from app.tests.factories import ArticleFactory, CommentFactory, UserFactory


@pytest.mark.django_db
class TestCommentModel:
    """Commentモデルのテスト"""

    def test_comment_creation(self, comment):
        """コメントが正しく作成されることを確認"""
        assert isinstance(comment, Comment)
        assert comment.content
        assert comment.article is not None
        assert comment.user is not None

    def test_comment_creation_with_custom_values(self):
        """カスタム値でコメントが作成されることを確認"""
        comment = CommentFactory.create(content='カスタムコメント')
        assert comment.content == 'カスタムコメント'

    def test_comment_id_is_uuid(self, comment):
        """コメントのIDがUUIDであることを確認"""
        assert isinstance(comment.id, UUID)

    def test_comment_str_method(self, comment):
        """__str__メソッドが正しい形式を返すことを確認"""
        expected = f'{comment.user.username} - {comment.article.title}'
        assert str(comment) == expected

    def test_comment_has_timestamps(self, comment):
        """コメントが作成日時と更新日時を持つことを確認"""
        assert comment.created_at is not None
        assert comment.updated_at is not None

    def test_comment_content_is_text_field(self, comment):
        """コメント内容がTextFieldであることを確認"""
        field_type = comment._meta.get_field('content').get_internal_type()
        assert field_type == 'TextField'

    def test_comment_verbose_names(self, comment):
        """フィールドのverbose_nameが正しく設定されていることを確認"""
        assert comment._meta.get_field('article').verbose_name == '記事'
        assert comment._meta.get_field('user').verbose_name == '投稿者'
        assert comment._meta.get_field('content').verbose_name == 'コメント内容'
        assert comment._meta.get_field('created_at').verbose_name == '作成日時'
        assert comment._meta.get_field('updated_at').verbose_name == '更新日時'

    def test_comment_meta_verbose_name(self, comment):
        """Metaのverbose_nameが正しく設定されていることを確認"""
        assert comment._meta.verbose_name == 'コメント'
        assert comment._meta.verbose_name_plural == 'コメント'

    def test_comment_article_relationship(self, comment):
        """コメントと記事の関連が正しく設定されていることを確認"""
        assert comment.article is not None
        assert comment in comment.article.comments.all()

    def test_comment_user_relationship(self, comment):
        """コメントとユーザーの関連が正しく設定されていることを確認"""
        assert comment.user is not None
        assert comment in comment.user.comments.all()

    def test_comment_ordering(self, article, user):
        """コメントが作成日時の降順で並ぶことを確認"""
        comment1 = CommentFactory.create(article=article, user=user, content='コメント1')
        comment2 = CommentFactory.create(article=article, user=user, content='コメント2')
        comments = Comment.objects.all()
        # 最後に作成されたコメントが最初に来る
        assert comments[0] == comment2
        assert comments[1] == comment1

    def test_comment_cascade_delete_article(self):
        """記事が削除されたときにコメントも削除されることを確認"""
        article = ArticleFactory.create()
        comment = CommentFactory.create(article=article)
        comment_id = comment.id
        article.delete()
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_comment_cascade_delete_user(self):
        """ユーザーが削除されたときにコメントも削除されることを確認"""
        user = UserFactory.create()
        article = ArticleFactory.create(user=user)
        comment = CommentFactory.create(article=article, user=user)
        comment_id = comment.id
        user.delete()
        assert not Comment.objects.filter(id=comment_id).exists()

    def test_multiple_comments_on_article(self, article, user):
        """1つの記事に複数のコメントを追加できることを確認"""
        comment1 = CommentFactory.create(article=article, user=user, content='1つ目のコメント')
        comment2 = CommentFactory.create(article=article, user=user, content='2つ目のコメント')
        assert article.comments.count() == 2
        assert comment1 in article.comments.all()
        assert comment2 in article.comments.all()
