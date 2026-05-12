import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestHashPin:
    """Testy dla funkcji hashowania PIN."""

    def test_hash_pin_returns_tuple(self):
        from main import MainWindow
        result = MainWindow._hash_pin("1234")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], bytes)

    def test_hash_pin_different_salts(self):
        from main import MainWindow
        hash1 = MainWindow._hash_pin("1234")
        hash2 = MainWindow._hash_pin("1234")
        assert hash1[0] != hash2[0]
        assert hash1[1] != hash2[1]

    def test_verify_pin_correct(self):
        from main import MainWindow
        pin, salt = MainWindow._hash_pin("1234")
        assert MainWindow._verify_pin("1234", pin, salt) is True

    def test_verify_pin_incorrect(self):
        from main import MainWindow
        pin, salt = MainWindow._hash_pin("1234")
        assert MainWindow._verify_pin("0000", pin, salt) is False


class TestTokenCalculation:
    """Testy dla obliczania tokenów."""

    def test_empty_text(self):
        from main import MainWindow
        mw = MainWindow()
        mw._active_note_id = "test"
        mw._notes = [{"id": "test", "name": "Test", "content": ""}]
        mw.editor.setPlainText("")
        mw._update_counters()
        tokens_text = mw.tokens_label.text()
        assert "~0 tokenów" in tokens_text

    def test_short_text(self):
        from main import MainWindow
        mw = MainWindow()
        mw._active_note_id = "test"
        mw._notes = [{"id": "test", "name": "Test", "content": "abc"}]
        mw.editor.setPlainText("abc")
        mw._update_counters()
        tokens_text = mw.tokens_label.text()
        assert "1 tokenów" in tokens_text or "0 tokenów" in tokens_text

    def test_long_text(self):
        from main import MainWindow
        mw = MainWindow()
        mw._active_note_id = "test"
        mw._notes = [{"id": "test", "name": "Test", "content": "a" * 100}]
        mw.editor.setPlainText("a" * 100)
        mw._update_counters()
        tokens_text = mw.tokens_label.text()
        assert "25 tokenów" in tokens_text


class TestDataMigration:
    """Testy dla migracji danych."""

    def test_missing_content_key(self):
        from main import MainWindow
        mw = MainWindow()
        note = {"id": "123", "name": "Test"}
        mw._notes = [note]
        for note in mw._notes:
            note.setdefault("content", "")
            note.setdefault("created_at", datetime.now().isoformat())
            note.setdefault("updated_at", datetime.now().isoformat())
        assert mw._notes[0].get("content") == ""
        assert "created_at" in mw._notes[0]
        assert "updated_at" in mw._notes[0]

    def test_complete_note_unchanged(self):
        from main import MainWindow
        mw = MainWindow()
        now = datetime.now().isoformat()
        note = {"id": "123", "name": "Test", "content": "Hello", "created_at": now, "updated_at": now}
        mw._notes = [note]
        for note in mw._notes:
            note.setdefault("content", "")
            note.setdefault("created_at", datetime.now().isoformat())
            note.setdefault("updated_at", datetime.now().isoformat())
        assert mw._notes[0]["content"] == "Hello"
        assert mw._notes[0]["created_at"] == now


class TestNavigation:
    """Testy dla nawigacji między notatkami."""

    def test_next_note_circular(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [
            {"id": "1", "name": "Note 1", "content": ""},
            {"id": "2", "name": "Note 2", "content": ""},
            {"id": "3", "name": "Note 3", "content": ""},
        ]
        mw._active_note_id = "1"
        mw._buttons = []
        mw._select_note = Mock()
        mw._next_note()
        mw._select_note.assert_called_with("2")

    def test_next_note_wraps(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [
            {"id": "1", "name": "Note 1", "content": ""},
            {"id": "2", "name": "Note 2", "content": ""},
        ]
        mw._active_note_id = "2"
        mw._buttons = []
        mw._select_note = Mock()
        mw._next_note()
        mw._select_note.assert_called_with("1")

    def test_prev_note_wraps(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [
            {"id": "1", "name": "Note 1", "content": ""},
            {"id": "2", "name": "Note 2", "content": ""},
        ]
        mw._active_note_id = "1"
        mw._buttons = []
        mw._select_note = Mock()
        mw._prev_note()
        mw._select_note.assert_called_with("2")


class TestReorderNotes:
    """Testy dla zmiany kolejności notatek."""

    def test_reorder_updates_position(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [
            {"id": "1", "name": "Note 1", "content": "", "updated_at": "2025-01-01T00:00:00"},
            {"id": "2", "name": "Note 2", "content": "", "updated_at": "2025-01-02T00:00:00"},
            {"id": "3", "name": "Note 3", "content": "", "updated_at": "2025-01-03T00:00:00"},
        ]
        mw._reorder_notes("1", 2)
        assert mw._notes[0]["id"] == "2"
        assert mw._notes[1]["id"] == "3"
        assert mw._notes[2]["id"] == "1"

    def test_reorder_does_not_change_updated_at(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [
            {"id": "1", "name": "Note 1", "content": "", "updated_at": "2025-01-01T00:00:00"},
            {"id": "2", "name": "Note 2", "content": "", "updated_at": "2025-01-01T00:00:00"},
        ]
        mw._reorder_notes("1", 1)
        assert mw._notes[0]["updated_at"] == "2025-01-01T00:00:00"


class TestDirtyFlag:
    """Testy dla flagi _dirty."""

    def test_dirty_resetzt_after_save(self):
        from main import MainWindow
        mw = MainWindow()
        mw._dirty = True
        mw._notes = []
        mw._active_note_id = None
        mw._select_note = Mock()
        mw._font_size = 11
        mw._theme_name = "Klasyczny"

        mw._save_current()
        assert mw._dirty is False


class TestWindowTitle:
    """Testy dla tytułu okna."""

    def test_title_changes_with_note(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [{"id": "1", "name": "Test Note", "content": "Hello"}]
        mw._buttons = []
        mw._select_note("1")
        assert "Test Note" in mw.windowTitle()

    def test_title_reset_on_deselect(self):
        from main import MainWindow
        mw = MainWindow()
        mw._notes = [{"id": "1", "name": "Test Note", "content": "Hello"}]
        mw._active_note_id = "1"
        mw._buttons = []
        mw._deselect_note()
        assert mw.windowTitle() == "Anti-Spaghetti"


class TestEscapeKey:
    """Testy dla klawisza Escape w dialogach."""

    def test_draggable_dialog_escape(self):
        from main import DraggableDialog
        from PyQt6.QtCore import QEvent

        mw = QApplication.activeWindow()
        if mw is None:
            mw = QWidget()
        dialog = DraggableDialog(mw)
        dialog.accept = Mock()
        dialog.reject = Mock()

        event = Mock()
        event.key.return_value = Qt.Key.Key_Escape
        dialog.keyPressEvent(event)
        dialog.reject.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
