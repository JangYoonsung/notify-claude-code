#!/usr/bin/env python3
"""
Claude Code Session Monitor
セッション情報を収集・分析するモジュール
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib


class SessionMonitor:
    """Claude Codeのセッション情報を監視・分析"""

    def __init__(self):
        self.home = Path.home()
        self.claude_config = self.home / ".claude.json"
        self.claude_projects = self.home / ".claude" / "projects"
        self.monitor_dir = self.home / ".claude-monitor"
        self.cache_dir = self.monitor_dir / "cache"
        self.logs_dir = self.monitor_dir / "logs"
        self.reports_dir = self.monitor_dir / "reports"

        # ディレクトリ作成
        for d in [self.monitor_dir, self.cache_dir, self.logs_dir, self.reports_dir]:
            d.mkdir(exist_ok=True)

    def load_config(self) -> Optional[Dict[str, Any]]:
        """Claude設定ファイルを読み込み"""
        try:
            if self.claude_config.exists():
                with open(self.claude_config, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
        return None

    def get_current_project(self) -> Optional[str]:
        """現在のプロジェクトパスを取得"""
        cwd = os.getcwd()
        config = self.load_config()

        if not config or 'projects' not in config:
            return None

        # 現在のディレクトリに一致するプロジェクトを探す
        # 最も長い一致パスを優先（より具体的なプロジェクト）
        matched_projects = []
        for project_path in config['projects'].keys():
            if cwd.startswith(project_path):
                matched_projects.append(project_path)

        if not matched_projects:
            return None

        # 最も長いパス（最も具体的）を返す
        return max(matched_projects, key=len)

    def get_project_folder(self, project_path: str) -> Optional[Path]:
        """プロジェクトパスに対応する.claude/projectsフォルダを取得"""
        # パスを変換: /Users/foo/bar -> -Users-foo-bar
        # また、.（ドット）も-（ハイフン）に変換される
        folder_name = project_path.replace('/', '-').replace('.', '-')
        project_folder = self.claude_projects / folder_name

        if project_folder.exists():
            return project_folder
        return None

    def get_current_session_file(self, project_folder: Path) -> Optional[Path]:
        """現在のセッションのjsonlファイルを取得"""
        # agent-で始まらないjsonlファイルを探す（セッションファイル）
        jsonl_files = [f for f in project_folder.glob('*.jsonl')
                      if not f.name.startswith('agent-')]

        if not jsonl_files:
            return None

        # 最新のファイルを返す
        return max(jsonl_files, key=lambda f: f.stat().st_mtime)

    def parse_session_data(self, session_file: Path) -> Dict[str, Any]:
        """セッションjsonlファイルからデータを解析"""
        stats = {
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_creation_tokens': 0,
            'cache_read_tokens': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'tool_calls': 0,
            'duration_ms': 0,
            'api_duration_ms': 0,
        }

        session_id = session_file.stem
        first_timestamp = None
        last_timestamp = None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)

                        # タイムスタンプを記録
                        if 'timestamp' in data:
                            ts = data['timestamp']
                            if first_timestamp is None:
                                first_timestamp = ts
                            last_timestamp = ts

                        # トークン使用量を集計
                        if 'message' in data and 'usage' in data['message']:
                            usage = data['message']['usage']
                            stats['input_tokens'] += usage.get('input_tokens', 0)
                            stats['output_tokens'] += usage.get('output_tokens', 0)
                            stats['cache_creation_tokens'] += usage.get('cache_creation_input_tokens', 0)
                            stats['cache_read_tokens'] += usage.get('cache_read_input_tokens', 0)

                        # ツール呼び出しをカウント
                        if data.get('type') == 'assistant':
                            if 'message' in data and 'content' in data['message']:
                                for item in data['message']['content']:
                                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                                        stats['tool_calls'] += 1

                        # コード変更を記録（file-history-snapshotから）
                        if data.get('type') == 'file-history-snapshot':
                            # 簡易的な行数カウント（実装可能であれば）
                            pass

                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"セッションファイル解析エラー: {e}")

        # 実行時間を計算
        if first_timestamp and last_timestamp:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
                end = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                stats['duration_ms'] = int((end - start).total_seconds() * 1000)
            except:
                pass

        stats['session_id'] = session_id
        return stats

    def calculate_cost(self, stats: Dict[str, Any]) -> float:
        """トークン使用量からコストを計算

        Claude Sonnet 4.5の料金（2025年時点の想定）:
        - Input: $3 per 1M tokens
        - Output: $15 per 1M tokens
        - Cache creation: $3.75 per 1M tokens
        - Cache read: $0.30 per 1M tokens
        """
        input_cost = (stats['input_tokens'] / 1_000_000) * 3.0
        output_cost = (stats['output_tokens'] / 1_000_000) * 15.0
        cache_creation_cost = (stats['cache_creation_tokens'] / 1_000_000) * 3.75
        cache_read_cost = (stats['cache_read_tokens'] / 1_000_000) * 0.30

        return input_cost + output_cost + cache_creation_cost + cache_read_cost

    def get_session_info(self) -> Dict[str, Any]:
        """現在のセッション情報を取得"""
        project_path = self.get_current_project()
        if not project_path:
            return {}

        project_folder = self.get_project_folder(project_path)
        if not project_folder:
            return {}

        session_file = self.get_current_session_file(project_folder)
        if not session_file:
            return {}

        # セッションデータを解析
        stats = self.parse_session_data(session_file)

        # コストを計算
        cost = self.calculate_cost(stats)

        has_session_data = any([
            stats['input_tokens'] > 0,
            stats['output_tokens'] > 0,
            stats['tool_calls'] > 0
        ])

        return {
            'project_path': project_path,
            'project_name': Path(project_path).name,
            'session_id': stats.get('session_id', 'unknown'),
            'has_session_data': has_session_data,
            'cost': {
                'last_session': cost,
                'formatted': f"${cost:.4f}"
            },
            'tokens': {
                'input': stats['input_tokens'],
                'output': stats['output_tokens'],
                'cache_creation': stats['cache_creation_tokens'],
                'cache_read': stats['cache_read_tokens'],
                'total': stats['input_tokens'] + stats['output_tokens']
            },
            'duration': {
                'total_ms': stats['duration_ms'],
                'api_ms': stats.get('api_duration_ms', 0),
                'tool_ms': 0,  # jsonlからは直接取得できない
                'formatted': self._format_duration(stats['duration_ms'])
            },
            'code_changes': {
                'lines_added': stats['lines_added'],
                'lines_removed': stats['lines_removed'],
                'net_change': stats['lines_added'] - stats['lines_removed']
            },
            'tool_calls': stats['tool_calls'],
            'timestamp': datetime.now().isoformat()
        }

    def _format_duration(self, ms: int) -> str:
        """ミリ秒を人間が読める形式に変換"""
        if ms < 1000:
            return f"{ms}ms"

        seconds = ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"

        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"

        hours = minutes / 60
        return f"{hours:.1f}h"

    def get_user_stats(self) -> Dict[str, Any]:
        """ユーザー統計情報を取得"""
        config = self.load_config()
        if not config:
            return {}

        return {
            'user_id': config.get('userID', 'unknown'),
            'num_startups': config.get('numStartups', 0),
            'first_start': config.get('firstStartTime', 'unknown'),
            'auto_updates': config.get('autoUpdates', False),
            'total_projects': len(config.get('projects', {}))
        }

    def calculate_session_hash(self, session_info: Dict[str, Any]) -> str:
        """セッション情報のハッシュを計算"""
        # セッションIDとタイムスタンプからハッシュ生成
        data = f"{session_info.get('session_id', '')}_{session_info.get('timestamp', '')}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def save_session_snapshot(self, session_info: Dict[str, Any]) -> Path:
        """セッション情報のスナップショットを保存"""
        session_hash = self.calculate_session_hash(session_info)
        snapshot_file = self.cache_dir / f"session_{session_hash}.json"

        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)

        return snapshot_file

    def generate_session_report(self, session_info: Dict[str, Any]) -> str:
        """セッション情報から詳細レポートを生成"""
        lines = []
        lines.append("=" * 60)
        lines.append("Claude Code Session Report")
        lines.append("=" * 60)
        lines.append("")

        # プロジェクト情報
        lines.append(f"プロジェクト: {session_info.get('project_name', 'Unknown')}")
        lines.append(f"セッションID: {session_info.get('session_id', 'Unknown')[:16]}...")
        lines.append("")

        # コスト情報
        cost_info = session_info.get('cost', {})
        lines.append(f"コスト: {cost_info.get('formatted', '$0.0000')}")
        lines.append("")

        # トークン使用量
        tokens = session_info.get('tokens', {})
        lines.append("トークン使用量:")
        lines.append(f"  入力: {tokens.get('input', 0):,}")
        lines.append(f"  出力: {tokens.get('output', 0):,}")
        lines.append(f"  キャッシュ作成: {tokens.get('cache_creation', 0):,}")
        lines.append(f"  キャッシュ読込: {tokens.get('cache_read', 0):,}")
        lines.append(f"  合計: {tokens.get('total', 0):,}")
        lines.append("")

        # 実行時間
        duration = session_info.get('duration', {})
        lines.append("実行時間:")
        lines.append(f"  合計: {duration.get('formatted', '0ms')}")
        lines.append("")

        # ツール呼び出し
        lines.append(f"ツール呼び出し: {session_info.get('tool_calls', 0)} 回")
        lines.append("")

        # コード変更
        changes = session_info.get('code_changes', {})
        if changes.get('lines_added', 0) > 0 or changes.get('lines_removed', 0) > 0:
            lines.append("コード変更:")
            lines.append(f"  追加: +{changes.get('lines_added', 0)} 行")
            lines.append(f"  削除: -{changes.get('lines_removed', 0)} 行")
            lines.append(f"  純変更: {changes.get('net_change', 0):+d} 行")
            lines.append("")

        lines.append(f"タイムスタンプ: {session_info.get('timestamp', 'Unknown')}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def log_session(self, session_info: Dict[str, Any]):
        """セッション情報をログファイルに記録"""
        log_file = self.logs_dir / f"sessions_{datetime.now().strftime('%Y%m')}.log"

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{session_info.get('timestamp', 'Unknown')} | ")
            f.write(f"Session: {session_info.get('session_id', 'Unknown')[:8]} | ")
            f.write(f"Cost: {session_info.get('cost', {}).get('formatted', '$0.0000')} | ")
            f.write(f"Tokens: {session_info.get('tokens', {}).get('total', 0):,} | ")
            f.write(f"Tools: {session_info.get('tool_calls', 0)}\n")


def main():
    """メイン処理"""
    monitor = SessionMonitor()

    # セッション情報を取得
    session_info = monitor.get_session_info()

    if not session_info:
        print("セッション情報が見つかりません")
        return

    # レポート生成
    report = monitor.generate_session_report(session_info)
    print(report)

    # スナップショット保存
    snapshot_file = monitor.save_session_snapshot(session_info)
    print(f"\nスナップショット保存: {snapshot_file}")

    # ログ記録
    monitor.log_session(session_info)


if __name__ == "__main__":
    main()
