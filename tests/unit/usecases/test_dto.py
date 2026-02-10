"""VideoUpdatePreview のプロパティテスト"""

import pytest

from confengine_to_youtube.usecases.dto import VideoUpdatePreview


def _create_preview(
    *,
    current_title: str = "Current Title",
    new_title: str = "New Title",
    current_description: str = "Current description",
    new_description: str = "New description",
) -> VideoUpdatePreview:
    return VideoUpdatePreview(
        session_key="2025-01-01T10:00:00#Room1",
        video_id="abc123",
        current_title=current_title,
        new_title=new_title,
        current_description=current_description,
        new_description=new_description,
    )


class TestHasTitleChanges:
    def test_returns_true_when_title_differs(self) -> None:
        preview = _create_preview(
            current_title="Old Title",
            new_title="New Title",
        )

        assert preview.has_title_changes is True

    def test_returns_false_when_title_same(self) -> None:
        preview = _create_preview(
            current_title="Same Title",
            new_title="Same Title",
        )

        assert preview.has_title_changes is False


class TestHasDescriptionChanges:
    def test_returns_true_when_description_differs(self) -> None:
        preview = _create_preview(
            current_description="Old description",
            new_description="New description",
        )

        assert preview.has_description_changes is True

    def test_returns_false_when_description_same(self) -> None:
        preview = _create_preview(
            current_description="Same description",
            new_description="Same description",
        )

        assert preview.has_description_changes is False


class TestHasChanges:
    @pytest.mark.parametrize(
        ("current_title", "new_title", "current_desc", "new_desc", "expected"),
        [
            pytest.param("Old", "New", "Same", "Same", True, id="title_only"),
            pytest.param("Same", "Same", "Old", "New", True, id="description_only"),
            pytest.param("Old", "New", "Old", "New", True, id="both_changed"),
            pytest.param("Same", "Same", "Same", "Same", False, id="no_changes"),
        ],
    )
    def test_returns_expected_value(
        self,
        current_title: str,
        new_title: str,
        current_desc: str,
        new_desc: str,
        *,
        expected: bool,
    ) -> None:
        preview = _create_preview(
            current_title=current_title,
            new_title=new_title,
            current_description=current_desc,
            new_description=new_desc,
        )

        assert preview.has_changes is expected
