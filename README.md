# Claude Code 通知システム

Claude Codeのセッション情報（コスト、トークン使用量、コード変更など）を自動収集し、macOS通知を配信するシステム

## インストール

### NPMパッケージとして使用（推奨）

```bash
# npx経由で直接実行
npx notify-claude-code --status

# グローバルインストール
npm install -g notify-claude-code
```

### ローカル開発

```bash
cd ~/.claude-monitor
npm install
npm run build
npm link
```

## クイックスタート

```bash
# セッション完了通知
npx notify-claude-code

# 詳細通知
npx notify-claude-code --mode detailed

# ステータス確認
npx notify-claude-code --status
```

## 主な機能

### 収集される情報
- コスト（セッション毎の料金）
- トークン使用量（入力/出力/キャッシュ）
- 実行時間
- コード変更（追加/削除行数）

### 通知モード
- **compact**: コンパクトな単一通知（デフォルト）
- **detailed**: 詳細な情報を含む通知
- **all**: 該当する全ての通知を送信

### 通知の種類
- セッション完了通知
- 高コスト警告（閾値超過時）
- トークンマイルストーン
- 大規模コード変更

## Claude Code Hooks設定

`~/.claude/settings.json`に追加してセッション終了時に自動通知：

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "npx notify-claude-code --mode compact"
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "npx notify-claude-code --mode detailed"
      }]
    }]
  }
}
```

## 基本コマンド

```bash
# 通知の送信
npx notify-claude-code                              # compact通知
npx notify-claude-code --mode detailed              # 詳細通知
npx notify-claude-code --mode all                   # 全通知
npx notify-claude-code --custom "タイトル" "メッセージ"  # カスタム通知

# 設定管理
npx notify-claude-code --status                     # ステータス確認
npx notify-claude-code --enable                     # 有効化
npx notify-claude-code --disable                    # 無効化

# デバッグ
npx notify-claude-code --debug                      # デバッグモード
```

## 設定ファイル

`~/.claude-monitor/notification_config.json`

```json
{
  "enabled": true,
  "mode": "compact",
  "cost_threshold": 1.0,
  "large_change_threshold": 100,
  "long_session_minutes": 30,
  "enable_milestones": true,
  "enable_warnings": true,
  "quiet_hours": {
    "enabled": false,
    "start": "22:00",
    "end": "08:00"
  }
}
```

## アーキテクチャ

```
~/.claude/projects/{project}/*.jsonl
  ↓
SessionMonitor (セッション情報解析)
  ↓
NotificationTemplates (メッセージ生成)
  ↓
NotificationSystem (通知配信)
  ↓
macOS通知
```

### 主要コンポーネント

- **SessionMonitor**: セッションデータの解析・集計
- **NotificationTemplates**: 通知メッセージの生成
- **NotificationSystem**: 通知の配信とログ記録
- **SecurityValidator**: セキュリティ検証

## terminal-notifier（推奨）

より高機能な通知のため、terminal-notifierのインストールを推奨：

```bash
brew install terminal-notifier
```

## トラブルシューティング

### 通知が表示されない

```bash
# ステータス確認
npx notify-claude-code --status

# テスト通知
npx notify-claude-code --custom "テスト" "これはテストです"

# デバッグモード
npx notify-claude-code --debug
```

macOS設定：システム環境設定 > 通知 > ターミナル > 「通知を許可」をON

### セッション情報が表示されない

Claude Codeで実際に作業を行い、APIコールが発生した後にデータが記録されます。

```bash
# セッション情報を確認
python3 ~/.claude-monitor/scripts/session_monitor.py
```

## ログファイル

- 通知ログ: `~/.claude-monitor/logs/notifications.log`
- セッションログ: `~/.claude-monitor/logs/sessions_YYYYMM.log`
- スナップショット: `~/.claude-monitor/cache/session_*.json`

## セキュリティとプライバシー

- 全データはローカルに保存
- ネットワーク通信なし
- 外部サービスへの送信なし
- 危険なコマンドパターンの自動検出

## システム要件

- macOS 10.14以降
- Python 3.6以降
- Node.js 14.0以降
- オプション: terminal-notifier

## ライセンス

MIT
