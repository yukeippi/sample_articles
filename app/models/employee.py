from uuid import uuid7

from django.db import models

from .base import TimestampedModel, SoftDeleteModel


class Employee(TimestampedModel, SoftDeleteModel):
    """社員モデル"""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    name = models.CharField(max_length=200, verbose_name='氏名')
    email = models.EmailField(unique=True, verbose_name='メールアドレス')
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='所属組織',
    )

    class Meta:
        verbose_name = '社員'
        verbose_name_plural = '社員'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'{self.name} ({self.email})'
