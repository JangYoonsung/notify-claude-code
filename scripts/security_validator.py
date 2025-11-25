#!/usr/bin/env python3
"""
Security Validator for Claude Code Notification System
セキュリティチェック機能
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Tuple


class SecurityValidator:
    """セキュリティ検証クラス"""

    # 危険なパターン
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',  # ルートディレクトリの削除
        r'rm\s+-rf\s+\*',  # 全ファイル削除
        r'dd\s+if=/dev/(zero|random)\s+of=',  # ディスク破壊
        r':\(\)\{\s*:\|:&\s*\};:',  # フォークボム
        r'curl.*\|\s*sh',  # パイプ経由の実行
        r'wget.*\|\s*sh',  # パイプ経由の実行
        r'eval\s+\$\(',  # eval での実行
        r'exec\s+\$\(',  # exec での実行
    ]

    # 許可されたディレクトリ
    ALLOWED_DIRECTORIES = [
        '/Users',
        '/home',
        '/tmp',
        '/var/tmp',
    ]

    @staticmethod
    def validate_command(command: str) -> Tuple[bool, str]:
        """
        コマンドの安全性を検証

        Returns:
            (is_safe, message)
        """
        # 危険なパターンのチェック
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"危険なパターンが検出されました: {pattern}"

        return True, "OK"

    @staticmethod
    def validate_path(path: str) -> Tuple[bool, str]:
        """
        パスの安全性を検証（パストラバーサル攻撃対策）

        Returns:
            (is_safe, message)
        """
        # パストラバーサルのチェック
        if '..' in path:
            return False, "パストラバーサルが検出されました"

        # 絶対パスの検証
        try:
            abs_path = os.path.abspath(path)

            # 許可されたディレクトリ配下かチェック
            is_allowed = any(
                abs_path.startswith(allowed_dir)
                for allowed_dir in SecurityValidator.ALLOWED_DIRECTORIES
            )

            if not is_allowed:
                return False, f"許可されていないパスです: {abs_path}"

        except Exception as e:
            return False, f"パス検証エラー: {e}"

        return True, "OK"

    @staticmethod
    def validate_notification_data(notification: Dict[str, str]) -> Tuple[bool, str]:
        """
        通知データの安全性を検証

        Returns:
            (is_safe, message)
        """
        # タイトルとメッセージの長さチェック
        title = notification.get('title', '')
        message = notification.get('message', '')

        if len(title) > 256:
            return False, "タイトルが長すぎます"

        if len(message) > 4096:
            return False, "メッセージが長すぎます"

        # 制御文字のチェック
        control_chars = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')

        if control_chars.search(title):
            return False, "タイトルに不正な文字が含まれています"

        if control_chars.search(message):
            return False, "メッセージに不正な文字が含まれています"

        return True, "OK"

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1024) -> str:
        """
        文字列のサニタイズ

        Args:
            text: サニタイズ対象の文字列
            max_length: 最大長

        Returns:
            サニタイズ済み文字列
        """
        # 制御文字を削除
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        # 長さ制限
        if len(text) > max_length:
            text = text[:max_length] + '...'

        return text

    @staticmethod
    def check_file_permissions(file_path: str) -> Tuple[bool, str]:
        """
        ファイルのパーミッションをチェック

        Returns:
            (is_safe, message)
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return True, "ファイルが存在しません（新規作成）"

            # ファイルのパーミッションを確認
            stat_info = path.stat()
            mode = stat_info.st_mode

            # 他者への書き込み権限がある場合は警告
            if mode & 0o002:  # world-writable
                return False, "他者への書き込み権限があります"

            # グループへの書き込み権限の確認
            if mode & 0o020:  # group-writable
                # 所有者が自分でない場合は警告
                if stat_info.st_uid != os.getuid():
                    return False, "所有者ではないファイルです"

            return True, "OK"

        except Exception as e:
            return False, f"パーミッションチェックエラー: {e}"

    @staticmethod
    def validate_json_data(data: str) -> Tuple[bool, str]:
        """
        JSONデータの検証

        Returns:
            (is_valid, message)
        """
        import json

        try:
            # JSONとしてパース可能かチェック
            json.loads(data)

            # サイズチェック（10MB以下）
            if len(data) > 10 * 1024 * 1024:
                return False, "JSONデータが大きすぎます"

            return True, "OK"

        except json.JSONDecodeError as e:
            return False, f"不正なJSON形式: {e}"
        except Exception as e:
            return False, f"JSON検証エラー: {e}"


def main():
    """テスト用メイン処理"""
    validator = SecurityValidator()

    print("=== セキュリティバリデータ テスト ===\n")

    # コマンド検証テスト
    test_commands = [
        "ls -la",
        "rm -rf /",
        "curl http://example.com | sh",
        "python script.py"
    ]

    print("コマンド検証:")
    for cmd in test_commands:
        is_safe, msg = validator.validate_command(cmd)
        status = "✓" if is_safe else "✗"
        print(f"  {status} {cmd}: {msg}")

    print("\nパス検証:")
    test_paths = [
        "/Users/test/file.txt",
        "/Users/test/../../../etc/passwd",
        "/etc/shadow",
        "/tmp/test.log"
    ]

    for path in test_paths:
        is_safe, msg = validator.validate_path(path)
        status = "✓" if is_safe else "✗"
        print(f"  {status} {path}: {msg}")

    print("\n通知データ検証:")
    test_notifications = [
        {'title': 'Test', 'message': 'Hello World'},
        {'title': 'A' * 300, 'message': 'Too long title'},
        {'title': 'Test\x00', 'message': 'Control char'}
    ]

    for notif in test_notifications:
        is_safe, msg = validator.validate_notification_data(notif)
        status = "✓" if is_safe else "✗"
        print(f"  {status} {notif.get('title', '')[:20]}: {msg}")


if __name__ == "__main__":
    main()
