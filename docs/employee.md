# 社員モデル

## 概要

社員情報を管理するモデル。組織に所属する社員の基本情報（氏名、メールアドレス）を保持します。

**論理削除対応:** このモデルは論理削除（Soft Delete）に対応しており、削除されたレコードは物理的には保持されます。詳細は [docs/soft_delete.md](soft_delete.md) を参照してください。

## テーブル構造

### Employee（社員）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PRIMARY KEY | 社員ID（uuid7） |
| name | VARCHAR(200) | NOT NULL | 氏名 |
| email | VARCHAR(254) | NOT NULL | メールアドレス |
| organization_id | UUID | FOREIGN KEY, NULL | 所属組織ID（NULL=未所属） |
| deleted_at | TIMESTAMP | NULL | 削除日時（論理削除） |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- `idx_employee_organization`: (organization_id)
- `idx_employee_email`: (email)
- `idx_employee_deleted_at`: (deleted_at)

**制約:**
- `email`: アプリケーション側でユニーク制約（論理削除されていない社員のみ）
- `organization`: PROTECT制約（組織の物理削除時、社員が存在する場合削除できない）
- `organization` が NULL の場合は未所属社員となる

## データ例

### 有効な社員（deleted_at が NULL）
```json
{
  "id": "01234567-89ab-cdef-0123-456789abcdef",
  "name": "山田太郎",
  "email": "yamada.taro@example.com",
  "organization_id": "fedcba98-7654-3210-fedc-ba9876543210",
  "deleted_at": null,
  "created_at": "2025-01-15 10:00:00",
  "updated_at": "2025-01-15 10:00:00"
}
```

### 未所属の社員（organization_id が NULL）
```json
{
  "id": "abcdef12-3456-7890-abcd-ef1234567890",
  "name": "佐藤次郎",
  "email": "sato.jiro@example.com",
  "organization_id": null,
  "deleted_at": null,
  "created_at": "2025-01-20 14:00:00",
  "updated_at": "2025-01-20 14:00:00"
}
```

### 削除済み社員（deleted_at に日時が設定）
```json
{
  "id": "98765432-10fe-dcba-9876-543210fedcba",
  "name": "田中花子",
  "email": "tanaka.hanako@example.com",
  "organization_id": "fedcba98-7654-3210-fedc-ba9876543210",
  "deleted_at": "2025-02-01 15:30:00",
  "created_at": "2025-01-10 09:00:00",
  "updated_at": "2025-02-01 15:30:00"
}
```

## モデル定義

### Employeeモデル (`app/models/employee.py`)

```python
from uuid import uuid7
from django.core.exceptions import ValidationError
from django.db import models
from .base import TimestampedModel, SoftDeleteModel

class Employee(TimestampedModel, SoftDeleteModel):
    """社員モデル"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='氏名'
    )
    email = models.EmailField(
        verbose_name='メールアドレス'
    )
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
```

**主要な変更点:**
- `SoftDeleteModel` を継承し、論理削除機能を追加
- `email` フィールドから `unique=True` を削除（DB制約を解除）
- `clean()` メソッドでアプリケーション側のユニーク制約を実装
- `save()` メソッドで保存前に必ず `full_clean()` を実行

## 主要機能

### 1. CRUD操作

#### 作成
```python
from app.models import Employee, Organization

org = Organization.objects.get(name='営業部')
employee = Employee.objects.create(
    name='山田太郎',
    email='yamada.taro@example.com',
    organization=org
)
```

#### 読み取り
```python
# 全社員取得（論理削除されていない社員のみ）
employees = Employee.objects.all()

# 特定組織の社員取得
org_employees = Employee.objects.filter(organization=org)

# メールアドレスで検索
employee = Employee.objects.get(email='yamada.taro@example.com')

# 削除済みも含めて取得
all_employees = Employee.objects.with_deleted()

# 削除済みのみ取得
deleted_employees = Employee.objects.only_deleted()
```

#### 更新
```python
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.name = '山田次郎'
employee.save()

# 組織異動
new_org = Organization.objects.get(name='人事部')
employee.organization = new_org
employee.save()
```

#### 削除

**論理削除（推奨）:**
```python
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.delete()  # deleted_at に現在時刻が設定される

# 削除されたかどうか確認
print(employee.is_deleted)  # True
```

**削除の取り消し（復元）:**
```python
# 削除済み社員を取得
employee = Employee.objects.with_deleted().get(email='yamada.taro@example.com')

# 復元
if employee.is_deleted:
    employee.restore()  # deleted_at が NULL にリセットされる
```

**物理削除（非推奨）:**
```python
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.hard_delete()  # データベースから完全に削除される
```

### 2. リレーション

#### 組織から社員を取得
```python
org = Organization.objects.get(name='営業部')
employees = org.employees.all()  # related_name='employees'

# 社員数を取得
employee_count = org.employees.count()
```

#### 社員から組織を取得
```python
employee = Employee.objects.get(email='yamada.taro@example.com')
org = employee.organization
print(org.name)  # '営業部'
```

## UIフロー

### 社員一覧

URL: `/employees/`

**表示内容:**
- 氏名
- メールアドレス
- 所属組織
- 操作（編集・削除）

### 社員作成

URL: `/employees/new/`

**入力項目:**
- 氏名（必須）
- メールアドレス（必須、ユニーク）
- 所属組織（必須、ドロップダウン）

### 社員編集

URL: `/employees/{id}/edit/`

**入力項目:**
- 氏名
- メールアドレス
- 所属組織

### 社員削除

URL: `/employees/{id}/delete/`

削除前に確認画面を表示

## フォーム

### EmployeeForm (`app/forms.py`)

```python
class EmployeeForm(forms.ModelForm):
    """社員の作成・編集フォーム"""

    class Meta:
        model = Employee
        fields = ['name', 'email', 'organization']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '氏名を入力'}
            ),
            'email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'メールアドレスを入力'}
            ),
            'organization': forms.Select(
                attrs={'class': 'form-select'}
            ),
        }
        labels = {
            'name': '氏名',
            'email': 'メールアドレス',
            'organization': '所属組織',
        }
```

## ビュー

### EmployeeListView
- **用途**: 社員一覧表示
- **テンプレート**: `employees/employee_list.html`

### EmployeeCreateView
- **用途**: 社員作成
- **テンプレート**: `employees/employee_form.html`
- **認証**: ログイン必須

### EmployeeUpdateView
- **用途**: 社員編集
- **テンプレート**: `employees/employee_form.html`
- **認証**: ログイン必須

### EmployeeDeleteView
- **用途**: 社員削除
- **テンプレート**: `employees/employee_confirm_delete.html`
- **認証**: ログイン必須

## バリデーション

### 1. メールアドレスのユニーク制約（論理削除対応）

**アプリケーション側で制御:**

メールアドレスの重複チェックは、論理削除されていない社員のみを対象に行われます。

```python
# 有効な社員の中で重複したメールアドレスは登録不可
from django.core.exceptions import ValidationError

try:
    Employee.objects.create(
        name='田中花子',
        email='yamada.taro@example.com',  # 既存の有効な社員のメール
        organization=org
    )
except ValidationError as e:
    print(e.message_dict)  # {'email': ['このメールアドレスは既に使用されています。']}
```

**論理削除された社員のメールアドレスは再利用可能:**

```python
# 社員を論理削除
employee1 = Employee.objects.get(email='yamada.taro@example.com')
employee1.delete()  # 論理削除

# 同じメールアドレスで新しい社員を登録可能
employee2 = Employee.objects.create(
    name='山田次郎',
    email='yamada.taro@example.com',  # OK（employee1は削除済み）
    organization=org
)
```

**注意:** DB側のユニーク制約は削除されており、アプリケーション側の `clean()` メソッドでバリデーションを実装しています。

### 2. 組織削除時の保護

**論理削除の場合:**

```python
# 社員が所属している組織を論理削除
org = Organization.objects.get(name='営業部')
if org.employees.exists():
    org.delete()  # 組織が論理削除される（社員との関係は維持）
```

組織が論理削除された場合も、社員との外部キー関係は物理的に保持されます。

**物理削除の場合:**

```python
# 社員が所属している組織を物理削除しようとすると ProtectedError
org = Organization.objects.get(name='営業部')
if org.employees.exists():
    org.hard_delete()  # ProtectedError が発生
```

## 組織との関連

### 論理削除時の動作

**組織を論理削除すると、所属社員は未所属になります:**

```python
# 組織を論理削除
org = Organization.objects.get(name='営業部')
employees = org.employees.all()  # [山田太郎, 田中花子, ...]

org.delete()  # 論理削除を実行

# 所属社員は未所属になる（organization が NULL に設定される）
for employee in employees:
    employee.refresh_from_db()
    print(employee.organization)  # None（未所属化）

# 組織自体は論理削除される
org.refresh_from_db()
print(org.is_deleted)  # True
```

**未所属社員の取得:**

```python
# 未所属の社員を取得
unaffiliated_employees = Employee.objects.filter(organization__isnull=True)

# 所属組織がある社員のみ取得
affiliated_employees = Employee.objects.filter(organization__isnull=False)
```

**組織と社員を一緒に論理削除:**

```python
# 組織に所属する全社員を論理削除
org = Organization.objects.get(name='営業部')
org.employees.all().delete()  # 全社員を論理削除

# 組織も論理削除
org.delete()
```

### 物理削除時の制約

組織を物理削除する場合、PROTECT制約により社員が存在すると削除できません。

```python
# 正しい物理削除手順
org = Organization.objects.get(name='営業部')

# 1. 社員を他の組織に異動させる
new_org = Organization.objects.get(name='人事部')
for employee in org.employees.all():
    employee.organization = new_org
    employee.save()

# 2. 組織を物理削除
org.hard_delete()
```

または

```python
# 社員ごと物理削除する場合
org = Organization.objects.get(name='営業部')
for employee in org.employees.all():
    employee.hard_delete()  # 物理削除

org.hard_delete()  # 組織を物理削除
```

## 将来の拡張

### 予約更新システムとの統合

社員の組織異動を未来の日付で予約できるようにする予定。

**実装予定機能:**
- 社員の組織異動予約
- 社員情報の更新予約
- 社員の退職予約（削除）

**例:**
```python
# 2025年4月1日に山田太郎を人事部に異動
EmployeeReservationHelper.create_reservation(
    action='update',
    scheduled_date=date(2025, 4, 1),
    employee=employee,
    organization=new_org
)
```

## 注意事項

### 1. メールアドレスの一意性（論理削除対応）

- **有効な社員のメールアドレスは一意である必要があります**
- 論理削除された社員のメールアドレスは再利用可能です
- アプリケーション側のバリデーションで制御しています（DB制約ではない）

### 2. 組織との関連

- 社員は組織に所属することができます（NULL 許可）
- 所属組織が論理削除されると、社員は未所属（organization=NULL）になります
- 未所属の社員も作成可能です

### 3. データ整合性

- **論理削除**: 組織が論理削除されると、所属社員の organization は NULL になります
- **物理削除**: `PROTECT` 制約により、所属社員が存在する場合は組織を物理削除できません
- 論理削除されたレコードもテーブルに残るため、定期的なクリーンアップが推奨されます

### 4. 論理削除の注意点

- デフォルトのクエリ（`Employee.objects.all()`）は削除済みを除外します
- 削除済みも含めて取得する場合は `with_deleted()` を使用します
- 論理削除されたレコードもディスク容量を消費します
- 詳細は [docs/soft_delete.md](soft_delete.md) を参照してください

## まとめ

社員モデルは:
- **UUID（uuid7）** をIDとして使用
- **論理削除（Soft Delete）** に対応し、データの復元が可能
- **メールアドレスのアプリケーション側バリデーション** で有効な社員の一意性を確保
- **PROTECT制約** で組織との整合性を維持（物理削除時）
- **NULL許可の組織フィールド** により未所属社員をサポート
- **組織の論理削除時に自動的に未所属化** される
- **SoftDeleteModel継承** により、削除済みレコードの管理が容易
- **予約更新システムとの統合** を想定した設計

**関連ドキュメント:**
- [論理削除の詳細](soft_delete.md)
- [組織モデル](organization.md)（未作成）
- [予約更新システム](reservation.md)

将来的に、組織統合機能と連携して、社員の自動移動なども実装予定です。
