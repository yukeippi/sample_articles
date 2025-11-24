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

    def delete(self, using=None, keep_parents=False):
        """論理削除（子組織の親と所属社員の組織をNULLに設定）"""
        # 子組織の親をNULLに設定（ルート組織化）
        self.children.update(parent=None)

        # 所属社員の組織をNULLに設定（未所属化）
        self.employees.update(organization=None)

        # 自身を論理削除
        super().delete(using=using, keep_parents=keep_parents)

    def merge_into(self, target_organization):
        """
        この組織を他の組織に統合する

        Args:
            target_organization: 統合先の組織

        処理内容:
        - この組織に所属する社員を全て統合先組織に移動
        - この組織の子組織を全て統合先組織の子組織に変更
        - この組織を論理削除
        """
        if not isinstance(target_organization, Organization):
            raise ValueError('統合先は組織オブジェクトである必要があります')

        if target_organization.pk == self.pk:
            raise ValueError('自分自身に統合することはできません')

        # 統合先が削除済みの場合はエラー
        if target_organization.deleted_at is not None:
            raise ValueError('削除済みの組織には統合できません')

        # 統合先が自分の子孫の場合はエラー（循環参照を防ぐ）
        if target_organization in self.get_descendants():
            raise ValueError('子孫組織には統合できません')

        # 所属社員を統合先組織に移動
        self.employees.update(organization=target_organization)

        # 子組織の親を統合先組織に変更
        self.children.update(parent=target_organization)

        # 自身を論理削除
        self.delete()
