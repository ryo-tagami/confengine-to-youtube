from datetime import datetime
from io import StringIO
from zoneinfo import ZoneInfo

from confengine_to_youtube.adapters.mapping_file_writer import MappingFileWriter
from confengine_to_youtube.domain.conference_schedule import ConferenceSchedule
from confengine_to_youtube.domain.schedule_slot import ScheduleSlot
from confengine_to_youtube.domain.session import Session
from confengine_to_youtube.domain.session_abstract import SessionAbstract
from confengine_to_youtube.domain.speaker import Speaker


class TestMappingFileWriter:
    def test_write_single_session(self, jst: ZoneInfo) -> None:
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title="Clean Architecture入門",
                    track="技術",
                    speakers=(Speaker(first_name="", last_name="田中太郎"),),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session1",
                ),
            ),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      10:00:\n"
            "        # Clean Architecture入門 - 田中太郎\n"
            "        video_id: ''\n"
        )
        assert result == expected

    def test_write_multiple_speakers(self, jst: ZoneInfo) -> None:
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=11,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title="ペアプロ実践",
                    track="技術",
                    speakers=(
                        Speaker(first_name="", last_name="田中太郎"),
                        Speaker(first_name="", last_name="山田花子"),
                    ),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session1",
                ),
            ),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      11:00:\n"
            "        # ペアプロ実践 - 田中太郎, 山田花子\n"
            "        video_id: ''\n"
        )
        assert result == expected

    def test_write_multiple_days(self, jst: ZoneInfo) -> None:
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=8,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title="Day2 Session",
                    track="技術",
                    speakers=(Speaker(first_name="", last_name="佐藤"),),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session2",
                ),
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title="Day1 Session",
                    track="技術",
                    speakers=(Speaker(first_name="", last_name="鈴木"),),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session1",
                ),
            ),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      10:00:\n"
            "        # Day1 Session - 鈴木\n"
            "        video_id: ''\n"
            "  2026-01-08:\n"
            "    Hall A:\n"
            "      10:00:\n"
            "        # Day2 Session - 佐藤\n"
            "        video_id: ''\n"
        )
        assert result == expected

    def test_write_multiple_rooms(self, jst: ZoneInfo) -> None:
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall B",
                    ),
                    title="Session in Hall B",
                    track="技術",
                    speakers=(Speaker(first_name="", last_name="佐藤"),),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session2",
                ),
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title="Session in Hall A",
                    track="技術",
                    speakers=(Speaker(first_name="", last_name="鈴木"),),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session1",
                ),
            ),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      10:00:\n"
            "        # Session in Hall A - 鈴木\n"
            "        video_id: ''\n"
            "    Hall B:\n"
            "      10:00:\n"
            "        # Session in Hall B - 佐藤\n"
            "        video_id: ''\n"
        )
        assert result == expected

    def test_write_empty_sessions(self, jst: ZoneInfo) -> None:
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions: {}\n"
        )
        assert result == expected

    def test_write_session_without_speakers(self, jst: ZoneInfo) -> None:
        """スピーカーなしのセッションではタイトルのみがコメントに出力される"""
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title="パネルディスカッション",
                    track="技術",
                    speakers=(),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session1",
                ),
            ),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      10:00:\n"
            "        # パネルディスカッション\n"
            "        video_id: ''\n"
        )
        assert result == expected

    def test_write_long_title_wraps_at_word_boundary(self, jst: ZoneInfo) -> None:
        """長いタイトルは分かち書き単位で折り返される"""
        # タイトル + " - " + スピーカー名 の合計が70文字幅を超えるケース
        # タイトル34文字 (68幅) + " - " (3幅) + スピーカー4文字 (8幅) = 79幅
        long_title = (
            "アジャイル開発における継続的インテグレーションの実践と課題について"
        )
        schedule = ConferenceSchedule(
            conf_id="test-conf",
            timezone=jst,
            sessions=(
                Session(
                    slot=ScheduleSlot(
                        timeslot=datetime(
                            year=2026,
                            month=1,
                            day=7,
                            hour=10,
                            minute=0,
                            tzinfo=jst,
                        ),
                        room="Hall A",
                    ),
                    title=long_title,
                    track="技術",
                    speakers=(Speaker(first_name="", last_name="田中太郎"),),
                    abstract=SessionAbstract(content="概要"),
                    url="https://example.com/session1",
                ),
            ),
        )
        generated_at = datetime(
            year=2026,
            month=1,
            day=19,
            hour=10,
            minute=30,
            second=0,
            tzinfo=jst,
        )

        writer = MappingFileWriter()
        output = StringIO()
        writer.write(
            schedule=schedule,
            output=output,
            generated_at=generated_at,
        )
        result = output.getvalue()

        # タイトル全体 + " - 田中太郎" が1行に収まらないので改行される
        long_comment = (
            "        # アジャイル開発における継続的インテグレーションの"
            "実践と課題について - \n"
        )
        expected = (
            "# ConfEngine Mapping Template\n"
            "# Generated: 2026-01-19T10:30:00+09:00\n"
            "conf_id: test-conf\n"
            "# プレイリストID (YouTube Studioで事前に作成)\n"
            "# 例: PLxxxxxxxxxxxxxxxx\n"
            "playlist_id: ''\n"
            "# ハッシュタグ\n"
            "# 例:\n"
            "#   hashtags:\n"
            "#     - '#RSGT2026'\n"
            "#     - '#Agile'\n"
            "hashtags: []\n"
            "# フッター (複数行の場合はリテラルブロック `|` を使用)\n"
            "# 例:\n"
            "#   footer: |\n"
            "#     1行目\n"
            "#     2行目\n"
            "footer: ''\n"
            "# セッション\n"
            "# セッションごとに更新対象を制御できます (デフォルト: true):\n"
            "# 例:\n"
            "#   sessions:\n"
            '#     "2026-01-07":\n'
            '#       "Hall A":\n'
            '#         "10:00":\n'
            '#           video_id: "abc123"\n'
            "#           update_title: false\n"
            "#           update_description: false\n"
            "sessions:\n"
            "  2026-01-07:\n"
            "    Hall A:\n"
            "      10:00:\n"
            f"{long_comment}"
            "        # 田中太郎\n"
            "        video_id: ''\n"
        )
        assert result == expected
