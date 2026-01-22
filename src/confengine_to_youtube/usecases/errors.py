"""ユースケース層の例外クラス"""

from __future__ import annotations


class VideoNotFoundError(Exception):
    """動画が見つからないエラー"""


class MappingFileError(Exception):
    """マッピングファイル読み込みエラー"""
