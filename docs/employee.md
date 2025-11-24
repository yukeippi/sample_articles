# 社員モデル

## 概要

社員情報を管理するモデル。組織に所属する社員の基本情報（氏名、メールアドレス）を保持します。

## テーブル構造

### Employee（社員）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PRIMARY KEY | 社員ID（uuid7） |
| name | VARCHAR(200) | NOT NULL | 氏名 |
| email | VARCHAR(254) | NOT NULL, UNIQUE | メールアドレス |
| organization_id | UUID | FOREIGN KEY, NOT NULL | 所属組織ID |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- `idx_employee_organization`: (organization_id)
- `idx_employee_email`: (email)

**制約:**
- `email`: ユニーク制約（重複不可）
- `organization`: PROTECT制約（組織削除時は社員が存在する場合削除できない）

## データ例

```json
{
  "id": "01234567-89ab-cdef-0123-456789abcdef",
  "name": "山田太郎",
  "email": "yamada.taro@example.com",
  "organization_id": "fedcba98-7654-3210-fedc-ba9876543210",
  "created_at": "2025-01-15 10:00:00",
  "updated_at": "2025-01-15 10:00:00"
}
```

## モデル定義

### Employeeモデル (`app/models/employee.py`)

```python
from uuid import uuid7
from django.db import models
from .base import TimestampedModel

class Employee(TimestampedModel):
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
        unique=True,
        verbose_name='メールアドレス'
    )
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

    def __str__(self):
        return f'{self.name} ({self.email})'
```

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
# 全社員取得
employees = Employee.objects.all()

# 特定組織の社員取得
org_employees = Employee.objects.filter(organization=org)

# メールアドレスで検索
employee = Employee.objects.get(email='yamada.taro@example.com')
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
```python
employee = Employee.objects.get(email='yamada.taro@example.com')
employee.delete()
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

### 1. メールアドレスのユニーク制約

```python
# 重複したメールアドレスは登録不可
try:
    Employee.objects.create(
        name='田中花子',
        email='yamada.taro@example.com',  # 既存のメール
        organization=org
    )
except IntegrityError:
    print('このメールアドレスは既に使用されています')
```

### 2. 組織削除時の保護

```python
# 社員が所属している組織は削除不可
org = Organization.objects.get(name='営業部')
if org.employees.exists():
    # ProtectedError が発生
    org.delete()  # エラー: 社員が所属しているため削除できません
```

## 組織との関連

### 組織削除の制約

社員が所属している組織を削除しようとすると、`ProtectedError` が発生します。

```python
# 正しい削除手順
org = Organization.objects.get(name='営業部')

# 1. 社員を他の組織に異動させる
new_org = Organization.objects.get(name='人事部')
for employee in org.employees.all():
    employee.organization = new_org
    employee.save()

# 2. 組織を削除
org.delete()
```

または

```python
# 社員ごと削除する場合
org = Organization.objects.get(name='営業部')
org.employees.all().delete()  # 先に社員を削除
org.delete()  # 組織を削除
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

### 1. メールアドレスの一意性

- メールアドレスは全社員で一意である必要があります
- 同じメールアドレスで複数の社員を登録することはできません

### 2. 組織との関連

- 社員は必ず一つの組織に所属している必要があります
- 所属組織がない社員は作成できません
- 組織を削除する前に、所属している社員を他の組織に異動させるか、削除する必要があります

### 3. データ整合性

- 組織削除時は `PROTECT` 制約により、所属社員が存在する場合はエラーになります
- これにより、データの整合性が保たれます

## まとめ

社員モデルは:
- **UUID（uuid7）** をIDとして使用
- **メールアドレスのユニーク制約** でデータ整合性を確保
- **PROTECT制約** で組織との整合性を維持
- **シンプルな設計** で拡張性を確保
- **予約更新システムとの統合** を想定した設計

将来的に、組織統合機能と連携して、社員の自動移動なども実装予定です。
