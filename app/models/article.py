from uuid import uuid7

from django.contrib.auth.models import User
from django.db import models

from .base import TimestampedModel


class Article(TimestampedModel):
    """記事モデル"""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    title = models.CharField(max_length=200, verbose_name='タイトル')
    content = models.TextField(verbose_name='本文')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='articles', verbose_name='投稿者'
    )

    class Meta:
        verbose_name = '記事'
        verbose_name_plural = '記事'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
