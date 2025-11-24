from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    """タイムスタンプを持つ抽象ベースモデル"""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """論理削除を考慮したマネージャー"""

    def get_queryset(self):
        """デフォルトで削除済みを除外"""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """削除済みも含める"""
        return super().get_queryset()

    def only_deleted(self):
        """削除済みのみ"""
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """論理削除を実装する基底モデル"""

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='削除日時'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # 削除済み含む全レコード

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """論理削除（deleted_atに現在時刻を設定）"""
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self):
        """物理削除（実際にレコードを削除）"""
        super().delete()

    def restore(self):
        """削除を取り消し"""
        self.deleted_at = None
        self.save()

    @property
    def is_deleted(self):
        """削除済みかどうか"""
        return self.deleted_at is not None
