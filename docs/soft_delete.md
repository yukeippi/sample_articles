# 論理削除（Soft Delete）

## 概要

論理削除は、データベースからレコードを物理的に削除するのではなく、削除フラグを立てることでデータを保持したまま非表示にする仕組みです。これにより、誤削除からのデータ復旧や監査証跡の保持が可能になります。

## 実装概要

本システムでは、以下のモデルで論理削除を実装しています：

- **Employee（社員）**
- **department（組織）**

## 基底モデル

### SoftDeleteModel

論理削除機能を提供する抽象基底モデル。

**ファイル:** [app/models/base.py](app/models/base.py)

```python
from django.db import models
from django.utils import timezone

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
```

### SoftDeleteManager

論理削除されたレコードをデフォルトで除外するカスタムマネージャー。

```python
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
```

## 使用方法

### 1. モデルへの適用

論理削除を使用したいモデルに `SoftDeleteModel` を継承させます。

```python
from .base import TimestampedModel, SoftDeleteModel

class Employee(TimestampedModel, SoftDeleteModel):
    """社員モデル"""
    # フィールド定義...
```

### 2. 論理削除の実行

通常の `delete()` メソッドを呼び出すと、論理削除が実行されます。

```python
# 社員を論理削除
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.delete()  # deleted_at に現在時刻が設定される

# デフォルトのクエリでは削除済みレコードは取得されない
employees = Employee.objects.all()  # 削除済みは含まれない
```

### 3. 削除済みレコードの取得

```python
# 削除済みも含めて取得
all_employees = Employee.objects.with_deleted()

# 削除済みのみ取得
deleted_employees = Employee.objects.only_deleted()

# 全レコードを取得（マネージャー経由せず）
all_records = Employee.all_objects.all()
```

### 4. 削除の取り消し（復元）

```python
# 削除済み社員を復元
employee = Employee.objects.with_deleted().get(email='yamada.taro@example.com')
if employee.is_deleted:
    employee.restore()  # deleted_at が None にリセットされる
```

### 5. 物理削除

本当にレコードを削除したい場合は `hard_delete()` を使用します。

```python
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.hard_delete()  # データベースから完全に削除される
```

## データベーススキーマ

### deleted_at カラム

| 属性 | 値 |
|------|-----|
| 型 | TIMESTAMP WITH TIME ZONE |
| NULL許可 | YES |
| デフォルト値 | NULL |
| インデックス | YES |

**状態:**
- `NULL`: レコードは有効（削除されていない）
- `タイムスタンプ`: レコードは削除済み（削除された日時）

## クエリの動作

### デフォルトマネージャー（objects）

```python
# 削除されていないレコードのみ取得
Employee.objects.all()
# SQL: SELECT * FROM app_employee WHERE deleted_at IS NULL
```

### with_deleted()

```python
# 削除済みも含めて全て取得
Employee.objects.with_deleted()
# SQL: SELECT * FROM app_employee
```

### only_deleted()

```python
# 削除済みのみ取得
Employee.objects.only_deleted()
# SQL: SELECT * FROM app_employee WHERE deleted_at IS NOT NULL
```

### all_objects マネージャー

```python
# マネージャー経由で全レコード取得
Employee.all_objects.all()
# SQL: SELECT * FROM app_employee
```

## ユースケース

### 1. 誤削除からの復旧

```python
# ユーザーが誤って社員を削除
employee.delete()

# 管理者が復元
deleted_employee = Employee.objects.with_deleted().get(id=employee_id)
deleted_employee.restore()
```

### 2. 監査証跡の保持

```python
# 組織の削除履歴を確認
deleted_orgs = department.objects.only_deleted()
for org in deleted_orgs:
    print(f'{org.name} - 削除日時: {org.deleted_at}')
```

### 3. 削除予定レコードの一覧

```python
# 30日以上前に削除されたレコードを物理削除
from django.utils import timezone
from datetime import timedelta

threshold = timezone.now() - timedelta(days=30)
old_deleted = Employee.objects.only_deleted().filter(deleted_at__lt=threshold)

for employee in old_deleted:
    employee.hard_delete()  # 物理削除
```

### 4. バッチ削除と復元

```python
# 特定組織の全社員を論理削除
org = department.objects.get(name='営業部')
org.employees.all().delete()

# 一括復元
deleted_employees = Employee.objects.only_deleted().filter(department=org)
for employee in deleted_employees:
    employee.restore()
```

## 注意事項

### 1. 外部キー制約との関係

論理削除されたレコードも物理的には存在するため、外部キー制約は維持されます。

```python
# 組織を論理削除しても、社員との関係は維持される
org = department.objects.get(name='営業部')
org.delete()  # 論理削除

# 社員から削除済み組織を参照可能
employee = Employee.objects.get(email='yamada.taro@example.com')
print(employee.department.name)  # '営業部' （削除済みでも参照可能）
```

### 2. ユニーク制約（Employee モデルの実装例）

**Employeeモデルでは、アプリケーション側でユニーク制約を実装しています。**

論理削除されたレコードは制約の対象外になります。

```python
# 社員を論理削除
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.delete()  # 論理削除

# 同じメールアドレスで新規作成可能（削除済みは対象外）
Employee.objects.create(
    email='yamada.taro@example.com',  # OK（employee は削除済み）
    name='山田次郎',
    department=org
)
```

**実装方法:**

```python
class Employee(TimestampedModel, SoftDeleteModel):
    email = models.EmailField(verbose_name='メールアドレス')  # unique=True なし

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
```

`Employee.objects`は`SoftDeleteManager`を使用しているため、`deleted_at IS NULL`のレコードのみを自動的にチェックします。

**他の解決策:**
1. **パーシャルインデックス（PostgreSQL）**: DB側で `deleted_at IS NULL` の条件付きユニーク制約
2. **削除時に値を変更**: メールアドレスに削除日時を付加（例: `email_20250201_153000`）

### 3. カスケード削除

`on_delete=models.CASCADE` が設定されている外部キーでは、親レコードの論理削除時に子レコードも論理削除する必要があります。

```python
# 組織の論理削除時に子組織も論理削除
class department(TimestampedModel, SoftDeleteModel):
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,  # 物理削除のカスケード
        # ...
    )

    def delete(self, using=None, keep_parents=False):
        # 子組織も論理削除
        for child in self.children.all():
            child.delete()
        # 自身を論理削除
        super().delete(using=using, keep_parents=keep_parents)
```

### 4. パフォーマンス

論理削除されたレコードもテーブルに残るため、以下の影響があります：

- テーブルサイズの増加
- インデックスサイズの増加
- クエリパフォーマンスの低下（大量の削除済みレコードがある場合）

**対策:**
- 定期的に古い削除済みレコードを物理削除
- `deleted_at` にインデックスを作成（実装済み）
- パーティショニングの検討

## ベストプラクティス

### 1. 削除ポリシーの明確化

どのモデルで論理削除を使用するか、物理削除との使い分けを明確にします。

**論理削除を推奨:**
- ユーザーデータ（監査が必要）
- マスターデータ（履歴保持が必要）
- 復元の可能性があるデータ

**物理削除を推奨:**
- 一時データ
- ログデータ
- 機密データ（削除が必須）

### 2. 定期的なクリーンアップ

```python
# 管理コマンドの例
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Employee, department

class Command(BaseCommand):
    help = '30日以上前に削除されたレコードを物理削除'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(days=30)

        # 社員の物理削除
        old_employees = Employee.objects.only_deleted().filter(
            deleted_at__lt=threshold
        )
        count = old_employees.count()
        for employee in old_employees:
            employee.hard_delete()

        self.stdout.write(
            self.style.SUCCESS(f'{count}件の社員レコードを物理削除しました')
        )
```

### 3. UI/UX の考慮

削除操作時にユーザーに以下を明示します：

- 論理削除であること（復元可能）
- 復元方法
- 物理削除までの期間

### 4. テストの実装

```python
from django.test import TestCase
from app.models import Employee, department

class SoftDeleteTestCase(TestCase):
    def test_soft_delete(self):
        """論理削除のテスト"""
        org = department.objects.create(name='テスト部署')
        employee = Employee.objects.create(
            name='テスト太郎',
            email='test@example.com',
            department=org
        )

        # 削除
        employee.delete()

        # デフォルトでは取得できない
        self.assertFalse(Employee.objects.filter(id=employee.id).exists())

        # with_deleted() で取得可能
        self.assertTrue(
            Employee.objects.with_deleted().filter(id=employee.id).exists()
        )

        # deleted_at が設定されている
        deleted_employee = Employee.objects.with_deleted().get(id=employee.id)
        self.assertIsNotNone(deleted_employee.deleted_at)
        self.assertTrue(deleted_employee.is_deleted)

    def test_restore(self):
        """復元のテスト"""
        org = department.objects.create(name='テスト部署')
        employee = Employee.objects.create(
            name='テスト太郎',
            email='test@example.com',
            department=org
        )

        # 削除と復元
        employee.delete()
        employee.restore()

        # 通常のクエリで取得可能
        self.assertTrue(Employee.objects.filter(id=employee.id).exists())

        # deleted_at が NULL
        restored_employee = Employee.objects.get(id=employee.id)
        self.assertIsNone(restored_employee.deleted_at)
        self.assertFalse(restored_employee.is_deleted)

    def test_hard_delete(self):
        """物理削除のテスト"""
        org = department.objects.create(name='テスト部署')
        employee = Employee.objects.create(
            name='テスト太郎',
            email='test@example.com',
            department=org
        )

        employee_id = employee.id
        employee.hard_delete()

        # どのマネージャーでも取得不可
        self.assertFalse(
            Employee.objects.with_deleted().filter(id=employee_id).exists()
        )
        self.assertFalse(
            Employee.all_objects.filter(id=employee_id).exists()
        )
```

## まとめ

論理削除の実装により：

- **データの安全性**: 誤削除からの復旧が可能
- **監査証跡**: 削除履歴の保持
- **柔軟な運用**: 論理削除と物理削除の使い分け
- **データ整合性**: 外部キー関係の維持

適切な削除ポリシーと定期的なクリーンアップにより、効率的なデータ管理が実現できます。
