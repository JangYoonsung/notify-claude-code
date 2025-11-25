#!/usr/bin/env python3
"""
Claude Code Notification Templates
セッション情報を基にした通知メッセージのテンプレート
"""

from typing import Dict, Any
from enum import Enum


class NotificationLevel(Enum):
    """通知レベル"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    MILESTONE = "milestone"


class NotificationTemplates:
    """通知テンプレート集"""

    @staticmethod
    def session_complete(session_info: Dict[str, Any]) -> Dict[str, str]:
        """セッション完了通知"""
        # セッションデータがない場合の処理
        has_data = session_info.get('has_session_data', False)

        if not has_data:
            project_name = session_info.get('project_name', 'Unknown')
            return {
                'title': "✅ Claude Code 完了",
                'message': f"📁 {project_name} | データ収集待ち",
                'level': NotificationLevel.SUCCESS.value
            }

        tokens = session_info.get('tokens', {})
        cost = session_info.get('cost', {})
        duration = session_info.get('duration', {})
        changes = session_info.get('code_changes', {})

        title = "✅ Claude セッション完了"
        message_parts = []

        # プロジェクト名
        project_name = session_info.get('project_name', 'Unknown')
        message_parts.append(f"📁 {project_name}")

        # コスト情報
        cost_val = cost.get('last_session', 0)
        if cost_val > 0:
            message_parts.append(f"💰 {cost.get('formatted', '$0.0000')}")

        # トークン使用量（簡潔に）
        total_tokens = tokens.get('total', 0)
        if total_tokens > 0:
            message_parts.append(f"🎯 {total_tokens:,}t")

        # 実行時間
        duration_ms = duration.get('total_ms', 0)
        if duration_ms > 0:
            message_parts.append(f"⏱️ {duration.get('formatted', '0ms')}")

        # コード変更
        net_change = changes.get('net_change', 0)
        if net_change != 0:
            sign = "+" if net_change > 0 else ""
            message_parts.append(f"📝 {sign}{net_change}L")

        return {
            'title': title,
            'message': " | ".join(message_parts),
            'level': NotificationLevel.SUCCESS.value
        }

    @staticmethod
    def high_cost_warning(session_info: Dict[str, Any], threshold: float = 1.0) -> Dict[str, str]:
        """高コスト警告"""
        cost = session_info.get('cost', {}).get('last_session', 0)

        if cost < threshold:
            return None

        project_name = session_info.get('project_name', 'Unknown')

        return {
            'title': "⚠️ 高コスト警告",
            'message': f"{project_name} | コスト: ${cost:.4f} | 閾値を超えました",
            'level': NotificationLevel.WARNING.value
        }

    @staticmethod
    def token_milestone(session_info: Dict[str, Any]) -> Dict[str, str]:
        """トークンマイルストーン通知"""
        tokens = session_info.get('tokens', {})
        total = tokens.get('total', 0)

        # マイルストーン判定
        milestones = [10000, 50000, 100000, 500000, 1000000]
        milestone = None

        for m in milestones:
            if total >= m and total < m * 1.1:  # 10%マージン
                milestone = m
                break

        if not milestone:
            return None

        project_name = session_info.get('project_name', 'Unknown')

        return {
            'title': f"🎉 {milestone:,} トークン達成！",
            'message': f"{project_name} | 合計: {total:,} tokens",
            'level': NotificationLevel.MILESTONE.value
        }

    @staticmethod
    def large_code_change(session_info: Dict[str, Any], threshold: int = 100) -> Dict[str, str]:
        """大規模コード変更通知"""
        changes = session_info.get('code_changes', {})
        lines_added = changes.get('lines_added', 0)
        lines_removed = changes.get('lines_removed', 0)
        total_change = lines_added + lines_removed

        if total_change < threshold:
            return None

        project_name = session_info.get('project_name', 'Unknown')

        return {
            'title': "📊 大規模変更",
            'message': f"{project_name} | +{lines_added} -{lines_removed} ({total_change} 行)",
            'level': NotificationLevel.INFO.value
        }

    @staticmethod
    def long_session(session_info: Dict[str, Any], threshold_minutes: int = 30) -> Dict[str, str]:
        """長時間セッション通知"""
        duration_ms = session_info.get('duration', {}).get('total_ms', 0)
        duration_minutes = duration_ms / 1000 / 60

        if duration_minutes < threshold_minutes:
            return None

        project_name = session_info.get('project_name', 'Unknown')
        formatted_duration = session_info.get('duration', {}).get('formatted', '0ms')

        return {
            'title': "⏰ 長時間セッション",
            'message': f"{project_name} | {formatted_duration} の作業完了",
            'level': NotificationLevel.INFO.value
        }

    @staticmethod
    def cache_efficiency(session_info: Dict[str, Any]) -> Dict[str, str]:
        """キャッシュ効率通知"""
        tokens = session_info.get('tokens', {})
        cache_read = tokens.get('cache_read', 0)
        total_input = tokens.get('input', 0) + cache_read

        if total_input == 0:
            return None

        # キャッシュヒット率計算
        hit_rate = (cache_read / total_input) * 100

        if hit_rate < 50:  # 50%未満なら通知しない
            return None

        project_name = session_info.get('project_name', 'Unknown')

        return {
            'title': "⚡ 高効率キャッシュ",
            'message': f"{project_name} | キャッシュヒット率: {hit_rate:.1f}%",
            'level': NotificationLevel.SUCCESS.value
        }

    @staticmethod
    def daily_summary(sessions: list, date: str) -> Dict[str, str]:
        """日次サマリー通知"""
        if not sessions:
            return None

        total_cost = sum(s.get('cost', {}).get('last_session', 0) for s in sessions)
        total_tokens = sum(s.get('tokens', {}).get('total', 0) for s in sessions)
        total_changes = sum(abs(s.get('code_changes', {}).get('net_change', 0)) for s in sessions)

        message_parts = [
            f"セッション数: {len(sessions)}",
            f"コスト: ${total_cost:.4f}",
            f"トークン: {total_tokens:,}",
            f"コード変更: {total_changes} 行"
        ]

        return {
            'title': f"📅 {date} の作業サマリー",
            'message': " | ".join(message_parts),
            'level': NotificationLevel.INFO.value
        }

    @staticmethod
    def custom(title: str, message: str, level: NotificationLevel = NotificationLevel.INFO) -> Dict[str, str]:
        """カスタム通知"""
        return {
            'title': title,
            'message': message,
            'level': level.value
        }


class NotificationBuilder:
    """通知メッセージビルダー"""

    def __init__(self):
        self.templates = NotificationTemplates()

    def build_all_notifications(self, session_info: Dict[str, Any]) -> list:
        """セッション情報から全ての該当通知を生成"""
        notifications = []

        # 基本完了通知
        notifications.append(
            self.templates.session_complete(session_info)
        )

        # 条件付き通知
        notif_methods = [
            self.templates.high_cost_warning,
            self.templates.token_milestone,
            self.templates.large_code_change,
            self.templates.long_session,
            self.templates.cache_efficiency
        ]

        for method in notif_methods:
            notif = method(session_info)
            if notif:
                notifications.append(notif)

        return [n for n in notifications if n]

    def build_compact_notification(self, session_info: Dict[str, Any]) -> Dict[str, str]:
        """コンパクトな単一通知を生成"""
        # セッションデータがない場合
        has_data = session_info.get('has_session_data', False)

        if not has_data:
            project_name = session_info.get('project_name', 'Unknown')
            return {
                'title': "✅ Claude Code 完了",
                'message': f"{project_name}",
                'level': NotificationLevel.SUCCESS.value
            }

        # 最も重要な情報のみを含む通知
        project_name = session_info.get('project_name', 'Unknown')
        cost_val = session_info.get('cost', {}).get('last_session', 0)
        tokens = session_info.get('tokens', {}).get('total', 0)
        changes = session_info.get('code_changes', {}).get('net_change', 0)

        message_parts = [project_name]

        # データがある項目のみ追加
        if cost_val > 0:
            cost = session_info.get('cost', {}).get('formatted', '$0.0000')
            message_parts.append(cost)

        if tokens > 0:
            message_parts.append(f"{tokens:,}t")

        if changes != 0:
            message_parts.append(f"{changes:+d}L")

        return {
            'title': "✅ Claude セッション完了",
            'message': " | ".join(message_parts),
            'level': NotificationLevel.SUCCESS.value
        }

    def build_detailed_notification(self, session_info: Dict[str, Any]) -> Dict[str, str]:
        """詳細な通知を生成"""
        project_name = session_info.get('project_name', 'Unknown')
        cost = session_info.get('cost', {}).get('formatted', '$0.0000')
        tokens = session_info.get('tokens', {})
        duration = session_info.get('duration', {}).get('formatted', '0ms')
        changes = session_info.get('code_changes', {})

        details = [
            f"プロジェクト: {project_name}",
            f"コスト: {cost}",
            f"トークン: {tokens.get('total', 0):,}",
            f"時間: {duration}",
            f"変更: +{changes.get('lines_added', 0)} -{changes.get('lines_removed', 0)}"
        ]

        return {
            'title': "Claude Code セッション詳細",
            'message': "\n".join(details),
            'level': NotificationLevel.INFO.value
        }


def main():
    """テスト用メイン処理"""
    # サンプルセッション情報
    sample_session = {
        'project_name': 'test-project',
        'cost': {'last_session': 0.5234, 'formatted': '$0.5234'},
        'tokens': {'total': 125000, 'input': 80000, 'output': 45000, 'cache_read': 200000},
        'duration': {'total_ms': 1800000, 'formatted': '30.0m'},
        'code_changes': {'lines_added': 150, 'lines_removed': 80, 'net_change': 70}
    }

    builder = NotificationBuilder()

    print("=== コンパクト通知 ===")
    compact = builder.build_compact_notification(sample_session)
    print(f"Title: {compact['title']}")
    print(f"Message: {compact['message']}\n")

    print("=== 全通知 ===")
    all_notifs = builder.build_all_notifications(sample_session)
    for notif in all_notifs:
        print(f"[{notif['level'].upper()}] {notif['title']}")
        print(f"  {notif['message']}\n")


if __name__ == "__main__":
    main()
