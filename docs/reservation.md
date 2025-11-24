# 汎用予約更新システム

## 概要

複数のモデル（組織、社員など）に対して、未来の日付での変更を予約できる汎用的な予約更新システムです。
更新内容をJSONB形式で保存することで、柔軟なデータ構造に対応しています。

## 主な特徴

- **汎用性**: GenericForeignKeyを使用し、任意のモデルに対応
- **依存関係管理**: 未適用の予約更新を親として指定可能（フェーズ2実装済み）
- **JSONB保存**: 更新内容をJSON形式で保存し、モデルごとの拡張が容易
- **プレビュー機能**: 指定日時点での状態をメモリ上でシミュレーション
- **バッチ適用**: 管理コマンドで一括適用

## テーブル構造

### 1. UpdateStatus（更新ステータスマスター）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| code | VARCHAR(20) | PRIMARY KEY | ステータスコード |
| name | VARCHAR(50) | NOT NULL | ステータス名 |

**データ例:**
```
code      | name
----------|------------
pending   | 予約中
applied   | 適用済み
cancelled | キャンセル済み
```

### 2. Reservation（汎用予約更新）

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | UUID | PRIMARY KEY | 予約更新ID |
| content_type_id | INTEGER | FOREIGN KEY | 対象モデルのContentType |
| object_id | UUID | NULL | 対象オブジェクトのID（新規作成時はNULL） |
| action | VARCHAR(10) | NOT NULL | 操作種別（create/update/delete） |
| data | JSONB | NOT NULL | 更新データ（モデル固有の情報） |
| depends_on_id | UUID | FOREIGN KEY (self) NULL | 依存する予約更新ID（親として使用） |
| scheduled_date | DATE | NOT NULL | 適用予定日 |
| status_id | VARCHAR(20) | FOREIGN KEY | ステータス（デフォルト: pending） |
| applied_at | TIMESTAMP | NULL | 適用日時 |
| applied_object_id | UUID | NULL | 適用後に生成されたオブジェクトID |
| created_at | TIMESTAMP | NOT NULL | 作成日時 |
| updated_at | TIMESTAMP | NOT NULL | 更新日時 |

**インデックス:**
- `idx_reservation_scheduled_status`: (scheduled_date, status_id)
- `idx_reservation_content_object`: (content_type_id, object_id)
- `idx_reservation_depends_on`: (depends_on_id)

**制約:**
- `action`: 'create', 'update', 'delete' のいずれか
- 新規作成時は `object_id` が NULL
- 更新・削除時は `object_id` が必須

## データ例

### 組織の新規作成予約

```json
{
  "id": "01234567-89ab-cdef-0123-456789abcdef",
  "content_type_id": 5,  // Organization
  "object_id": null,
  "action": "create",
  "data": {
    "name": "システム部",
    "parent_id": "existing-org-uuid"
  },
  "depends_on_id": null,
  "scheduled_date": "2025-04-01",
  "status_id": "pending",
  "applied_at": null,
  "applied_object_id": null,
  "created_at": "2025-01-15 10:00:00",
  "updated_at": "2025-01-15 10:00:00"
}
```

### 未来の組織を親とする新規作成予約

```json
{
  "id": "fedcba98-7654-3210-fedc-ba9876543210",
  "content_type_id": 5,  // Organization
  "object_id": null,
  "action": "create",
  "data": {
    "name": "開発一課"
    // parent_idは指定しない（depends_onで親を指定）
  },
  "depends_on_id": "01234567-89ab-cdef-0123-456789abcdef",  // システム部の予約
  "scheduled_date": "2025-04-01",
  "status_id": "pending",
  "applied_at": null,
  "applied_object_id": null,
  "created_at": "2025-01-15 10:05:00",
  "updated_at": "2025-01-15 10:05:00"
}
```

### 組織の更新予約

```json
{
  "id": "11111111-2222-3333-4444-555555555555",
  "content_type_id": 5,
  "object_id": "existing-org-uuid",
  "action": "update",
  "data": {
    "name": "営業部（改称後）",
    "parent_id": "new-parent-uuid"
  },
  "depends_on_id": null,
  "scheduled_date": "2025-05-01",
  "status_id": "pending",
  "applied_at": null,
  "applied_object_id": null,
  "created_at": "2025-01-15 11:00:00",
  "updated_at": "2025-01-15 11:00:00"
}
```

## アーキテクチャ

### コンポーネント構成

```
app/
├── models/
│   ├── reservation.py          # 汎用予約更新モデル
│   ├── organization.py         # 組織モデル
│   └── __init__.py
├── utils/
│   └── organization_reservation.py  # 組織用ヘルパークラス
├── forms.py                    # フォーム定義
├── views_organization.py       # 組織関連ビュー
└── management/
    └── commands/
        └── apply_organization_reservations.py  # バッチ適用コマンド
```

### 主要クラス

#### 1. Reservationモデル (`app/models/reservation.py`)

```python
class Reservation(TimestampedModel):
    """汎用予約更新データ"""

    # 対象モデルの指定（GenericForeignKey）
    content_type = models.ForeignKey(ContentType, ...)
    object_id = models.UUIDField(null=True, blank=True, ...)
    content_object = GenericForeignKey('content_type', 'object_id')

    # 操作内容
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, ...)
    data = models.JSONField(...)  # JSONB型

    # 依存関係
    depends_on = models.ForeignKey('self', null=True, blank=True, ...)

    # スケジュールとステータス
    scheduled_date = models.DateField(...)
    status = models.ForeignKey(UpdateStatus, ...)

    # 適用結果
    applied_at = models.DateTimeField(null=True, blank=True, ...)
    applied_object_id = models.UUIDField(null=True, blank=True, ...)
```

#### 2. OrganizationReservationHelper (`app/utils/organization_reservation.py`)

組織モデル専用のヘルパークラス。汎用Reservationモデルを使いやすくラップします。

**主要メソッド:**

- `create_reservation()`: 組織の予約更新を作成
- `apply_reservation()`: 予約更新を適用
- `get_pending_reservations()`: 予約中の予約更新を取得
- `format_for_display()`: 表示用にフォーマット

## 使用方法

### 1. 組織の新規作成を予約

```python
from app.utils.organization_reservation import OrganizationReservationHelper
from datetime import date

# 既存組織を親とする場合
OrganizationReservationHelper.create_reservation(
    action='create',
    scheduled_date=date(2025, 4, 1),
    name='営業部',
    parent=existing_org,  # 既存のOrganizationオブジェクト
)
# → 階層検証が自動的に実行されます

# 未来の組織を親とする場合
parent_reservation = Reservation.objects.get(...)  # 親となる予約
OrganizationReservationHelper.create_reservation(
    action='create',
    scheduled_date=date(2025, 4, 1),
    name='営業一課',
    parent_reservation=parent_reservation,  # 未適用の予約を親として指定
)
# → 循環参照チェックが自動的に実行されます
```

### 2. 組織の更新を予約

```python
OrganizationReservationHelper.create_reservation(
    action='update',
    scheduled_date=date(2025, 5, 1),
    organization=existing_org,
    name='営業部（新名称）',
    parent=new_parent_org,
)
# → 階層検証により、自己参照や循環参照が防止されます
```

### 3. 組織の削除を予約

```python
OrganizationReservationHelper.create_reservation(
    action='delete',
    scheduled_date=date(2025, 6, 1),
    organization=org_to_delete,
)
```

### 4. バッチ適用（トポロジカルソート統合版）

```bash
# 今日までの予約を適用
python manage.py apply_organization_reservations
# → 依存関係を自動解決し、最適な順序で適用されます

# 特定日までの予約を適用
python manage.py apply_organization_reservations --date 2025-04-01

# ドライラン（適用せずに確認のみ）
python manage.py apply_organization_reservations --dry-run
# → 適用順序を事前に確認できます
```

**バッチコマンドの出力例:**
```
適用対象日: 2025-04-01
適用対象: 5件
依存関係を解決しました
✓ [1/5] 適用完了: [新規作成] システム部
✓ [2/5] 適用完了: [新規作成] 開発一課
✓ [3/5] 適用完了: [新規作成] 開発二課
✓ [4/5] 適用完了: [更新] 営業部
✓ [5/5] 適用完了: [削除] 廃止予定組織

処理完了: 成功 5件 / 失敗 0件
```

## 依存関係の処理

### フェーズ3実装（最新版）✨

**実装済み機能:**
- ✅ `depends_on` フィールドで親予約を指定
- ✅ 適用時に `applied_object_id` を使用して親組織を設定
- ✅ **トポロジカルソートによる自動順序決定**
- ✅ **循環参照の自動検出とエラー表示**
- ✅ **組織階層の検証（自己参照・循環参照防止）**

**新機能の詳細:**

1. **循環参照チェック (`check_circular_dependency`)**
   - 予約作成時に自動的に循環参照をチェック
   - 循環参照が検出された場合は `ValueError` を発生
   - 例: A → B → C → A のような依存関係を防止

2. **トポロジカルソート (`topological_sort`)**
   - Kahn's アルゴリズムを使用して依存関係を自動解決
   - 適用順序を自動的に決定（手動での順序管理が不要）
   - 予定日と作成日時を考慮した最適な順序

3. **組織階層検証 (`validate_hierarchy`)**
   - 自己参照の防止（組織が自分自身を親にできない）
   - 循環参照の防止（子孫組織を親に設定できない）
   - 予約作成時に自動的に検証

**動作フロー:**
```
1. システム部の予約作成（depends_on: null）
   ↓ 循環参照チェック: OK
   ↓
2. 開発一課の予約作成（depends_on: システム部の予約ID）
   ↓ 循環参照チェック: OK
   ↓
3. バッチ適用実行
   ↓ トポロジカルソート実行
   ↓ 依存関係を解決し、適用順序を自動決定
   ↓
4. システム部を作成 → applied_object_id に組織IDを保存
   ↓
5. 開発一課を作成 → depends_on.applied_object_id から親を取得
```

**エラー検出例:**
```python
# 循環参照の例
予約A (depends_on: 予約B)
予約B (depends_on: 予約C)
予約C (depends_on: 予約A)  # エラー: 循環参照が検出されました

# 自己参照の例
組織を更新して、自分自身を親に設定  # エラー: 組織は自分自身を親にできません
```

## UIフロー

### 予約更新の作成

1. 予約更新一覧画面で「予約更新を作成」ボタンをクリック
2. フォーム入力:
   - 操作種別: 新規作成/更新/削除
   - 対象組織: （更新・削除の場合のみ）
   - 組織名: （新規作成・更新の場合）
   - **親組織（既存）**: 既存の組織から選択
   - **親組織（未来の予約）**: 未適用の新規作成予約から選択
   - 適用予定日
3. 保存
4. 一覧画面に戻る

### 予約更新一覧の表示

- 操作種別をカラーバッジで表示:
  - 新規作成: 緑
  - 更新: 青
  - 削除: 赤
- ステータスをバッジで表示:
  - 予約中: 黄
  - 適用済み: 緑
  - キャンセル済み: 灰
- 親組織の表示:
  - 既存組織: 組織名
  - 未来の予約: 「未来: システム部」（青バッジ）

### プレビュー機能

指定日時点での組織構造をツリー表示。未適用の予約更新も含めてシミュレーション。

## 実装済み: 社員モデルへの拡張

社員モデルに対する予約更新機能が実装済みです。

### 実装内容

#### 1. ヘルパークラス (`app/utils/employee_reservation.py`)

```python
class EmployeeReservationHelper:
    """社員予約更新のヘルパークラス"""

    @staticmethod
    def get_content_type():
        """社員のContentTypeを取得"""
        return ContentType.objects.get_for_model(Employee)

    @staticmethod
    def create_reservation(action, scheduled_date, employee=None,
                          name=None, email=None, organization=None):
        """社員の予約更新を作成"""
        content_type = EmployeeReservationHelper.get_content_type()

        data = {}
        if name:
            data['name'] = name
        if email:
            data['email'] = email
        if organization:
            data['organization_id'] = str(organization.id)
        elif organization is None and action in [Reservation.ACTION_CREATE, Reservation.ACTION_UPDATE]:
            data['organization_id'] = None

        return Reservation.objects.create(
            content_type=content_type,
            object_id=employee.id if employee else None,
            action=action,
            data=data,
            scheduled_date=scheduled_date,
            status_id=UpdateStatus.PENDING,
        )

    @staticmethod
    def apply_reservation(reservation):
        """予約更新を適用"""
        if reservation.action == Reservation.ACTION_CREATE:
            employee = Employee.objects.create(
                name=reservation.data['name'],
                email=reservation.data['email'],
                organization_id=reservation.data.get('organization_id'),
            )
            reservation.applied_object_id = employee.id
        elif reservation.action == Reservation.ACTION_UPDATE:
            employee = Employee.objects.get(id=reservation.object_id)
            if 'name' in reservation.data:
                employee.name = reservation.data['name']
            if 'email' in reservation.data:
                employee.email = reservation.data['email']
            if 'organization_id' in reservation.data:
                employee.organization_id = reservation.data['organization_id']
            employee.save()
        elif reservation.action == Reservation.ACTION_DELETE:
            employee = Employee.objects.get(id=reservation.object_id)
            employee.delete()

        reservation.status_id = UpdateStatus.APPLIED
        reservation.applied_at = timezone.now()
        reservation.save()

    @staticmethod
    def get_pending_reservations(scheduled_date=None):
        """予約中の社員予約更新を取得"""
        content_type = EmployeeReservationHelper.get_content_type()
        queryset = Reservation.objects.filter(
            content_type=content_type,
            status_id=UpdateStatus.PENDING,
        )
        if scheduled_date:
            queryset = queryset.filter(scheduled_date__lte=scheduled_date)
        return queryset.order_by('scheduled_date', 'created_at')

    @staticmethod
    def format_for_display(reservation):
        """予約更新を表示用にフォーマット"""
        # 表示用のデータを整形して返却
        # ...
```

#### 2. フォーム (`app/forms.py`)

```python
class EmployeeReservationForm(forms.Form):
    """社員予約更新フォーム"""

    ACTION_CHOICES = [
        ('create', '新規作成'),
        ('update', '更新'),
        ('delete', '削除'),
    ]

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        label='対象社員',
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label='操作種別',
    )
    name = forms.CharField(
        max_length=200,
        required=False,
        label='氏名',
    )
    email = forms.EmailField(
        required=False,
        label='メールアドレス',
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label='所属組織',
    )
    scheduled_date = forms.DateField(
        label='適用予定日',
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        employee = cleaned_data.get('employee')
        name = cleaned_data.get('name')
        email = cleaned_data.get('email')

        if action == 'create':
            if not name or not email:
                raise forms.ValidationError('新規作成の場合、氏名とメールアドレスは必須です。')
        elif action in ['update', 'delete']:
            if not employee:
                raise forms.ValidationError('更新/削除の場合、対象社員は必須です。')
        return cleaned_data
```

#### 3. ビュー (`app/views/employee.py`)

```python
class EmployeeReservationListView(LoginRequiredMixin, View):
    """社員予約更新一覧ビュー"""
    # 全ステータスの予約を取得し表示

class EmployeeReservationCreateView(LoginRequiredMixin, View):
    """社員予約更新作成ビュー"""
    # フォームから予約を作成

class EmployeeReservationUpdateView(LoginRequiredMixin, View):
    """社員予約更新編集ビュー"""
    # 予約中の予約を編集

class EmployeeReservationDeleteView(LoginRequiredMixin, DeleteView):
    """社員予約更新削除（キャンセル）ビュー"""
    # 予約をキャンセル（ステータス変更）

class EmployeePreviewView(LoginRequiredMixin, View):
    """社員プレビュービュー"""
    # 指定日時点での社員情報を予約更新を含めて表示
```

#### 4. URL設定 (`app/urls.py`)

```python
# 社員予約更新関連
path('employees/reservations/',
     views.EmployeeReservationListView.as_view(),
     name='employee_reservation_list'),
path('employees/reservations/new/',
     views.EmployeeReservationCreateView.as_view(),
     name='employee_reservation_create'),
path('employees/reservations/<uuid:pk>/edit/',
     views.EmployeeReservationUpdateView.as_view(),
     name='employee_reservation_update'),
path('employees/reservations/<uuid:pk>/delete/',
     views.EmployeeReservationDeleteView.as_view(),
     name='employee_reservation_delete'),
path('employees/preview/',
     views.EmployeePreviewView.as_view(),
     name='employee_preview'),
```

### 使用方法

#### 社員の新規作成を予約

```python
from app.utils.employee_reservation import EmployeeReservationHelper
from datetime import date

EmployeeReservationHelper.create_reservation(
    action='create',
    scheduled_date=date(2025, 4, 1),
    name='山田太郎',
    email='yamada.taro@example.com',
    organization=org,  # Organizationオブジェクト
)
```

#### 社員情報の更新を予約

```python
EmployeeReservationHelper.create_reservation(
    action='update',
    scheduled_date=date(2025, 5, 1),
    employee=existing_employee,
    name='山田次郎',  # 名前変更
    organization=new_org,  # 組織異動
)
```

#### 社員の退職を予約（削除）

```python
EmployeeReservationHelper.create_reservation(
    action='delete',
    scheduled_date=date(2025, 6, 30),
    employee=employee_to_retire,
)
```

### UIフロー

#### 予約更新一覧
- URL: `/employees/reservations/`
- ヘッダーの「社員」メニュー → 「社員の予約更新」からアクセス
- 表示内容:
  - 操作種別（新規作成/更新/削除）
  - 対象社員
  - 氏名・メールアドレス・所属組織
  - 適用予定日
  - ステータス（予約中/適用済み/キャンセル済み）
  - 操作ボタン（編集/キャンセル）

#### 予約更新の作成
- URL: `/employees/reservations/new/`
- 予約更新一覧から「予約更新を作成」ボタンでアクセス
- 入力項目:
  - 操作種別: 新規作成/更新/削除（必須）
  - 対象社員: （更新・削除の場合のみ必須）
  - 氏名: （新規作成・更新の場合）
  - メールアドレス: （新規作成・更新の場合）
  - 所属組織: （任意、ドロップダウン）
  - 適用予定日: （必須）

#### プレビュー機能
- URL: `/employees/preview/?date=YYYY-MM-DD`
- 予約更新一覧から「プレビュー」ボタンでアクセス
- 機能:
  - 指定日時点での社員一覧を表示
  - 予約更新（新規作成/更新/削除）をメモリ上でシミュレーション
  - 新規作成予定の社員は水色でハイライト表示
  - 日付選択フォームで任意の日付を確認可能

### データ例

#### 社員の新規作成予約

```json
{
  "id": "employee-reservation-uuid",
  "content_type_id": 6,  // Employee
  "object_id": null,
  "action": "create",
  "data": {
    "name": "山田太郎",
    "email": "yamada.taro@example.com",
    "organization_id": "org-uuid"
  },
  "depends_on_id": null,
  "scheduled_date": "2025-04-01",
  "status_id": "pending",
  "applied_at": null,
  "applied_object_id": null
}
```

#### 社員情報の更新予約（組織異動）

```json
{
  "id": "employee-update-uuid",
  "content_type_id": 6,
  "object_id": "existing-employee-uuid",
  "action": "update",
  "data": {
    "organization_id": "new-org-uuid"
  },
  "depends_on_id": null,
  "scheduled_date": "2025-04-01",
  "status_id": "pending",
  "applied_at": null,
  "applied_object_id": null
}
```

### 特徴

- **組織との連携**: 組織の予約更新と同様に、社員の組織異動を予約可能
- **プレビュー機能**: 予約更新適用後の社員一覧を事前確認
- **キャンセル機能**: 適用前であればキャンセル可能（ステータス変更）
- **組織と同じUI/UX**: 組織の予約更新機能と統一されたインターフェース

### 組織予約更新との違い

| 項目 | 組織 | 社員 |
|------|------|------|
| 操作種別 | 新規作成/更新/削除/統合 | 新規作成/更新/削除 |
| 階層構造 | あり（親子関係） | なし |
| depends_on | 使用可能（未来の組織を親指定） | 使用しない |
| プレビュー表示 | ツリー表示 | テーブル表示 |
| 依存関係解決 | トポロジカルソート必要 | 順序関係なし |

## 他のモデルへの拡張方法

上記の社員モデルの実装例を参考に、他のモデルにも同様のパターンで予約更新機能を追加できます。

### 拡張手順

1. ヘルパークラスの作成 (`app/utils/{model}_reservation.py`)
2. フォームの作成 (`app/forms.py`)
3. ビューの実装 (`app/views/{model}.py`)
4. URLパターンの追加 (`app/urls.py`)
5. テンプレートの作成 (`app/templates/{model}/reservations/`)
6. ヘッダーメニューへのリンク追加 (`templates/base/base.html`)

## データ構造設計の利点

### 1. JSONB使用の利点

- **柔軟性**: モデルごとに異なるフィールドを保存可能
- **拡張性**: 新しいフィールド追加時にマイグレーション不要
- **クエリ性能**: PostgreSQLのJSONB型はインデックス化可能

### 2. GenericForeignKey使用の利点

- **汎用性**: 単一テーブルで複数モデルに対応
- **保守性**: 予約更新の共通ロジックを一元管理
- **一覧性**: すべての予約更新を横断的に管理可能

### 3. ヘルパークラスパターン

- **分離**: モデル固有のロジックをヘルパーに集約
- **再利用**: 共通の予約更新ロジックを共有
- **テスト**: モデルごとに独立してテスト可能

## 注意事項

### 1. トランザクション管理

バッチ適用時は全体をトランザクション内で実行。一部失敗時はロールバック。

### 2. 依存関係の順序

現在（フェーズ2）は手動での順序管理が必要:
- 親となる予約を先に作成
- 同じ適用日の場合、作成順に適用される

### 3. データ整合性

- 適用前の検証が重要
- ドライランモードでの事前確認を推奨

### 4. パフォーマンス

- 大量の予約更新は一括処理で効率化
- プレビュー機能は全データをメモリに展開（組織数に注意）

## まとめ

この汎用予約更新システムは:
- **JSONB + GenericForeignKey** で柔軟性と汎用性を実現
- **depends_on フィールド** で未来の組織を親として指定可能
- **トポロジカルソート（フェーズ3実装済み）** で複雑な依存関係を自動解決
- **循環参照検出** により不正なデータを事前防止
- **組織階層検証** で自己参照や循環参照を防止
- **ヘルパークラスパターン** でモデル固有のロジックをカプセル化
- **他モデルへの拡張が容易** な設計

## 実装済み機能のまとめ

### ✅ フェーズ1: 基本機能
- 汎用予約更新モデル（GenericForeignKey使用）
- JSONB形式でのデータ保存
- 基本的なCRUD操作

### ✅ フェーズ2: 依存関係の基礎
- `depends_on` フィールドによる親子関係の管理
- `applied_object_id` による適用後オブジェクトの追跡
- 予定日と作成日時による基本的なソート

### ✅ フェーズ3: 高度な依存関係管理（最新実装）
- **循環参照チェック機能** (`check_circular_dependency`)
- **トポロジカルソート** (`topological_sort`)
- **組織階層検証** (`validate_hierarchy`)
- **バッチコマンドの依存関係自動解決**
- **エラーハンドリングの強化**

これにより、組織改変などの複雑な業務要件にも柔軟に対応できる、堅牢な予約更新システムが完成しました。
