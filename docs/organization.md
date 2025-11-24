# 組織モデル

## 概要

組織情報を管理するモデル。階層構造（ツリー構造）を持つ組織を隣接リストモデルで表現します。

**論理削除対応:** このモデルは論理削除（Soft Delete）に対応しており、削除されたレコードは物理的には保持されます。詳細は [docs/soft_delete.md](soft_delete.md) を参照してください。

**予約更新対応:** このモデルは予約更新システムに対応しており、未来の日付での組織の作成・更新・削除を予約できます。詳細は [docs/reservation.md](reservation.md) を参照してください。

## テーブル構造

### Organization（組織）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PRIMARY KEY | 組織ID（uuid7） |
| name | VARCHAR(200) | NOT NULL | 組織名 |
| parent_id | UUID | FOREIGN KEY, NULL | 親組織ID |
| deleted_at | TIMESTAMP | NULL | 削除日時（論理削除） |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- `idx_organization_parent`: (parent_id)
- `idx_organization_deleted_at`: (deleted_at)

**制約:**
- `parent`: CASCADE制約（親組織削除時は子組織も削除される）
- 自己参照外部キー（組織は他の組織を親として持つことができる）

## データ構造

### 隣接リストモデル

組織は隣接リストモデルで階層構造を表現します。各組織は親組織への参照を持ちます。

```
会社（parent: NULL）
├── 営業部（parent: 会社）
│   ├── 営業一課（parent: 営業部）
│   └── 営業二課（parent: 営業部）
└── 人事部（parent: 会社）
    └── 採用課（parent: 人事部）
```

## データ例

### ルート組織（parent が NULL）
```json
{
  "id": "01234567-89ab-cdef-0123-456789abcdef",
  "name": "株式会社サンプル",
  "parent_id": null,
  "deleted_at": null,
  "created_at": "2025-01-01 00:00:00",
  "updated_at": "2025-01-01 00:00:00"
}
```

### 子組織（parent が存在）
```json
{
  "id": "fedcba98-7654-3210-fedc-ba9876543210",
  "name": "営業部",
  "parent_id": "01234567-89ab-cdef-0123-456789abcdef",
  "deleted_at": null,
  "created_at": "2025-01-05 09:00:00",
  "updated_at": "2025-01-05 09:00:00"
}
```

### 削除済み組織（deleted_at に日時が設定）
```json
{
  "id": "98765432-10fe-dcba-9876-543210fedcba",
  "name": "旧企画部",
  "parent_id": "01234567-89ab-cdef-0123-456789abcdef",
  "deleted_at": "2025-02-15 16:00:00",
  "created_at": "2025-01-01 00:00:00",
  "updated_at": "2025-02-15 16:00:00"
}
```

## モデル定義

### Organizationモデル (`app/models/organization.py`)

```python
from uuid import uuid7
from django.db import models
from .base import TimestampedModel, SoftDeleteModel

class Organization(TimestampedModel, SoftDeleteModel):
    """組織マスターモデル（隣接リストモデル）"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='組織名'
    )
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
```

**主要な特徴:**
- `SoftDeleteModel` を継承し、論理削除機能を追加
- 自己参照外部キー `parent` で階層構造を表現
- `CASCADE` 制約により、親組織削除時に子組織も削除
- 便利メソッド: `get_ancestors()`, `get_descendants()`, `get_level()`

## 主要機能

### 1. CRUD操作

#### 作成

**ルート組織の作成:**
```python
from app.models import Organization

# ルート組織（親なし）
company = Organization.objects.create(name='株式会社サンプル')
```

**子組織の作成:**
```python
# 親組織を指定
sales_dept = Organization.objects.create(
    name='営業部',
    parent=company
)

# さらに子組織
sales_team1 = Organization.objects.create(
    name='営業一課',
    parent=sales_dept
)
```

#### 読み取り

```python
# 全組織取得（論理削除されていない組織のみ）
organizations = Organization.objects.all()

# 親組織を含めて取得（N+1問題を回避）
organizations = Organization.objects.select_related('parent').all()

# ルート組織のみ取得
root_orgs = Organization.objects.filter(parent__isnull=True)

# 特定組織の子組織を取得
sales_dept = Organization.objects.get(name='営業部')
children = sales_dept.children.all()  # related_name='children'

# 削除済みも含めて取得
all_orgs = Organization.objects.with_deleted()

# 削除済みのみ取得
deleted_orgs = Organization.objects.only_deleted()
```

#### 更新

```python
# 組織名を変更
org = Organization.objects.get(name='営業部')
org.name = '営業本部'
org.save()

# 親組織を変更（組織の移動）
hr_dept = Organization.objects.get(name='人事部')
recruiting = Organization.objects.get(name='採用課')
recruiting.parent = hr_dept
recruiting.save()

# ルート組織に変更
org.parent = None
org.save()
```

#### 削除

**論理削除（推奨）:**
```python
org = Organization.objects.get(name='旧企画部')
org.delete()  # deleted_at に現在時刻が設定される

# 削除されたかどうか確認
print(org.is_deleted)  # True

# 注意: CASCADE により子組織も論理削除される
```

**削除の取り消し（復元）:**
```python
# 削除済み組織を取得
org = Organization.objects.with_deleted().get(name='旧企画部')

# 復元
if org.is_deleted:
    org.restore()  # deleted_at が NULL にリセットされる
```

**物理削除（非推奨）:**
```python
org = Organization.objects.get(name='営業部')
org.hard_delete()  # データベースから完全に削除される

# 注意: CASCADE により子組織も物理削除される
```

### 2. 階層操作

#### 先祖組織の取得

```python
org = Organization.objects.get(name='営業一課')
ancestors = org.get_ancestors()  # [営業部, 株式会社サンプル]

# ルート組織の取得
root = ancestors[-1] if ancestors else org
```

#### 子孫組織の取得

```python
company = Organization.objects.get(name='株式会社サンプル')
descendants = company.get_descendants()  # 全ての子孫組織

# 子孫組織数を取得
count = len(descendants)
```

#### 階層レベルの取得

```python
company = Organization.objects.get(name='株式会社サンプル')
print(company.get_level())  # 0（ルート）

sales_dept = Organization.objects.get(name='営業部')
print(sales_dept.get_level())  # 1

sales_team1 = Organization.objects.get(name='営業一課')
print(sales_team1.get_level())  # 2
```

### 3. ツリー表示

#### ツリー構造の構築

```python
from app.utils.tree import build_tree, get_tree_html

# 全組織を取得
organizations = Organization.objects.select_related('parent').all()

# ツリー用のデータを準備
org_list = [
    {
        'id': str(org.id),
        'name': org.name,
        'parent': str(org.parent.id) if org.parent else None,
    }
    for org in organizations
]

# ツリー構造を構築
tree = build_tree(org_list)

# HTML形式で表示
tree_html = get_tree_html(tree)
```

## UIフロー

### 組織一覧

URL: `/organizations/`

**表示内容:**
- 組織ツリー（階層構造を視覚的に表示）
- 組織リスト（テーブル形式）
  - 組織名
  - 親組織
  - 作成日時
  - 更新日時
  - 操作（編集・削除）

**ボタン:**
- プレビュー: 予約更新を含めた将来の組織構造を表示
- 予約更新一覧: 予約更新の一覧を表示
- 新規作成: 新しい組織を作成（ログイン必須）

### 組織作成

URL: `/organizations/new/`

**入力項目:**
- 組織名（必須）
- 親組織（任意、ドロップダウン）

### 組織編集

URL: `/organizations/{id}/edit/`

**入力項目:**
- 組織名
- 親組織

### 組織削除

URL: `/organizations/{id}/delete/`

削除前に確認画面を表示。CASCADE制約により、子組織も削除されることを警告。

### 組織プレビュー

URL: `/organizations/preview/?date=YYYY-MM-DD`

**機能:**
- 指定した日付時点での組織構造をプレビュー
- 現在のデータ + その日付までの予約更新を適用（メモリ上）
- ツリー形式で表示

## フォーム

### OrganizationForm (`app/forms.py`)

```python
class OrganizationForm(forms.ModelForm):
    """組織の作成・編集フォーム"""

    class Meta:
        model = Organization
        fields = ['name', 'parent']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '組織名を入力'}
            ),
            'parent': forms.Select(
                attrs={'class': 'form-select'}
            ),
        }
        labels = {
            'name': '組織名',
            'parent': '親組織',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False
        self.fields['parent'].queryset = Organization.objects.all()
```

## ビュー

### OrganizationListView
- **用途**: 組織一覧表示（ツリー + テーブル）
- **テンプレート**: `organizations/organization_list.html`

### OrganizationCreateView
- **用途**: 組織作成
- **テンプレート**: `organizations/organization_form.html`
- **認証**: ログイン必須

### OrganizationUpdateView
- **用途**: 組織編集
- **テンプレート**: `organizations/organization_form.html`
- **認証**: ログイン必須

### OrganizationDeleteView
- **用途**: 組織削除
- **テンプレート**: `organizations/organization_confirm_delete.html`
- **認証**: ログイン必須

### OrganizationPreviewView
- **用途**: 予約更新を含めた組織構造のプレビュー
- **テンプレート**: `organizations/organization_preview.html`
- **認証**: ログイン必須

## バリデーション

### 1. 循環参照の防止

組織が自分自身を親にすることや、子孫組織を親にすることを防ぐ必要があります。

**実装例:**
```python
from django.core.exceptions import ValidationError

def clean(self):
    """バリデーション: 循環参照の防止"""
    super().clean()

    if self.parent:
        # 自分自身を親にできない
        if self.parent == self:
            raise ValidationError({
                'parent': '組織は自分自身を親にできません。'
            })

        # 子孫組織を親にできない
        descendants = self.get_descendants()
        if self.parent in descendants:
            raise ValidationError({
                'parent': '子孫組織を親組織として指定できません。'
            })
```

**注意:** 現在の実装では、この循環参照チェックは予約更新システムの `OrganizationReservationHelper.validate_hierarchy()` に実装されています。

### 2. CASCADE削除の警告

親組織を削除すると、子組織も削除されることをユーザーに警告する必要があります。

```python
# 削除前に子組織の存在をチェック
org = Organization.objects.get(name='営業部')
if org.children.exists():
    print(f'警告: {org.children.count()}件の子組織も削除されます')
```

## 論理削除との関係

### CASCADE削除の動作

**論理削除の場合:**

親組織を論理削除すると、Django の `on_delete=models.CASCADE` は **物理削除** を試みます。

**問題点:**
```python
# 親組織を論理削除
parent_org = Organization.objects.get(name='営業部')
parent_org.delete()  # SoftDeleteModel の delete() が呼ばれる

# しかし、CASCADE により子組織は物理削除されようとする
# これは意図しない動作の可能性がある
```

**解決策:**

親組織の論理削除時に、子組織も論理削除するようにオーバーライドが必要です。

```python
class Organization(TimestampedModel, SoftDeleteModel):
    # ...

    def delete(self, using=None, keep_parents=False):
        """論理削除（子組織も論理削除）"""
        # 子組織を論理削除
        for child in self.children.all():
            child.delete()

        # 自身を論理削除
        super().delete(using=using, keep_parents=keep_parents)
```

**注意:** この実装は現在モデルに含まれていません。必要に応じて追加してください。

## 社員との関連

### PROTECT制約

組織には社員が所属しており、`Employee` モデルは `on_delete=models.PROTECT` で組織を参照しています。

**論理削除の場合:**
```python
# 社員が所属している組織を論理削除
org = Organization.objects.get(name='営業部')
org.delete()  # OK（社員との関係は維持される）

# 社員から削除済み組織を参照可能
employee = Employee.objects.get(email='yamada.taro@example.com')
print(employee.organization.name)  # '営業部'（削除済みでも参照可能）
print(employee.organization.is_deleted)  # True
```

**物理削除の場合:**
```python
# 社員が所属している組織を物理削除しようとすると ProtectedError
org = Organization.objects.get(name='営業部')
if org.employees.exists():
    org.hard_delete()  # ProtectedError が発生
```

## 予約更新システムとの統合

### 予約更新の種類

組織モデルは以下の予約更新に対応しています：

1. **作成予約**: 未来の日付で新しい組織を作成
2. **更新予約**: 組織名や親組織の変更を予約
3. **削除予約**: 組織の削除を予約

### 予約更新の作成

```python
from app.utils.organization_reservation import OrganizationReservationHelper
from datetime import date

# 2025年4月1日に新組織を作成
OrganizationReservationHelper.create_reservation(
    action='create',
    scheduled_date=date(2025, 4, 1),
    name='新事業部',
    parent=company
)

# 2025年4月1日に組織名を変更
OrganizationReservationHelper.create_reservation(
    action='update',
    scheduled_date=date(2025, 4, 1),
    organization=sales_dept,
    name='営業本部'
)

# 2025年12月31日に組織を削除
OrganizationReservationHelper.create_reservation(
    action='delete',
    scheduled_date=date(2025, 12, 31),
    organization=old_dept
)
```

詳細は [docs/reservation.md](reservation.md) を参照してください。

## 注意事項

### 1. CASCADE削除

- **論理削除**: デフォルトでは子組織は物理削除されます。子組織も論理削除する場合は `delete()` メソッドのオーバーライドが必要です
- **物理削除**: 親組織を物理削除すると、子組織も物理削除されます

### 2. 循環参照

- 組織階層で循環参照が発生しないよう、予約更新システムでバリデーションを実装しています
- 直接モデルを操作する場合は、循環参照に注意が必要です

### 3. パフォーマンス

- `get_descendants()` は再帰的にクエリを実行するため、深い階層では遅くなる可能性があります
- 大規模な組織構造では、MPTT（Modified Preorder Tree Traversal）などの階層モデルの検討も推奨されます

### 4. 論理削除の注意点

- デフォルトのクエリ（`Organization.objects.all()`）は削除済みを除外します
- 削除済みも含めて取得する場合は `with_deleted()` を使用します
- 論理削除されたレコードもディスク容量を消費します
- 詳細は [docs/soft_delete.md](soft_delete.md) を参照してください

## まとめ

組織モデルは:
- **UUID（uuid7）** をIDとして使用
- **論理削除（Soft Delete）** に対応し、データの復元が可能
- **階層構造** を隣接リストモデルで表現
- **予約更新システム** に対応し、未来の組織変更を管理
- **CASCADE制約** により、親組織削除時に子組織も削除
- **PROTECT制約** により、社員が所属する組織の物理削除を防止
- **便利メソッド** で階層操作を簡単に実装

**関連ドキュメント:**
- [論理削除の詳細](soft_delete.md)
- [社員モデル](employee.md)
- [予約更新システム](reservation.md)

将来的に、組織統合機能により、複数の組織を統合する機能も実装予定です。
