# Django Article & Comment System

シンプルな記事・コメント投稿システムのDjangoプロジェクトです。

## プロジェクト概要

このプロジェクトは、ユーザーが記事を投稿し、それに対してコメントを付けられるシステムです。

## このアプリで試していること
- アプリケーションをディレクトリに分けずに一つで開発する構成
- idをUUIDにした場合の作り方
- ログレベルの調整
- コンソールによるデータ操作（rails consoleの様な）
- AppRunnerへのデプロイ用actions
- デバッガ
- 更新履歴管理
- データベース周りの操作（マイグレーションファイルの中身、ロールバック操作など）
- ORMの使い方
- カラム構成のルール策定
- 操作履歴

## 技術スタック

- **Python**: 3.14+
- **Django**: 5.2.8+
- **PostgreSQL**: データベース
- **開発ツール**:
  - django-environ: 環境変数管理
  - django-extensions: shell_plusなど便利な拡張機能
  - ipython: インタラクティブシェル

## データモデル

### Article（記事）
- `id`: UUID (uuid7)
- `title`: 記事タイトル
- `content`: 本文
- `user`: 投稿者（User外部キー）
- `created_at`: 作成日時（インデックス付き）
- `updated_at`: 更新日時

### Comment（コメント）
- `id`: UUID (uuid7)
- `article`: 記事（Article外部キー）
- `user`: 投稿者（User外部キー）
- `content`: コメント内容
- `created_at`: 作成日時（インデックス付き）
- `updated_at`: 更新日時

## 開発履歴

### 2025-11-08

#### 初期セットアップ
- **初期環境構築** (19:17)
  - プロジェクトの基本構造を作成

- **Django初期環境構築** (20:02)
  - Djangoプロジェクトの初期設定
  - PostgreSQLとの接続設定

- **HelloWorldを表示** (20:28)
  - 動作確認用のシンプルなビューを実装

#### モデル設計
- **モデルを階層構造で作ってみる** (20:47)
  - `app/models/`ディレクトリ構造を導入
  - 初期のArticleモデルを作成

- **デフォルトでcreated_atにインデックスを付与するように改修** (21:13)
  - `TimestampedModel`抽象ベースクラスを作成
  - `created_at`に自動的に`db_index=True`を設定

### 2025-11-09

#### ユーザー機能の追加
- **ArticleにUserを紐付け** (09:44)
  - ArticleモデルにUserとの外部キー関連を追加
  - マイグレーションを実行

- **settings.pyの消し忘れ** (09:58)
  - 設定ファイルの整理

- **shell_plusの導入** (09:58)
  - django-extensionsのshell_plusを有効化
  - より便利な開発環境を構築

#### 環境設定
- **devでのログレベルを変更** (10:51)
  - 開発環境のログ設定を調整

#### コメント機能の追加
- **commentモデルの追加** (11:19)
  - Commentモデルを実装
  - Article、Userとの外部キー関連を設定
  - カラム順序を制御するため`models.Model`を直接継承
  - `created_at`に明示的にインデックスを付与

## セットアップ方法

### 前提条件
- Python 3.14以上
- PostgreSQL
- uv（パッケージマネージャー）

### インストール手順

1. リポジトリをクローン
```bash
git clone <repository-url>
cd workspace
```

2. 仮想環境を作成・有効化
```bash
uv venv
source .venv/bin/activate  # Linuxの場合
```

3. 依存関係をインストール
```bash
uv pip install -e .
```

4. 環境変数を設定
`.env.dev`ファイルを作成し、データベース接続情報を設定

5. マイグレーションを実行
```bash
python manage.py migrate
```

6. 開発サーバーを起動
```bash
python manage.py runserver
```

## 開発コマンド

### マイグレーション
```bash
# マイグレーションファイルを作成
python manage.py makemigrations

# マイグレーションを実行
python manage.py migrate
```

### シェル
```bash
# 拡張シェルを起動（モデルが自動インポートされる）
python manage.py shell_plus
```

### データベース確認
```bash
# データベースシェルに接続
python manage.py dbshell
```

### テスト
```bash
# ユニットテストを実行
uv run pytest app/tests/models/

# E2Eテストを実行（Playwrightを使用）
uv run pytest app/tests/e2e/

# すべてのテストを実行
uv run pytest

# 特定のテストファイルを実行
uv run pytest app/tests/e2e/test_auth.py

# テストカバレッジを確認
uv run pytest --cov=app
```

**E2Eテストについて:**
- Playwrightを使用したブラウザテストを実装
- ヘッドレスモードで実行（XServerなしで動作）
- テスト用ユーザー: `testuser` / `password` と `otheruser` / `password`

## アーキテクチャの特徴

### モデル設計の方針

#### タイムスタンプフィールド
- `TimestampedModel`抽象ベースクラスを提供
- カラム順序を制御したい場合は、`models.Model`を直接継承し、タイムスタンプフィールドを明示的に定義

#### インデックス戦略
- `created_at`フィールドには必ず`db_index=True`を設定
- 外部キー（ForeignKey）には自動的にインデックスが付与される

#### UUID主キー
- uuid7を使用（時系列順序性を保持）
- データベース分散時のID衝突を回避

## プロジェクト構成

```
workspace/
├── app/                    # メインアプリケーション
│   ├── migrations/         # マイグレーションファイル
│   ├── models/            # モデル定義（階層構造）
│   │   ├── __init__.py
│   │   ├── base.py        # TimestampedModel抽象ベースクラス
│   │   ├── article.py     # Articleモデル
│   │   └── comment.py     # Commentモデル
│   ├── views.py           # ビュー
│   └── ...
├── config/                # プロジェクト設定
│   ├── settings/          # 環境別設定
│   │   ├── base.py
│   │   └── dev.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── pyproject.toml
└── README.md
```

## ライセンス

MIT

## 作成者

Yuichiro Kei
