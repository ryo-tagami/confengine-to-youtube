"""スマートコンストラクタ用センチネル"""

from __future__ import annotations

from typing import Final


class Sentinel:
    """直接インスタンス化を防ぐためのセンチネルクラス"""

    __slots__ = ()


SENTINEL: Final = Sentinel()
