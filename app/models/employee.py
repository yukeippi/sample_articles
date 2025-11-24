from uuid import uuid7

from django.core.exceptions import ValidationError
from django.db import models

from .base import TimestampedModel, SoftDeleteModel


class Employee(TimestampedModel, SoftDeleteModel):
    """社員モデル"""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    name = models.CharField(max_length=200, verbose_name='氏名')
    email = models.EmailField(verbose_name='メールアドレス')
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
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

    def clean(self):
        """バリデーション: 論理削除されていない社員のメールアドレスは重複不可"""
        super().clean()

        # 削除されていない社員の中で同じメールアドレスがないかチェック
        query = Employee.objects.filter(email=self.email)

        # 更新の場合は自分自身を除外
        if self.pk:
            query = query.exclude(pk=self.pk)

        if query.exists():
            raise ValidationError({
                'email': 'このメールアドレスは既に使用されています。'
            })

    def save(self, *args, **kwargs):
        """保存前にバリデーションを実行"""
        self.full_clean()
        super().save(*args, **kwargs)
