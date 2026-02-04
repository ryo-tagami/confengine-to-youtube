"""mutmut ラッパースクリプト

macOS で mutmut の fork 後に setproctitle が CoreFoundation を呼び出し
SIGSEGV が発生する問題を回避する。

See: https://github.com/boxed/mutmut/issues/446
"""

from __future__ import annotations

import platform

if platform.system() == "Darwin":
    import setproctitle

    setproctitle.setproctitle = lambda _title: None  # type: ignore[assignment]

from mutmut.__main__ import cli

cli()
