#!/usr/bin/env python3
"""
Claude Code Advanced Notification System
セッション情報を活用した詳細な通知システム
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 同じディレクトリのモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))

from session_monitor import SessionMonitor
from notification_templates import NotificationBuilder, NotificationLevel
from security_validator import SecurityValidator


class NotificationFormatter:
    """通知メッセージのフォーマッター"""

    @staticmethod
    def format_for_terminal_notifier(notification: Dict[str, str], session_info: Optional[Dict[str, Any]] = None) -> List[str]:
        """terminal-notifier用にフォーマット（高度な機能対応）"""
        args = [
            'terminal-notifier',
            '-title', notification['title'],
            '-message', notification['message'],
            '-sender', 'com.apple.Terminal',
            '-group', 'claude-code-notifications',
            '-activate', 'com.apple.Terminal'  # クリック時にターミナルを前面に
        ]

        # サブタイトルを追加（プロジェクト名）
        if session_info:
            project_name = session_info.get('project_name', '')
            if project_name:
                args.extend(['-subtitle', f'📁 {project_name}'])

        # レベルに応じてサウンドを変更
        sound_map = {
            'success': 'Glass',
            'info': 'Tink',
            'warning': 'Basso',
            'milestone': 'Hero'
        }
        sound = sound_map.get(notification.get('level', 'info'), 'Glass')
        args.extend(['-sound', sound])

        # 通知の有効期限を設定（重要度に応じて）
        timeout_map = {
            'success': '5',
            'info': '3',
            'warning': '10',
            'milestone': '10'
        }
        timeout = timeout_map.get(notification.get('level', 'info'), '5')
        args.extend(['-timeout', timeout])

        return args

    @staticmethod
    def format_for_osascript(notification: Dict[str, str]) -> str:
        """osascript用にフォーマット"""
        sound_map = {
            'success': 'Glass',
            'info': 'Tink',
            'warning': 'Basso',
            'milestone': 'Hero'
        }
        sound = sound_map.get(notification.get('level', 'info'), 'Glass')

        return (
            f'display notification "{notification["message"]}" '
            f'with title "{notification["title"]}" '
            f'sound name "{sound}"'
        )

    @staticmethod
    def format_for_log(notification: Dict[str, str]) -> str:
        """ログファイル用にフォーマット"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level = notification.get('level', 'info').upper()
        return f"[{timestamp}] [{level}] {notification['title']}: {notification['message']}"


class NotificationDelivery:
    """通知配信システム"""

    def __init__(self, debug: bool = False):
        self.formatter = NotificationFormatter()
        self.home = Path.home()
        self.log_file = self.home / ".claude-monitor" / "logs" / "notifications.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.debug = debug
        self.session_info = None  # セッション情報を保持

    def _has_terminal_notifier(self) -> bool:
        """terminal-notifierが利用可能かチェック"""
        try:
            subprocess.run(
                ['which', 'terminal-notifier'],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def send_via_terminal_notifier(self, notification: Dict[str, str]) -> bool:
        """terminal-notifier経由で通知を送信"""
        if not self._has_terminal_notifier():
            if self.debug:
                print("terminal-notifier が見つかりません", file=sys.stderr)
            return False

        try:
            args = self.formatter.format_for_terminal_notifier(notification, self.session_info)

            if self.debug:
                print(f"terminal-notifier コマンド: {' '.join(args)}", file=sys.stderr)

            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"terminal-notifier エラー: {e}", file=sys.stderr)
            return False

    def send_via_osascript(self, notification: Dict[str, str]) -> bool:
        """osascript経由で通知を送信"""
        try:
            script = self.formatter.format_for_osascript(notification)
            subprocess.Popen(
                ['osascript', '-e', script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"osascript エラー: {e}", file=sys.stderr)
            return False

    def play_sound(self, notification: Dict[str, str]) -> bool:
        """サウンドを再生"""
        sound_map = {
            'success': 'Glass',
            'info': 'Tink',
            'warning': 'Basso',
            'milestone': 'Hero'
        }
        sound = sound_map.get(notification.get('level', 'info'), 'Glass')

        try:
            subprocess.Popen(
                ['afplay', f'/System/Library/Sounds/{sound}.aiff'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False

    def log_to_file(self, notification: Dict[str, str]):
        """ファイルにログ記録"""
        try:
            log_line = self.formatter.format_for_log(notification)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception as e:
            print(f"ログ記録エラー: {e}", file=sys.stderr)

    def send_notification(self, notification: Dict[str, str]):
        """通知を複数の方法で送信"""
        if not notification:
            return

        # セキュリティ検証
        validator = SecurityValidator()
        is_safe, msg = validator.validate_notification_data(notification)

        if not is_safe:
            print(f"セキュリティ検証失敗: {msg}", file=sys.stderr)
            # サニタイズして再試行
            notification['title'] = validator.sanitize_string(notification.get('title', ''), 256)
            notification['message'] = validator.sanitize_string(notification.get('message', ''), 4096)

            if self.debug:
                print(f"通知データをサニタイズしました", file=sys.stderr)

        # 優先順位順に送信を試みる
        methods = [
            self.send_via_terminal_notifier,
            self.send_via_osascript,
        ]

        success = False
        for method in methods:
            if method(notification):
                success = True
                break

        # サウンド再生（バックグラウンド）
        self.play_sound(notification)

        # 常にログに記録
        self.log_to_file(notification)

        if not success:
            print(f"通知送信失敗: {notification['title']}", file=sys.stderr)

    def send_multiple(self, notifications: List[Dict[str, str]]):
        """複数の通知を送信"""
        for notification in notifications:
            self.send_notification(notification)


class NotificationConfig:
    """通知設定管理"""

    def __init__(self):
        self.config_file = Path.home() / ".claude-monitor" / "notification_config.json"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        default_config = {
            'enabled': True,
            'mode': 'compact',  # compact, detailed, all
            'cost_threshold': 1.0,
            'large_change_threshold': 100,
            'long_session_minutes': 30,
            'enable_milestones': True,
            'enable_warnings': True,
            'quiet_hours': {
                'enabled': False,
                'start': '22:00',
                'end': '08:00'
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception:
                pass

        return default_config

    def save_config(self):
        """設定をファイルに保存"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def is_quiet_hours(self) -> bool:
        """現在が静音時間帯かチェック"""
        if not self.config['quiet_hours']['enabled']:
            return False

        now = datetime.now().time()
        start = datetime.strptime(self.config['quiet_hours']['start'], '%H:%M').time()
        end = datetime.strptime(self.config['quiet_hours']['end'], '%H:%M').time()

        if start <= end:
            return start <= now <= end
        else:  # 日をまたぐ場合
            return now >= start or now <= end


class AdvancedNotificationSystem:
    """高度な通知システム統合クラス"""

    def __init__(self, debug: bool = False):
        self.monitor = SessionMonitor()
        self.builder = NotificationBuilder()
        self.delivery = NotificationDelivery(debug=debug)
        self.config = NotificationConfig()
        self.debug = debug

    def notify_session_complete(self, verbose: bool = False):
        """セッション完了時の通知"""
        if not self.config.config['enabled']:
            return

        if self.config.is_quiet_hours():
            if verbose:
                print("静音時間帯のため通知をスキップ")
            return

        # セッション情報取得
        session_info = self.monitor.get_session_info()
        if not session_info:
            if verbose:
                print("セッション情報が見つかりません")
            return

        # session_infoをdeliveryに渡す
        self.delivery.session_info = session_info

        # モードに応じて通知生成
        mode = self.config.config['mode']

        if mode == 'compact':
            notification = self.builder.build_compact_notification(session_info)
            self.delivery.send_notification(notification)

        elif mode == 'detailed':
            notification = self.builder.build_detailed_notification(session_info)
            self.delivery.send_notification(notification)

        elif mode == 'all':
            notifications = self.builder.build_all_notifications(session_info)
            self.delivery.send_multiple(notifications)

        # セッションログ記録
        self.monitor.log_session(session_info)

        # スナップショット保存
        if verbose:
            snapshot = self.monitor.save_session_snapshot(session_info)
            print(f"スナップショット保存: {snapshot}")

    def notify_custom(self, title: str, message: str, level: str = 'info'):
        """カスタム通知を送信"""
        if not self.config.config['enabled']:
            return

        notification = {
            'title': title,
            'message': message,
            'level': level
        }

        self.delivery.send_notification(notification)

    def show_status(self):
        """現在のステータスを表示"""
        print("=== Claude Code 通知システム ===")
        print(f"有効: {self.config.config['enabled']}")
        print(f"モード: {self.config.config['mode']}")
        print(f"静音時間帯: {'有効' if self.config.config['quiet_hours']['enabled'] else '無効'}")
        print(f"ログファイル: {self.delivery.log_file}")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='Claude Code Advanced Notification System')
    parser.add_argument('--mode', choices=['compact', 'detailed', 'all'],
                        help='通知モード')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='詳細出力')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='デバッグモード')
    parser.add_argument('--custom', nargs=2, metavar=('TITLE', 'MESSAGE'),
                        help='カスタム通知を送信')
    parser.add_argument('--status', action='store_true',
                        help='ステータスを表示')
    parser.add_argument('--enable', action='store_true',
                        help='通知を有効化')
    parser.add_argument('--disable', action='store_true',
                        help='通知を無効化')

    args = parser.parse_args()

    system = AdvancedNotificationSystem(debug=args.debug)

    if args.enable:
        system.config.config['enabled'] = True
        system.config.save_config()
        print("通知を有効化しました")
        return

    if args.disable:
        system.config.config['enabled'] = False
        system.config.save_config()
        print("通知を無効化しました")
        return

    if args.mode:
        system.config.config['mode'] = args.mode
        system.config.save_config()
        print(f"通知モードを '{args.mode}' に設定しました")

    if args.status:
        system.show_status()
        return

    if args.custom:
        title, message = args.custom
        system.notify_custom(title, message)
        return

    # デフォルト: セッション完了通知
    system.notify_session_complete(verbose=args.verbose)


if __name__ == "__main__":
    main()
