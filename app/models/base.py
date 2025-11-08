from django.db import models


class TimestampedModel(models.Model):
    """タイムスタンプを持つ抽象ベースモデル"""
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='作成日時'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新日時'
    )

    class Meta:
        abstract = True
