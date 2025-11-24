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

# 未来の組織を親とする場合
parent_reservation = Reservation.objects.get(...)  # 親となる予約
OrganizationReservationHelper.create_reservation(
    action='create',
    scheduled_date=date(2025, 4, 1),
    name='営業一課',
    parent_reservation=parent_reservation,  # 未適用の予約を親として指定
)
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
```

### 3. 組織の削除を予約

```python
OrganizationReservationHelper.create_reservation(
    action='delete',
    scheduled_date=date(2025, 6, 1),
    organization=org_to_delete,
)
```

### 4. バッチ適用

```bash
# 今日までの予約を適用
python manage.py apply_organization_reservations

# 特定日までの予約を適用
python manage.py apply_organization_reservations --date 2025-04-01

# ドライラン（適用せずに確認のみ）
python manage.py apply_organization_reservations --dry-run
```

## 依存関係の処理

### フェーズ2実装（現在）

**特徴:**
- `depends_on` フィールドで親予約を指定
- 適用時に `applied_object_id` を使用して親組織を設定
- 作成順と適用予定日でソート

**制限事項:**
- 手動での順序管理が必要（親を先に作成）
- 循環参照のチェックなし
- 複雑な依存関係では順序が保証されない可能性

**動作フロー:**
```
1. システム部の予約作成（depends_on: null）
   ↓
2. 開発一課の予約作成（depends_on: システム部の予約ID）
   ↓
3. バッチ適用実行
   ↓
4. システム部を作成 → applied_object_id に組織IDを保存
   ↓
5. 開発一課を作成 → depends_on.applied_object_id から親を取得
```

### フェーズ3（将来実装予定）

トポロジカルソートと循環参照検出を実装予定。

**実装予定機能:**
- 依存グラフの自動構築
- トポロジカルソートによる適用順序の自動決定
- 循環参照の検出とエラー表示

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

## 他のモデルへの拡張方法

### 例: 社員モデルへの拡張

#### 1. ヘルパークラスの作成

```python
# app/utils/employee_reservation.py

from django.contrib.contenttypes.models import ContentType
from app.models import Employee, Reservation, UpdateStatus

class EmployeeReservationHelper:
    """社員予約更新のヘルパークラス"""

    @staticmethod
    def get_content_type():
        return ContentType.objects.get_for_model(Employee)

    @staticmethod
    def create_reservation(action, scheduled_date, employee=None,
                          name=None, department=None, position=None):
        content_type = EmployeeReservationHelper.get_content_type()

        data = {}
        if name:
            data['name'] = name
        if department:
            data['department_id'] = str(department.id)
        if position:
            data['position'] = position

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
        # 社員固有の適用ロジック
        if reservation.action == Reservation.ACTION_CREATE:
            employee = Employee.objects.create(
                name=reservation.data['name'],
                department_id=reservation.data.get('department_id'),
                position=reservation.data.get('position'),
            )
            reservation.applied_object_id = employee.id
        # ... 以下略
```

#### 2. フォームの作成

```python
# app/forms.py

class EmployeeReservationForm(forms.Form):
    employee = forms.ModelChoiceField(...)
    action = forms.ChoiceField(...)
    name = forms.CharField(...)
    department = forms.ModelChoiceField(...)
    position = forms.CharField(...)
    scheduled_date = forms.DateField(...)
```

#### 3. ビューとテンプレートの追加

組織と同様のパターンでビューとテンプレートを作成。

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
- **depends_on フィールド** で未来の組織を親として指定可能（フェーズ2実装済み）
- **ヘルパークラスパターン** でモデル固有のロジックをカプセル化
- **他モデルへの拡張が容易** な設計

将来的にトポロジカルソート（フェーズ3）を実装することで、より複雑な依存関係にも対応可能です。
