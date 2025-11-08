from django.db import models
from uuid import uuid7


class Article(models.Model):
    """記事モデル"""
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    title = models.CharField(max_length=200, verbose_name='タイトル')
    content = models.TextField(verbose_name='本文')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = '記事'
        verbose_name_plural = '記事'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
