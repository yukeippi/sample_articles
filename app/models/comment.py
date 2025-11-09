from uuid import uuid7

from django.contrib.auth.models import User
from django.db import models

from .article import Article


class Comment(models.Model):
    """コメントモデル"""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='comments', verbose_name='記事'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments', verbose_name='投稿者'
    )
    content = models.TextField(verbose_name='コメント内容')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.article.title}'
