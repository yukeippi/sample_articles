# AWS IAM Policy Documentation

このディレクトリには、GitHub Actions経由でApp RunnerへのデプロイとECRへのイメージプッシュを行うためのIAMポリシーが含まれています。

## ファイル一覧

- `policy.json` - GitHub OIDC用IAMロール `github-oidc-apprunner-deploy` に適用するポリシー
- `trust.json` - App Runnerアクセスロール用の信頼ポリシー
- `ecr-pull.json` - App RunnerがECRからイメージをプルするためのポリシー
- `service.json` - App Runnerサービス設定（初回作成時の設定テンプレート）

## policy.json の詳細

このポリシーは最小権限の原則に基づいて設計されており、以下の5つのステートメントで構成されています。

### 1. EcrAuth - ECR認証トークンの取得

```json
{
  "Sid": "EcrAuth",
  "Effect": "Allow",
  "Action": ["ecr:GetAuthorizationToken"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:RequestedRegion": "ap-northeast-1"
    }
  }
}
```

**目的**: ECRにログインするための認証トークンを取得

**権限**:
- `ecr:GetAuthorizationToken` - ECR認証トークンの取得

**リソース**: `*` (この操作はアカウントレベルのため、特定のリソースを指定できない)

**条件**: `ap-northeast-1` リージョンのみに制限

**使用箇所**: `.github/workflows/deploy.yml` の `amazon-ecr-login@v2` アクション

---

### 2. EcrReadOnly - ECRリポジトリとイメージの読み取り

```json
{
  "Sid": "EcrReadOnly",
  "Effect": "Allow",
  "Action": [
    "ecr:DescribeRepositories",
    "ecr:BatchGetImage",
    "ecr:DescribeImages"
  ],
  "Resource": "arn:aws:ecr:ap-northeast-1:096547140789:repository/sample-todo"
}
```

**目的**: リポジトリ情報の取得とイメージの読み取り（主にロールバック用）

**権限**:
- `ecr:DescribeRepositories` - リポジトリのメタデータ取得（URI取得など）
- `ecr:BatchGetImage` - イメージマニフェストの取得
- `ecr:DescribeImages` - イメージの詳細情報取得（タグ確認など）

**リソース**: `sample-todo` リポジトリのみに制限

**使用箇所**:
- `.github/workflows/deploy.yml` L106 - リポジトリURI取得
- `.github/workflows/rollback.yml` L90, L140 - イメージの存在確認
- `.github/workflows/quick-rollback.yml` L140 - 前バージョンのイメージ確認

---

### 3. EcrPushOnly - ECRへのイメージプッシュ

```json
{
  "Sid": "EcrPushOnly",
  "Effect": "Allow",
  "Action": [
    "ecr:BatchCheckLayerAvailability",
    "ecr:CompleteLayerUpload",
    "ecr:InitiateLayerUpload",
    "ecr:PutImage",
    "ecr:UploadLayerPart"
  ],
  "Resource": "arn:aws:ecr:ap-northeast-1:096547140789:repository/sample-todo"
}
```

**目的**: Dockerイメージのプッシュに必要な書き込み権限

**権限**:
- `ecr:BatchCheckLayerAvailability` - レイヤーの存在確認（重複アップロード防止）
- `ecr:InitiateLayerUpload` - レイヤーアップロードの開始
- `ecr:UploadLayerPart` - レイヤーの一部（チャンク）をアップロード
- `ecr:CompleteLayerUpload` - レイヤーアップロードの完了
- `ecr:PutImage` - イメージマニフェストの登録

**リソース**: `sample-todo` リポジトリのみに制限

**使用箇所**: `.github/workflows/deploy.yml` L111, L114 - `docker push` コマンド

---

### 4. AppRunnerList - App Runnerサービス一覧の取得

```json
{
  "Sid": "AppRunnerList",
  "Effect": "Allow",
  "Action": ["apprunner:ListServices"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws:RequestedRegion": "ap-northeast-1"
    }
  }
}
```

**目的**: サービス名からARNを解決するためのサービス一覧取得

**権限**:
- `apprunner:ListServices` - アカウント内の全App Runnerサービス一覧を取得

**リソース**: `*` (この操作はアカウントレベルのため、特定のリソースを指定できない)

**条件**: `ap-northeast-1` リージョンのみに制限

**使用箇所**:
- `.github/workflows/deploy.yml` L137 - サービス名 `sample_todo` からARN解決
- `.github/workflows/rollback.yml` L113 - ロールバック時のARN解決
- 他の全ワークフローでも同様に使用

**注意**: この権限はアカウント内の全サービス名を閲覧できますが、リージョン制限により影響範囲は限定的です。

---

### 5. AppRunnerManage - App Runnerサービスの更新と参照

```json
{
  "Sid": "AppRunnerManage",
  "Effect": "Allow",
  "Action": [
    "apprunner:UpdateService",
    "apprunner:DescribeService"
  ],
  "Resource": "arn:aws:apprunner:ap-northeast-1:096547140789:service/sample_todo/*"
}
```

**目的**: 特定のApp Runnerサービスの更新とステータス確認

**権限**:
- `apprunner:UpdateService` - サービス設定の更新（新しいイメージのデプロイなど）
- `apprunner:DescribeService` - サービスの詳細情報とステータス取得

**リソース**: `sample_todo` サービスのみに制限（`/*` はサービス内の全リソースを意味）

**使用箇所**:
- `.github/workflows/deploy.yml` L149 - 新しいイメージでサービス更新
- `.github/workflows/deploy.yml` L159 - デプロイステータス確認（ポーリング）
- ロールバックワークフローでも同様に使用

---

## セキュリティのベストプラクティス

このポリシーは以下のセキュリティ原則に従っています:

1. **最小権限の原則**: 必要最小限の権限のみを付与
2. **リソースの明示的な制限**: 可能な限り特定のリソースARNを指定
3. **リージョン制限**: 条件付きアクセスでリージョンを制限
4. **権限の分離**: 読み取り専用と書き込み権限を分離

## ポリシーの適用方法

```bash
# IAMロールにポリシーを適用
aws iam put-role-policy \
  --role-name github-oidc-apprunner-deploy \
  --policy-name AppRunnerDeployPolicy \
  --policy-document file://.aws/policy.json

# ポリシーの確認
aws iam get-role-policy \
  --role-name github-oidc-apprunner-deploy \
  --policy-name AppRunnerDeployPolicy
```

## トラブルシューティング

### AccessDeniedException エラーが発生する場合

1. エラーメッセージで不足している権限（`Action`）を確認
2. 必要に応じて `policy.json` に権限を追加
3. IAMポリシーを再適用
4. GitHub Actionsワークフローを再実行

### よくあるエラーと対処法

- `apprunner:ListServices` エラー → Resource を `*` に設定（特定リソースに限定不可）
- `ecr:GetAuthorizationToken` エラー → Resource を `*` に設定（アカウントレベルの操作）
- リージョンエラー → Condition の `aws:RequestedRegion` を確認

---

## trust.json の詳細

App RunnerがECRからイメージをプルするためのアクセスロールに適用する信頼ポリシーです。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**目的**: App Runnerサービスがこのロールを引き受ける（AssumeRole）ことを許可

**Principal**: `build.apprunner.amazonaws.com` - App Runnerのビルドサービス

**適用先**: IAMロール `apprunner-ecr-access` の信頼関係

**作成コマンド**:
```bash
aws iam create-role \
  --role-name apprunner-ecr-access \
  --assume-role-policy-document file://.aws/trust.json
```

---

## ecr-pull.json の詳細

App Runnerが `apprunner-ecr-access` ロールを使用してECRからイメージをプルするためのポリシーです。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:DescribeImages",
        "ecr:BatchCheckLayerAvailability"
      ],
      "Resource": "arn:aws:ecr:ap-northeast-1:096547140789:repository/sample-todo"
    }
  ]
}
```

### ステートメント1: ECR認証

**権限**: `ecr:GetAuthorizationToken` - ECR認証トークンの取得

**リソース**: `*` (アカウントレベルの操作)

### ステートメント2: イメージプル

**権限**:
- `ecr:BatchGetImage` - イメージマニフェストの取得
- `ecr:GetDownloadUrlForLayer` - イメージレイヤーのダウンロードURL取得
- `ecr:DescribeImages` - イメージメタデータの取得
- `ecr:BatchCheckLayerAvailability` - レイヤーの存在確認

**リソース**: `sample-todo` リポジトリのみに制限

**適用コマンド**:
```bash
aws iam put-role-policy \
  --role-name apprunner-ecr-access \
  --policy-name ECRPullPolicy \
  --policy-document file://.aws/ecr-pull.json
```

**重要な修正点**:
- ❌ 旧: `arn:aws:ecr:::repository/sample_todo` （リージョンとアカウントIDが欠落、リポジトリ名の誤り）
- ✅ 新: `arn:aws:ecr:ap-northeast-1:096547140789:repository/sample-todo`

---

## service.json の詳細

App Runnerサービスの初回作成時に使用する設定テンプレートです。

```json
{
  "ServiceName": "sample_todo",
  "SourceConfiguration": {
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::096547140789:role/apprunner-ecr-access"
    },
    "AutoDeploymentsEnabled": true,
    "ImageRepository": {
      "ImageIdentifier": "096547140789.dkr.ecr.ap-northeast-1.amazonaws.com/sample-todo:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "DJANGO_SETTINGS_MODULE": "config.settings.prod",
          "DJANGO_SECRET_KEY": "your-secret-key-here-change-in-production",
          "DJANGO_ALLOWED_HOSTS": "*",
          "DATABASE_URL": "sqlite:///db.sqlite3",
          "DJANGO_CSRF_TRUSTED_ORIGINS": ""
        }
      }
    }
  },
  "InstanceConfiguration": {
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }
}
```

### 主要な設定項目

**ServiceName**: `sample_todo` - サービス名（GitHub Actionsワークフローで使用）

**AccessRoleArn**: `apprunner-ecr-access` - ECRからイメージをプルするためのロール

**AutoDeploymentsEnabled**: `true` - ECRに新しいイメージがプッシュされたら自動デプロイ

**ImageIdentifier**: 初回デプロイ時のイメージ（`:latest` タグ）

**Port**: `8000` - Djangoアプリケーションのポート

**InstanceConfiguration**:
- CPU: 1 vCPU
- Memory: 2 GB

### 環境変数

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | Django本番設定 |
| `DJANGO_SECRET_KEY` | `your-secret-key-here-change-in-production` | **要変更**: 本番環境用シークレットキー |
| `DJANGO_ALLOWED_HOSTS` | `*` | 許可するホスト（本番では具体的なドメインを指定推奨） |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | データベースURL |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `""` | CSRF信頼されるオリジン |

**セキュリティ警告**:
- ⚠️ `DJANGO_SECRET_KEY` は本番環境では必ず変更してください
- ⚠️ `DJANGO_ALLOWED_HOSTS` は本番環境では具体的なドメインを指定することを推奨

### サービス作成コマンド

```bash
# サービス作成（初回のみ）
aws apprunner create-service --cli-input-json file://.aws/service.json

# サービス更新（GitHub Actionsで自動実行）
aws apprunner update-service \
  --service-arn <SERVICE_ARN> \
  --source-configuration file://.aws/service.json
```

**注意**: GitHub Actionsワークフローでは、`service.json` を直接使用せず、`update-service` コマンドでイメージのみを更新しています。

---

## IAMロールとポリシーの関係図

```
GitHub Actions (OIDC)
    ↓ assumes
[github-oidc-apprunner-deploy] ← policy.json
    ↓ performs
    ├─ ECRにイメージをプッシュ
    └─ App Runnerサービスを更新

App Runner Service
    ↓ uses
[apprunner-ecr-access] ← trust.json + ecr-pull.json
    ↓ performs
    └─ ECRからイメージをプル
```

### 2つのロールの違い

| ロール名 | 目的 | 信頼関係 | ポリシー | 使用者 |
|---------|------|---------|---------|--------|
| `github-oidc-apprunner-deploy` | CI/CDパイプライン実行 | GitHub OIDC | `policy.json` | GitHub Actions |
| `apprunner-ecr-access` | イメージプル | App Runner | `ecr-pull.json` + `trust.json` | App Runner |

---

## セットアップ手順

### 1. App Runner用のECRアクセスロール作成

```bash
# ロール作成
aws iam create-role \
  --role-name apprunner-ecr-access \
  --assume-role-policy-document file://.aws/trust.json

# ECRプルポリシーをアタッチ
aws iam put-role-policy \
  --role-name apprunner-ecr-access \
  --policy-name ECRPullPolicy \
  --policy-document file://.aws/ecr-pull.json
```

### 2. GitHub Actions用のOIDCロール作成

```bash
# OIDCプロバイダー作成（初回のみ）
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# GitHub OIDC用のロール作成（信頼ポリシーは別途作成が必要）
aws iam create-role \
  --role-name github-oidc-apprunner-deploy \
  --assume-role-policy-document file://github-oidc-trust.json

# デプロイポリシーをアタッチ
aws iam put-role-policy \
  --role-name github-oidc-apprunner-deploy \
  --policy-name AppRunnerDeployPolicy \
  --policy-document file://.aws/policy.json
```

### 3. App Runnerサービス作成

```bash
aws apprunner create-service --cli-input-json file://.aws/service.json
```

---

## 関連リンク

- [AWS App Runner IAM Permissions](https://docs.aws.amazon.com/apprunner/latest/dg/security-iam.html)
- [Amazon ECR IAM Policies](https://docs.aws.amazon.com/AmazonECR/latest/userguide/security-iam.html)
- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
