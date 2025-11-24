from uuid import uuid7

from django.db import models

from .base import TimestampedModel, SoftDeleteModel


class Organization(TimestampedModel, SoftDeleteModel):
    """組織マスターモデル（隣接リストモデル）"""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False, verbose_name='ID')
    name = models.CharField(max_length=200, verbose_name='組織名')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='親組織',
    )

    class Meta:
        verbose_name = '組織'
        verbose_name_plural = '組織'
        ordering = ['name']
        indexes = [
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """先祖組織を取得（ルートまで）"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """子孫組織を取得（再帰的に全て）"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_level(self):
        """階層レベルを取得（ルート=0）"""
        return len(self.get_ancestors())
