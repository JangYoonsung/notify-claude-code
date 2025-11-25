# Claude Code 通知システム

Claude Codeのセッション情報（コスト、トークン使用量、コード変更など）を自動収集し、macOS通知を配信するシステム

## クイックスタート

```bash
# セッション完了通知を送信
~/.claude/scripts/notification_system.py

# 詳細な通知を送信
~/.claude/scripts/notification_system.py --mode detailed

# ステータス確認
~/.claude/scripts/notification_system.py --status
```

## 主な機能

### 1. 収集される情報
- プロジェクト情報
- コスト（セッション毎の料金）
- トークン使用量（入力/出力/キャッシュ）
- 実行時間（合計/API/ツール）
- コード変更（追加/削除行数）

### 2. 通知モード
- **compact**: コンパクトな単一通知（デフォルト）
  ```
  ✅ Claude セッション完了
  luup-server | $0.5234 | 125,000t | +70L
  ```

- **detailed**: 詳細な情報を含む通知
  ```
  Claude Code セッション詳細
  プロジェクト: luup-server
  コスト: $0.5234
  トークン: 125,000
  時間: 30.0m
  変更: +150 -80
  ```

- **all**: 該当する全ての通知を送信
  - セッション完了、高コスト警告、トークンマイルストーン、大規模コード変更など

### 3. 通知の種類
- セッション完了通知（基本）
- 高コスト警告（閾値: $1.0超過時）
- トークンマイルストーン（10K, 50K, 100K等）
- 大規模コード変更（100行以上）
- 長時間セッション（30分以上）
- 高効率キャッシュ（ヒット率50%以上）

## ファイル構成

```
~/.claude-monitor/
├── scripts/                          # Pythonモジュール
│   ├── notification_system.py        # メイン通知システム
│   ├── session_monitor.py            # セッション情報収集
│   ├── notification_templates.py     # 通知テンプレート生成
│   └── security_validator.py         # セキュリティ検証
├── cache/                            # セッションスナップショット
├── logs/                             # 通知・セッションログ
│   ├── notifications.log
│   └── sessions_YYYYMM.log
├── notification_config.json          # システム設定
├── CLAUDE.md                         # Claude Code用ガイド
└── README.md                         # このファイル
```

## 基本コマンド

### 通知の送信
```bash
# セッション完了通知（compact）
~/.claude/scripts/notification_system.py

# 詳細通知
~/.claude/scripts/notification_system.py --mode detailed

# 全通知
~/.claude/scripts/notification_system.py --mode all

# カスタム通知
~/.claude/scripts/notification_system.py --custom "タイトル" "メッセージ"

# デバッグモード
~/.claude/scripts/notification_system.py --debug
```

### 設定管理
```bash
# ステータス確認
~/.claude/scripts/notification_system.py --status

# 通知を有効化/無効化
~/.claude/scripts/notification_system.py --enable
~/.claude/scripts/notification_system.py --disable

# モード変更
~/.claude/scripts/notification_system.py --mode compact
```

### セッション情報の確認
```bash
# 現在のセッション情報を表示
~/.claude/scripts/session_monitor.py

# 通知ログを確認
tail -20 ~/.claude-monitor/logs/notifications.log

# セッションログを確認（当月）
tail -20 ~/.claude-monitor/logs/sessions_$(date +%Y%m).log
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

## Claude Code Hooks設定

`~/.claude/settings.json` に以下を追加してセッション終了時に自動通知：

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude-monitor/scripts/notification_system.py --mode compact"
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude-monitor/scripts/notification_system.py --mode detailed"
      }]
    }]
  }
}
```

## シェルエイリアス設定（推奨）

`~/.zshrc` または `~/.bashrc` に追加：

```bash
# 通知システムエイリアス
alias cn='~/.claude/scripts/notification_system.py'
alias cnd='~/.claude/scripts/notification_system.py --mode detailed'
alias cns='~/.claude/scripts/notification_system.py --status'
```

使用例：
```bash
cn              # コンパクト通知
cnd             # 詳細通知
cns             # ステータス確認
```

## システムアーキテクチャ

### データフロー
```
~/.claude/projects/{project}/*.jsonl → SessionMonitor → NotificationTemplates → NotificationSystem → macOS通知
```

セッションデータは`.claude/projects/`内の各プロジェクトフォルダに、JSONLファイルとして記録されます。

### 主要コンポーネント

1. **SessionMonitor** (`session_monitor.py`)
   - `~/.claude/projects/{project}/*.jsonl`からセッション情報を解析
   - トークン使用量、コスト、実行時間を集計
   - プロジェクト検出、データ収集、スナップショット保存

2. **NotificationTemplates** (`notification_templates.py`)
   - セッション情報から通知メッセージを生成
   - 複数の通知タイプをサポート

3. **NotificationSystem** (`notification_system.py`)
   - メインオーケストレーター
   - terminal-notifier/osascriptで配信
   - ログ記録、設定管理

4. **SecurityValidator** (`security_validator.py`)
   - 危険なコマンドパターン検出
   - パストラバーサル防止
   - 通知データの自動サニタイズ

## セキュリティ機能

### 自動検証
- 危険なコマンドパターンの検出（`rm -rf /`, `curl | sh`, など）
- パストラバーサル攻撃の防止
- 通知データのサニタイズ（長さ制限、制御文字除去）
- ファイルパーミッションチェック

### セキュリティ設定
```bash
# セキュリティバリデータのテスト
python3 ~/.claude-monitor/scripts/security_validator.py
```

## 高度な機能

### terminal-notifier連携

より高機能な通知には`terminal-notifier`をインストール：

```bash
brew install terminal-notifier
```

機能：
- プロジェクト名のサブタイトル表示
- 重要度別のタイムアウト設定
- クリック時にターミナルを前面表示
- 通知のグループ化

### 通知レベルとサウンド

| レベル | サウンド | タイムアウト | 用途 |
|--------|----------|--------------|------|
| success | Glass | 5秒 | セッション完了 |
| info | Tink | 3秒 | 情報通知 |
| warning | Basso | 10秒 | 警告 |
| milestone | Hero | 10秒 | マイルストーン |

## 重要な注意事項

### セッションデータについて

**データが記録される条件：**
- Claude Codeで実際に作業を行った
- APIコールが発生した（モデルとの対話）
- セッションが正常に終了した

**データがない場合：**
- プロジェクト名のみ表示されます（正常動作）
- 最初のセッション後にデータが記録されます
- 2回目以降のセッションで詳細通知が表示されます

データの有無を確認：
```bash
python3 ~/.claude-monitor/scripts/session_monitor.py
```

## トラブルシューティング

### 通知が表示されない

1. ステータス確認
   ```bash
   ~/.claude/scripts/notification_system.py --status
   ```

2. テスト通知
   ```bash
   ~/.claude/scripts/notification_system.py --custom "テスト" "これはテストです"
   ```

3. macOS通知設定を確認
   - システム環境設定 > 通知 > ターミナル
   - 「通知を許可」がONか確認

4. デバッグモードで実行
   ```bash
   ~/.claude/scripts/notification_system.py --debug
   ```

### terminal-notifierが使用されない

```bash
# インストール確認
which terminal-notifier

# インストール
brew install terminal-notifier
```

### セッション情報が表示されない

```bash
# プロジェクトデータの確認
python3 ~/.claude-monitor/scripts/session_monitor.py

# .claude.jsonの確認
cat ~/.claude.json | python3 -m json.tool
```

## カスタマイズ

### サウンドの変更

`~/.claude-monitor/scripts/notification_system.py` の `sound_map` を編集：

```python
sound_map = {
    'success': 'Glass',
    'info': 'Tink',
    'warning': 'Basso',
    'milestone': 'Hero'
}
```

利用可能なサウンド: Glass, Tink, Basso, Hero, Ping, Pop, Purr, Submarine, など

### 閾値の調整

`~/.claude-monitor/notification_config.json` を編集：

```json
{
  "cost_threshold": 2.0,           // 高コスト警告の閾値を$2.0に
  "large_change_threshold": 200,   // 大規模変更を200行に
  "long_session_minutes": 60       // 長時間セッションを60分に
}
```

### 静音時間帯の設定

```json
{
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00"
  }
}
```

夜間（22:00-08:00）は通知をログのみに記録し、表示しません。

## ログファイル

### 通知ログ
`~/.claude-monitor/logs/notifications.log`

すべての通知が記録されます。

### セッションログ
`~/.claude-monitor/logs/sessions_YYYYMM.log`

月ごとのセッション情報が記録されます。

### スナップショット
`~/.claude-monitor/cache/session_HASH.json`

各セッションの詳細情報がJSON形式で保存されます。

## 使用例

### 基本的な使い方

```bash
# 1. Claude Codeで作業
# 2. 作業完了後に実行
~/.claude/scripts/notification_system.py

# または詳細通知
~/.claude/scripts/notification_system.py --mode detailed
```

### 自動化

```bash
# gitフックで自動通知（.git/hooks/post-commit）
#!/bin/bash
~/.claude/scripts/notification_system.py --custom "Git Commit" "変更をコミットしました"

# コマンド完了後に通知
npm run build && ~/.claude/scripts/notification_system.py --custom "ビルド完了" "成功しました"
```

### デバッグ

```bash
# 詳細出力でデバッグ
~/.claude/scripts/notification_system.py --verbose --debug

# ログをリアルタイムで監視
tail -f ~/.claude-monitor/logs/notifications.log
```

## システム要件

- macOS 10.14以降
- Python 3.6以降（システム標準）
- オプション: terminal-notifier（Homebrew経由）

## パフォーマンス

- 起動時間: <100ms
- メモリ使用量: <10MB
- CPU使用率: 通知送信時のみ瞬間的
- ディスク使用量: ログとスナップショットで数MB/月

## セキュリティとプライバシー

- 全データはローカルに保存
- ネットワーク通信なし
- 外部サービスへの送信なし
- ファイルパーミッション: 適切に制限

## バージョン情報

- Version: 1.0.0
- Created: 2025-11-25
- Last Updated: 2025-11-25

## 参考資料

- [Zenn記事: Claude Code の Hooks と terminal-notifier を活用した通知システム構築ガイド](https://zenn.dev/yuru_log/articles/claude-code-hooks-terminal-notifier-guide)
- [terminal-notifier GitHub](https://github.com/julienXX/terminal-notifier)
- Claude Code 公式ドキュメント

## まとめ

このシステムにより、Claude Codeの作業セッションを自動的に追跡し、コスト、トークン使用量、コード変更などの重要な情報をmacOS通知で受け取ることができます。セキュリティ機能、デバッグモード、カスタマイズ可能な設定により、プロダクション品質の通知システムを実現しています。
