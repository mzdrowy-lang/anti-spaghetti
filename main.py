import sys
import json
import os
import uuid
import hashlib
import shutil
import re
import logging
import atexit
from pathlib import Path
from datetime import datetime

__version__ = "1.0.0"
__app_name__ = "Anti-Spaghetti"

# Konfiguracja logowania
log = logging.getLogger(__app_name__)
log.setLevel(logging.WARNING)
if not log.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(name)s [%(levelname)s] %(message)s"))
    log.addHandler(handler)

from PyQt6.QtGui import QFont, QPainter, QColor, QKeySequence, QShortcut, QFontDatabase, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QSize, QTimer, QRegularExpression, QRect, QEvent
try:
    import qtawesome
except ImportError:
    qtawesome = None
    log.warning("qtawesome nie zainstalowane – ikony nie beda widoczne")

def _icon(name: str, color: str):
    """Bezpieczne wywołanie qtawesome.icon z fallbackiem."""
    if qtawesome:
        return qtawesome.icon(name, color=color)
    from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPen
    pm = QPixmap(20, 20)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(color), 2))
    p.drawLine(4, 10, 16, 10)
    p.drawLine(10, 4, 10, 16)
    p.end()
    return QIcon(pm)

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QLineEdit,
    QDialog,
    QMenu,
    QSizePolicy,
)

# ──────────────────────────────────────────────
# STALE – kolory (oryginalne, NIEnaruszone)
# ──────────────────────────────────────────────
BG_APP        = "#1a1a18"
BG_EDITOR     = "#222220"
BG_BTN        = "#2b2b29"
BG_BTN_HOVER  = "#333331"
BG_BTN_ACTIVE = "#3d3d3a"
BG_BOTTOMBAR  = "#222220"
TEXT_MAIN     = "#e2e2d1"
TEXT_DIM      = "#888880"
ACCENT        = "#555550"
SEPARATOR     = "#3a3a38"

# ──────────────────────────────────────────────
# MOTYWY (dodatek – nie zmienia oryginalnych stalych)
# ──────────────────────────────────────────────
THEMES = {
    "Klasyczny": {
        "BG_APP": BG_APP, "BG_EDITOR": BG_EDITOR,
        "BG_BTN": BG_BTN, "BG_BTN_HOVER": BG_BTN_HOVER,
        "BG_BTN_ACTIVE": BG_BTN_ACTIVE, "BG_BOTTOMBAR": BG_BOTTOMBAR,
        "TEXT_MAIN": TEXT_MAIN, "TEXT_DIM": TEXT_DIM,
        "ACCENT": ACCENT, "SEPARATOR": SEPARATOR,
    },
    "Ciemny": {
        "BG_APP":        "#0d1117",
        "BG_EDITOR":     "#161b22",
        "BG_BTN":        "#161b22",
        "BG_BTN_HOVER":  "#1c2128",
        "BG_BTN_ACTIVE": "#1c2128",
        "BG_BOTTOMBAR":  "#0d1117",
        "TEXT_MAIN":     "#e6edf3",
        "TEXT_DIM":      "#7d8590",
        "ACCENT":        "#3b82f6",
        "SEPARATOR":     "#21262d",
    },
}

# ──────────────────────────────────────────────
# STALE – rozmiary
# ──────────────────────────────────────────────
SIZES = {
    "WINDOW_WIDTH":       700,
    "WINDOW_HEIGHT":      500,
    "WINDOW_MIN_W":       700,
    "WINDOW_MIN_H":       500,
    "SIDEBAR_DEF_W":      260,
    "SIDEBAR_MIN_W":      200,
    "SIDEBAR_MAX_W":      320,
    "HEADER_FONT_SIZE":   11,
    "BASE_FONT_SIZE":     11,
    "SMALL_FONT_SIZE":    10,
    "ICON_FONT_SIZE":     18,
    "BTN_HEIGHT":         32,
    "BTN_RADIUS":         10,
    "EDITOR_RADIUS":      12,
    "EDITOR_PAD":         16,
    "SCROLLBAR_W":         6,
    "SCROLLBAR_RADIUS":    3,
    "BOTTOM_BAR_H":       48,
    "BOTTOM_BAR_PAD":      8,
    "BOTTOM_BTN_SIZE":    36,
    "SEARCH_RADIUS":       8,
    "SIDEBAR_TOP_PAD":    12,
    "SIDEBAR_MARGIN":      8,
    "SIDEBAR_SPACING":     4,
    "SIDEBAR_LIST_TOP":    4,
    "SIDEBAR_LIST_BOT":    4,
    "SETTINGS_BTN_SIZE":  28,
    "ELIDE_PAD":          12,
    "DRAG_THRESHOLD":     10,
    "HEADER_PAD_LEFT":    20,
    "HEADER_PAD_TOP":     10,
    "HEADER_PAD_BOT":     10,
    "EDITOR_MARGIN_BOT":  12,
    "EDITOR_MARGIN_SIDE": 12,
    "VIEWPORT_MARGIN_R":  14,
    "RESIZE_MARGIN":      10,
    "FONT_SIZE_MIN":       8,
    "FONT_SIZE_MAX":      24,
}

# ──────────────────────────────────────────────
# QSS – szablony stylów (formatowanie po kluczach motywu)
# ──────────────────────────────────────────────
def _build_qss(template: str, colors: dict) -> str:
    return template.format_map(colors)

QSS_EDITOR_TPL = """
QPlainTextEdit {{
    background-color: {BG_EDITOR};
    color: {TEXT_MAIN};
    border: none;
    border-radius: {EDITOR_RADIUS}px;
    padding: {EDITOR_PAD}px;
    margin: 0px {EDITOR_MARGIN_SIDE}px {EDITOR_MARGIN_BOT}px {EDITOR_MARGIN_SIDE}px;
    selection-background-color: {ACCENT};
}}
QPlainTextEdit QScrollBar:vertical {{
    background: transparent;
    width: {SCROLLBAR_W}px;
    margin: 4px 0px;
}}
QPlainTextEdit QScrollBar::handle:vertical {{
    background: {ACCENT};
    border-radius: {SCROLLBAR_RADIUS}px;
    min-height: 20px;
}}
QPlainTextEdit QScrollBar::add-line:vertical,
QPlainTextEdit QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

QSS_SIDEBAR_BTN_TPL = """
QPushButton {{
    background-color: {BG_BTN};
    border: none;
    border-radius: {BTN_RADIUS}px;
}}
QPushButton:hover {{
    background-color: {BG_BTN_HOVER};
}}
QPushButton:checked {{
    background-color: {BG_BTN_ACTIVE};
}}
"""

QSS_SCROLLBAR_TPL = """
QScrollBar:vertical {{
    background: transparent;
    width: {SCROLLBAR_W}px;
    margin: 4px 0px;
}}
QScrollBar::handle:vertical {{
    background: {BG_APP};
    border-radius: {SCROLLBAR_RADIUS}px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

QSS_BOTTOMBAR_TPL = """
QWidget#BottomBar {{
    background-color: {BG_BOTTOMBAR};
    border-top: 1px solid {SEPARATOR};
}}
"""

QSS_BOTTOM_BTN_TPL = """
QPushButton {{
    background: transparent;
    border: none;
    border-radius: {SEARCH_RADIUS}px;
    min-width: {BOTTOM_BTN_SIZE}px;
    max-width: {BOTTOM_BTN_SIZE}px;
    min-height: {BOTTOM_BTN_SIZE}px;
    max-height: {BOTTOM_BTN_SIZE}px;
}}
QPushButton:hover {{
    background-color: {BG_BTN_HOVER};
}}
"""

QSS_SEARCH_TPL = """
QLineEdit {{
    background-color: {BG_BOTTOMBAR};
    color: {TEXT_MAIN};
    border: 1px solid {SEPARATOR};
    border-radius: {SEARCH_RADIUS}px;
    padding: 4px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit::placeholder {{
    color: {TEXT_DIM};
}}
"""

QSS_SETTINGS_BTN_TPL = """
QPushButton {{
    background: transparent;
    border: none;
    min-width: {SETTINGS_BTN_SIZE}px;
    max-width: {SETTINGS_BTN_SIZE}px;
    min-height: {SETTINGS_BTN_SIZE}px;
    max-height: {SETTINGS_BTN_SIZE}px;
}}
QPushButton:hover {{
    background-color: {BG_BTN_HOVER};
    border-radius: 4px;
}}
"""

def _default_qss(template: str) -> str:
    colors = dict(THEMES["Klasyczny"])
    colors.update(SIZES)
    return _build_qss(template, colors)

QSS_EDITOR      = _default_qss(QSS_EDITOR_TPL)
QSS_SIDEBAR_BTN = _default_qss(QSS_SIDEBAR_BTN_TPL)
QSS_SCROLLBAR   = _default_qss(QSS_SCROLLBAR_TPL)
QSS_BOTTOMBAR   = _default_qss(QSS_BOTTOMBAR_TPL)
QSS_BOTTOM_BTN  = _default_qss(QSS_BOTTOM_BTN_TPL)
QSS_SEARCH      = _default_qss(QSS_SEARCH_TPL)
QSS_SETTINGS_BTN = _default_qss(QSS_SETTINGS_BTN_TPL)


# ──────────────────────────────────────────────
# KLASA: DraggableDialog – dialog z przeciąganiem
# ──────────────────────────────────────────────
class DraggableDialog(QDialog):
    def __init__(self, parent, flags=Qt.WindowType.FramelessWindowHint):
        super().__init__(parent, flags)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

# ──────────────────────────────────────────────
# KLASA: SidebarButton
# ──────────────────────────────────────────────
class SidebarButton(QPushButton):
    """Przycisk wpisu w sidebarze z wlasnym rysowaniem tekstu."""

    def __init__(self, note_id: str, label: str, parent=None):
        super().__init__(parent)
        self._note_id = note_id
        self._label = label
        self._dragging = False
        self._drag_start_pos = None

        self.setFixedHeight(SIZES["BTN_HEIGHT"])
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCheckable(True)
        self.setText("")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(QSS_SIDEBAR_BTN)

        # menu kontekstowe (prawy klik)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        window = self.window()
        if isinstance(window, MainWindow):
            C = window._theme_colors
        else:
            C = {k: v for k, v in THEMES["Klasyczny"].items()}

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {C["BG_BTN"]};
                color: {C["TEXT_MAIN"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 6px;
                padding: 4px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        rename_action = menu.addAction("Zmień nazwę")
        delete_action = menu.addAction("Usuń wpis")
        action = menu.exec(self.mapToGlobal(pos))
        if action == delete_action:
            if isinstance(window, MainWindow):
                window._confirm_delete(self._note_id)
        elif action == rename_action:
            if isinstance(window, MainWindow):
                window._rename_note(self._note_id)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        rect = self.rect().adjusted(SIZES["ELIDE_PAD"], 0, -SIZES["ELIDE_PAD"], 0)
        elided = self.fontMetrics().elidedText(
            self._label, Qt.TextElideMode.ElideRight, rect.width()
        )
        window = self.window()
        if isinstance(window, MainWindow):
            text_color = QColor(window._theme_colors["TEXT_MAIN"])
        else:
            text_color = QColor(TEXT_MAIN)
        painter.setPen(text_color)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            elided,
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self._drag_start_pos is None:
            return
        if not self._dragging:
            if (
                event.pos() - self._drag_start_pos
            ).manhattanLength() < SIZES["DRAG_THRESHOLD"]:
                return
            self._dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.grabMouse()

        if self._dragging:
            try:
                global_pos = event.globalPosition().toPoint()
                parent = self.parentWidget()
                local_pos = parent.mapFromGlobal(global_pos)
                layout = parent.layout()

                # Autoscroll przy przeciaganiu
                from PyQt6.QtWidgets import QScrollArea
                scroll_area = self.window().findChild(QScrollArea)
                if scroll_area:
                    vbar = scroll_area.verticalScrollBar()
                    viewport_pos = scroll_area.viewport().mapFromGlobal(global_pos)
                    margin = 30
                    if viewport_pos.y() < margin:
                        vbar.setValue(vbar.value() - 15)
                    elif viewport_pos.y() > scroll_area.viewport().height() - margin:
                        vbar.setValue(vbar.value() + 15)

                target_index = None
                for i in range(layout.count() - 1):
                    item = layout.itemAt(i)
                    w = item.widget()
                    if w is None or w is self:
                        continue
                    geo = w.geometry()
                    if local_pos.y() < geo.center().y():
                        target_index = i
                        break

                if target_index is None:
                    target_index = max(0, layout.count() - 2)

                current_index = layout.indexOf(self)
                if current_index != target_index:
                    layout.insertWidget(target_index, self)
                    self._final_drag_index = target_index
            except Exception:
                self._dragging = False
                self._drag_start_pos = None
                self.setCursor(Qt.CursorShape.PointingHandCursor)
                if self.hasMouseGrab():
                    self.releaseMouse()

        event.accept()

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._drag_start_pos = None
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            if self.hasMouseGrab():
                self.releaseMouse()
            window = self.window()
            if isinstance(window, MainWindow):
                if hasattr(self, '_final_drag_index'):
                    window._reorder_notes(self._note_id, self._final_drag_index)
                    delattr(self, '_final_drag_index')
                window.save_notes()
            event.accept()
        else:
            self._drag_start_pos = None
            super().mouseReleaseEvent(event)


# ──────────────────────────────────────────────
# KLASA: MainWindow
# ──────────────────────────────────────────────
class MainWindow(QWidget):
    """Glowne okno aplikacji Anti-Spaghetti."""

    def __init__(self):
        super().__init__()
        self._notes: list[dict] = []
        self._buttons: list[SidebarButton] = []
        self._active_note_id: str | None = None
        self._dirty = False
        self._pin_hash: str | None = None
        self._pin_salt: bytes | None = None
        self._creating_note = False
        self._drag_pos = None
        self._resize_dir: str | None = None
        self._resize_start_geo = None

        self._theme_name = self._load_saved_theme()
        if self._theme_name not in THEMES:
            self._theme_name = "Klasyczny"

        self._font_size = self._load_config().get("font_size", SIZES["BASE_FONT_SIZE"])
        self._font_size = max(SIZES["FONT_SIZE_MIN"], min(SIZES["FONT_SIZE_MAX"], self._font_size))

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._setup_ui()
        self._apply_font_size()
        self._setup_shortcuts()
        self._setup_auto_save()

        self._load_notes()
        self._rebuild_sidebar()
        self._update_counters()

        if self._theme_name != "Klasyczny":
            self._apply_theme(self._theme_name)

        if self._pin_hash is not None:
            QTimer.singleShot(100, self._show_lock_screen)

        self._acquire_lock()

    def _acquire_lock(self):
        """Blokuje plik danych, by zapobiec konfliktom między instancjami."""
        lock_path = self._data_path().with_suffix(".lock")
        try:
            if os.name == 'nt':
                import msvcrt
                self._lock_file = open(lock_path, "w")
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                self._lock_file = open(lock_path, "w")
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._lock_file.write(str(os.getpid()))
                self._lock_file.flush()
        except Exception as e:
            log.warning("Nie udalo sie uzyskac locka pliku: %s", e)
            if hasattr(self, '_lock_file') and self._lock_file:
                try:
                    self._lock_file.close()
                except Exception:
                    pass
            self._lock_file = None

    def _release_lock(self):
        """Zwalnia blokadę pliku."""
        if not hasattr(self, '_lock_file') or not self._lock_file:
            return
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
            lock_path = self._data_path().with_suffix(".lock")
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass
        finally:
            self._lock_file = None

    # ─── budowa UI ───

    def _setup_ui(self):
        self.setWindowTitle("Anti-Spaghetti")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(SIZES["WINDOW_WIDTH"], SIZES["WINDOW_HEIGHT"])
        self.setMinimumSize(SIZES["WINDOW_MIN_W"], SIZES["WINDOW_MIN_H"])
        self.setStyleSheet(f"background-color: {BG_APP};")
        self._set_window_icon()

        self._title_font = self._load_title_font()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet(f"background-color: {BG_APP};")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(14, 0, 6, 0)
        title_layout.setSpacing(0)

        self.title_label = QLabel("Anti-Spaghetti")
        if self._title_font:
            title_font = QFont(self._title_font)
            title_font.setPointSize(20)
            self.title_label.setFont(title_font)
        else:
            self.title_label.setFont(self._make_font(20, bold=True))
        self.title_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self._btn_min = QPushButton("—")
        self._btn_min.setFixedSize(46, 32)
        self._btn_min.setFont(self._make_font(14))
        self._btn_min.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_DIM};
                border: none; font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {BG_BTN_HOVER}; color: {TEXT_MAIN};
            }}
        """)
        self._btn_min.clicked.connect(self.showMinimized)

        self._btn_max = QPushButton("□")
        self._btn_max.setFixedSize(46, 32)
        self._btn_max.setFont(self._make_font(14))
        self._btn_max.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_DIM};
                border: none; font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {BG_BTN_HOVER}; color: {TEXT_MAIN};
            }}
        """)
        self._btn_max.clicked.connect(self._toggle_maximize)

        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(46, 32)
        self._btn_close.setFont(self._make_font(16))
        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_DIM};
                border: none; font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: #e81123; color: white;
            }}
        """)
        self._btn_close.clicked.connect(self.close)

        title_layout.addWidget(self._btn_min)
        title_layout.addWidget(self._btn_max)
        title_layout.addWidget(self._btn_close)

        main_layout.addWidget(self.title_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(0)
        self.splitter.setChildrenCollapsible(False)

        self._setup_left_panel()
        self._setup_right_panel()

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([
            SIZES["WINDOW_WIDTH"] - SIZES["SIDEBAR_DEF_W"],
            SIZES["SIDEBAR_DEF_W"],
        ])
        self.right_panel.setMinimumWidth(SIZES["SIDEBAR_MIN_W"])
        self.right_panel.setMaximumWidth(SIZES["SIDEBAR_MAX_W"])

        self._setup_bottom_bar()

        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.bottom_bar)

    def _setup_left_panel(self):
        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.header = QLabel("Notatnik")
        font = self._make_font(SIZES["HEADER_FONT_SIZE"], bold=True)
        self.header.setFont(font)
        self.header.setStyleSheet(
            f"color: {TEXT_DIM}; "
            f"padding: {SIZES['HEADER_PAD_TOP']}px 0px "
            f"{SIZES['HEADER_PAD_BOT']}px {SIZES['HEADER_PAD_LEFT']}px;"
        )
        left_layout.addWidget(self.header)

        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet(QSS_EDITOR)
        self.editor.setFont(self._make_font(SIZES["BASE_FONT_SIZE"]))
        self.editor.setPlaceholderText("Zacznij pisać lub wklej tekst...")
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editor.verticalScrollBar().setStyleSheet(QSS_SCROLLBAR)
        self.editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._editor_context_menu)
        self.editor.textChanged.connect(self._on_text_changed)
        left_layout.addWidget(self.editor)

    def _setup_right_panel(self):
        self.right_panel = QWidget()
        self.right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        sidebar_top = QWidget()
        sidebar_top.setStyleSheet("background: transparent;")
        sidebar_top_layout = QHBoxLayout(sidebar_top)
        sidebar_top_layout.setContentsMargins(
            SIZES["SIDEBAR_TOP_PAD"], SIZES["SIDEBAR_TOP_PAD"],
            SIZES["SIDEBAR_TOP_PAD"], SIZES["SIDEBAR_TOP_PAD"],
        )
        sidebar_top_layout.setSpacing(0)

        self.count_label = QLabel("0 elementów")
        self.count_label.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        self.count_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(_icon("fa5s.cog", color=TEXT_DIM))
        self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setStyleSheet(QSS_SETTINGS_BTN)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self._on_settings_clicked)

        sidebar_top_layout.addWidget(self.count_label)
        sidebar_top_layout.addStretch()
        sidebar_top_layout.addWidget(self.settings_btn)

        right_layout.addWidget(sidebar_top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setViewportMargins(0, 0, SIZES["VIEWPORT_MARGIN_R"], 0)
        self.scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self.scroll.verticalScrollBar().setStyleSheet(QSS_SCROLLBAR)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(
            SIZES["SIDEBAR_MARGIN"],
            SIZES["SIDEBAR_LIST_TOP"],
            SIZES["SIDEBAR_MARGIN"],
            SIZES["SIDEBAR_LIST_BOT"],
        )
        self.scroll_layout.setSpacing(SIZES["SIDEBAR_SPACING"])
        self.scroll_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        right_layout.addWidget(self.scroll)

    def _setup_bottom_bar(self):
        self.bottom_bar = QWidget()
        self.bottom_bar.setObjectName("BottomBar")
        self.bottom_bar.setFixedHeight(SIZES["BOTTOM_BAR_H"])
        self.bottom_bar.setStyleSheet(QSS_BOTTOMBAR)
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(
            SIZES["BOTTOM_BAR_PAD"], 0, SIZES["BOTTOM_BAR_PAD"], 0,
        )
        bottom_layout.setSpacing(4)

        self.add_btn = QPushButton()
        self.add_btn.setIcon(_icon("fa5s.plus", color=TEXT_DIM))
        self.add_btn.setIconSize(QSize(20, 20))
        self.add_btn.setStyleSheet(QSS_BOTTOM_BTN)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_note)

        self.save_btn = QPushButton()
        self.save_btn.setIcon(_icon("fa5s.save", color=TEXT_DIM))
        self.save_btn.setIconSize(QSize(20, 20))
        self.save_btn.setStyleSheet(QSS_BOTTOM_BTN)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_current)

        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(_icon("fa5s.copy", color=TEXT_DIM))
        self.copy_btn.setIconSize(QSize(20, 20))
        self.copy_btn.setStyleSheet(QSS_BOTTOM_BTN)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)

        self.export_btn = QPushButton()
        self.export_btn.setIcon(_icon("fa5s.file-export", color=TEXT_DIM))
        self.export_btn.setIconSize(QSize(20, 20))
        self.export_btn.setStyleSheet(QSS_BOTTOM_BTN)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setToolTip("Eksportuj notatki (Ctrl+E)")
        self.export_btn.clicked.connect(self._show_export_dialog)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj...")
        self.search_edit.setStyleSheet(QSS_SEARCH)
        self.search_edit.setFont(self._make_font(SIZES["BASE_FONT_SIZE"]))
        self.search_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_edit.customContextMenuRequested.connect(self._search_context_menu)
        self.search_edit.textChanged.connect(self._on_search_text_changed)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)

        self._btn_size_down = QPushButton()
        self._btn_size_down.setIcon(_icon("fa5s.minus", color=TEXT_DIM))
        self._btn_size_down.setIconSize(QSize(14, 14))
        self._btn_size_down.setStyleSheet(QSS_BOTTOM_BTN)
        self._btn_size_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_size_down.clicked.connect(self._font_size_down)

        self.size_label = QLabel(f"{self._font_size}pt")
        self.size_label.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        self.size_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        self.size_label.setFixedWidth(32)
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_size_up = QPushButton()
        self._btn_size_up.setIcon(_icon("fa5s.plus", color=TEXT_DIM))
        self._btn_size_up.setIconSize(QSize(14, 14))
        self._btn_size_up.setStyleSheet(QSS_BOTTOM_BTN)
        self._btn_size_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_size_up.clicked.connect(self._font_size_up)

        self.tokens_label = QLabel("~0 tokenów")
        self.tokens_label.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        self.tokens_label.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")

        bottom_layout.addWidget(self.add_btn)
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.copy_btn)
        bottom_layout.addWidget(self.export_btn)
        bottom_layout.addWidget(self._btn_size_down)
        bottom_layout.addWidget(self.size_label)
        bottom_layout.addWidget(self._btn_size_up)
        bottom_layout.addWidget(self.search_edit, 1)
        bottom_layout.addWidget(self.tokens_label)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence.StandardKey.Save, self).activated.connect(self._save_current)
        QShortcut(QKeySequence("Ctrl+n"), self).activated.connect(self._add_note)
        QShortcut(QKeySequence("Ctrl+f"), self).activated.connect(self._focus_search)
        QShortcut(QKeySequence("Ctrl+d"), self).activated.connect(self._delete_current_note)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._font_size_up)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._font_size_down)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self._next_note)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self._prev_note)
        QShortcut(QKeySequence("Ctrl+e"), self).activated.connect(self._show_export_dialog)

    def _next_note(self):
        if not self._notes:
            return
        if self._active_note_id is None:
            self._select_note(self._notes[0]["id"])
            return
        current_index = next(
            (i for i, n in enumerate(self._notes) if n["id"] == self._active_note_id), -1
        )
        next_index = (current_index + 1) % len(self._notes)
        self._select_note(self._notes[next_index]["id"])

    def _prev_note(self):
        if not self._notes:
            return
        if self._active_note_id is None:
            self._select_note(self._notes[-1]["id"])
            return
        current_index = next(
            (i for i, n in enumerate(self._notes) if n["id"] == self._active_note_id), 0
        )
        prev_index = (current_index - 1) % len(self._notes)
        self._select_note(self._notes[prev_index]["id"])

    def _setup_auto_save(self):
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(5000)

    def _auto_save(self):
        if self._dirty:
            self.save_notes()
            self._dirty = False

    def _focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _delete_current_note(self):
        if self._active_note_id is not None:
            self._confirm_delete(self._active_note_id)

    def _font_size_up(self):
        if self._font_size < SIZES["FONT_SIZE_MAX"]:
            self._font_size += 1
            self._apply_font_size()
            self._save_config()

    def _font_size_down(self):
        if self._font_size > SIZES["FONT_SIZE_MIN"]:
            self._font_size -= 1
            self._apply_font_size()
            self._save_config()

    def _apply_font_size(self):
        self.editor.setFont(self._make_font(self._font_size))
        self.size_label.setText(f"{self._font_size}pt")

    # ─── funkcje pomocnicze ───

    def _make_font(self, size: int, bold: bool = False) -> QFont:
        font = QFont("Intel One Mono", size)
        if not font.exactMatch():
            font = QFont("Consolas", size)
        if bold:
            font.setBold(True)
        return font

    def _data_path(self) -> Path:
        return Path(__file__).parent / "notes.json"

    def _config_path(self) -> Path:
        return Path(__file__).parent / ".config"

    @staticmethod
    def _load_app_icon():
        """Laduje ikone aplikacji z pliku .ico."""
        from PyQt6.QtGui import QIcon
        icon_path = Path(__file__).parent / "icons" / "icon.ico"
        if icon_path.exists():
            return QIcon(str(icon_path))
        return QIcon()

    def _set_window_icon(self):
        self.setWindowIcon(self._load_app_icon())

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Usuwa niedozwolone znaki z nazwy pliku."""
        return re.sub(r'[<>:"/\\|?*]', '_', name)[:80]

    def _load_title_font(self):
        font_dir = Path(__file__).parent / "fonts"
        if font_dir.exists():
            for f in font_dir.glob("*.ttf"):
                fid = QFontDatabase.addApplicationFont(str(f))
                if fid >= 0:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    if families:
                        font = QFont(families[0], 12)
                        font.setBold(True)
                        return font
        return None

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _edge_at(self, pos) -> str | None:
        m = SIZES["RESIZE_MARGIN"]
        w, h = self.width(), self.height()
        edge = ""
        if pos.y() < m:
            edge += "top"
        elif pos.y() > h - m:
            edge += "bottom"
        if pos.x() < m:
            edge += "left"
        elif pos.x() > w - m:
            edge += "right"
        return edge if edge else None

    def _edge_cursor(self, edge: str) -> Qt.CursorShape:
        cursors = {
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "topleft": Qt.CursorShape.SizeFDiagCursor,
            "bottomright": Qt.CursorShape.SizeFDiagCursor,
            "topright": Qt.CursorShape.SizeBDiagCursor,
            "bottomleft": Qt.CursorShape.SizeBDiagCursor,
        }
        return cursors.get(edge, Qt.CursorShape.ArrowCursor)

    def event(self, event):
        """Przechwytuje HoverMove (WA_Hover) do zmiany kursora na krawedziach."""
        if event.type() == QEvent.Type.HoverMove:
            if not self.isMaximized():
                edge = self._edge_at(event.position().toPoint())
                if edge:
                    self.setCursor(self._edge_cursor(edge))
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
        return super().event(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._edge_at(event.pos())
            if edge and not self.isMaximized():
                self._resize_dir = edge
                self._resize_start_geo = self.geometry()
                self._drag_pos = event.globalPosition().toPoint()
                event.accept()
                return
            if self.title_bar.underMouse():
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_dir and self._resize_start_geo:
            delta = event.globalPosition().toPoint() - self._drag_pos
            geo = QRect(self._resize_start_geo)
            d = self._resize_dir
            if "left" in d:
                geo.setLeft(geo.left() + delta.x())
            if "right" in d:
                geo.setRight(geo.right() + delta.x())
            if "top" in d:
                geo.setTop(geo.top() + delta.y())
            if "bottom" in d:
                geo.setBottom(geo.bottom() + delta.y())
            if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                self.setGeometry(geo)
            event.accept()
            return
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if not self.isMaximized():
                self.move(event.globalPosition().toPoint() - self._drag_pos)
        elif not event.buttons():
            if not self.isMaximized():
                edge = self._edge_at(event.pos())
                if edge:
                    self.setCursor(self._edge_cursor(edge))
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_dir:
            self._resize_dir = None
            self._resize_start_geo = None
            event.accept()
            return
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.title_bar.underMouse():
            self._toggle_maximize()
        elif self.header.underMouse() and self._active_note_id is not None:
            self._deselect_note()
        super().mouseDoubleClickEvent(event)

    def _deselect_note(self):
        """Deselektuje aktywną notatkę - wraca do pustego edytora."""
        self._sync_editor_to_note()
        self._active_note_id = None
        self.header.setText("Notatnik")
        self.setWindowTitle("Anti-Spaghetti")
        self.editor.clear()
        for btn in self._buttons:
            btn.setChecked(False)
        self._update_counters()

    # ─── zarzadzanie danymi ───

    def _load_notes(self):
        path = self._data_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        self._notes = []
                        return
                    data = json.loads(content)
                    if not isinstance(data, list):
                        self._show_data_error("notes.json nie jest listą. Utworzono kopię zapasową.")
                        self._backup_corrupted_file(path)
                        self._notes = []
                        return
                    self._notes = [
                        n for n in data
                        if isinstance(n, dict) and isinstance(n.get("id"), str) and isinstance(n.get("name"), str)
                    ]
                    # Dodaj brakujące klucze i waliduj typy
                    for note in self._notes:
                        note["content"] = note.get("content") if isinstance(note.get("content"), str) else ""
                        if "created_at" not in note:
                            note["created_at"] = datetime.now().isoformat()
                        if "updated_at" not in note:
                            note["updated_at"] = note["created_at"]
                    self._migrate_notes()
            except json.JSONDecodeError as e:
                self._show_data_error(f"Błąd parsowania notes.json: {e}\nUtworzono kopię zapasową.")
                self._backup_corrupted_file(path)
                self._notes = []
            except Exception as e:
                self._show_data_error(f"Błąd odczytu notes.json: {e}\nUtworzono kopię zapasową.")
                self._backup_corrupted_file(path)
                self._notes = []
        else:
            self._notes = []

    def _backup_corrupted_file(self, path: Path):
        """Tworzy kopię zapasową uszkodzonego pliku."""
        try:
            backup_path = path.with_suffix(f".json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(path, backup_path)
        except Exception:
            pass

    def _show_data_error(self, message: str):
        """Wyświetla dialog błędu danych."""
        try:
            C = self._theme_colors if hasattr(self, '_theme_colors') else THEMES["Klasyczny"]
            msg_box = DraggableDialog(self)
            msg_box.setFixedSize(400, 180)
            msg_box.setStyleSheet(f"""
                QDialog {{
                    background-color: {C["BG_EDITOR"]};
                    border: 1px solid #e74c3c;
                    border-radius: 12px;
                }}
            """)
            layout = QVBoxLayout(msg_box)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(16)
            
            lbl = QLabel("Błąd danych")
            lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
            lbl.setStyleSheet("color: #e74c3c; background: transparent;")
            layout.addWidget(lbl)
            
            msg_lbl = QLabel(message)
            msg_lbl.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
            msg_lbl.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
            msg_lbl.setWordWrap(True)
            layout.addWidget(msg_lbl)
            
            btn = QPushButton("OK")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C["ACCENT"]};
                    color: {C["TEXT_MAIN"]};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 0px;
                    font-size: {SIZES["BASE_FONT_SIZE"]}px;
                }}
                QPushButton:hover {{
                    background-color: {C["BG_BTN_HOVER"]};
                }}
            """)
            btn.clicked.connect(msg_box.accept)
            layout.addWidget(btn)
            msg_box.exec()
            msg_box.deleteLater()
        except Exception:
            log.error("Błąd wyświetlania dialogu: %s", message)

    def _migrate_notes(self):
        now = datetime.now().isoformat()
        changed = False
        for note in self._notes:
            if "created_at" not in note:
                note["created_at"] = now
                changed = True
            if "updated_at" not in note:
                note["updated_at"] = now
                changed = True
        if changed:
            self.save_notes()

    def save_notes(self):
        self._sync_editor_to_note()
        path = self._data_path()
        tmp_path = path.with_suffix(".json.tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._notes, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception as e:
            self._show_save_error(str(e))
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def _show_save_error(self, message: str):
        """Wyświetla błąd zapisu."""
        try:
            C = self._theme_colors if hasattr(self, '_theme_colors') else THEMES["Klasyczny"]
            msg_box = DraggableDialog(self)
            msg_box.setFixedSize(360, 160)
            msg_box.setStyleSheet(f"""
                QDialog {{
                    background-color: {C["BG_EDITOR"]};
                    border: 1px solid #e74c3c;
                    border-radius: 12px;
                }}
            """)
            layout = QVBoxLayout(msg_box)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(12)

            lbl = QLabel("Błąd zapisu")
            lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
            lbl.setStyleSheet("color: #e74c3c; background: transparent;")
            layout.addWidget(lbl)

            msg_lbl = QLabel(f"Nie udało się zapisać danych:\n{message}")
            msg_lbl.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
            msg_lbl.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
            msg_lbl.setWordWrap(True)
            layout.addWidget(msg_lbl)

            btn = QPushButton("OK")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C["ACCENT"]};
                    color: {C["TEXT_MAIN"]};
                    border: none;
                    border-radius: 8px;
                    padding: 8px 0px;
                    font-size: {SIZES["BASE_FONT_SIZE"]}px;
                }}
                QPushButton:hover {{
                    background-color: {C["BG_BTN_HOVER"]};
                }}
            """)
            btn.clicked.connect(msg_box.accept)
            layout.addWidget(btn)

            center = self.geometry().center()
            msg_box.move(center.x() - msg_box.width() // 2, center.y() - msg_box.height() // 2)
            msg_box.exec()
            msg_box.deleteLater()
        except Exception:
            pass

    def _sync_editor_to_note(self):
        if self._active_note_id is not None:
            for note in self._notes:
                if note["id"] == self._active_note_id:
                    new_content = self.editor.toPlainText()
                    if note.get("content") != new_content:
                        note["content"] = new_content
                        note["updated_at"] = datetime.now().isoformat()
                    break

    def _rebuild_sidebar(self):
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self._buttons.clear()

        for note in self._notes:
            btn = SidebarButton(note["id"], note["name"], self.scroll_content)
            btn.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
            btn.clicked.connect(self._on_button_clicked)
            target_idx = max(0, self.scroll_layout.count() - 1)
            self.scroll_layout.insertWidget(target_idx, btn)
            self._buttons.append(btn)

        # dostosuj nowe przyciski do aktualnego motywu i czcionki
        C = dict(self._theme_colors)
        C.update(SIZES)
        for btn in self._buttons:
            btn.setStyleSheet(_build_qss(QSS_SIDEBAR_BTN_TPL, C))
            btn.setChecked(btn._note_id == self._active_note_id)

    # ─── motywy ───

    def _apply_theme(self, name: str):
        self._theme_name = name
        C = dict(THEMES[name])
        C.update(SIZES)

        self._set_window_icon()
        self.setStyleSheet(f"background-color: {C['BG_APP']};")

        self.title_bar.setStyleSheet(f"background-color: {C['BG_APP']};")
        self.title_label.setStyleSheet(f"color: {C['TEXT_DIM']}; background: transparent;")
        if self._title_font:
            title_font = QFont(self._title_font)
            title_font.setPointSize(20)
            self.title_label.setFont(title_font)
        else:
            self.title_label.setFont(self._make_font(20, bold=True))
        self._btn_min.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C['TEXT_DIM']};
                border: none; font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {C['BG_BTN_HOVER']}; color: {C['TEXT_MAIN']};
            }}
        """)
        self._btn_max.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C['TEXT_DIM']};
                border: none; font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {C['BG_BTN_HOVER']}; color: {C['TEXT_MAIN']};
            }}
        """)
        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C['TEXT_DIM']};
                border: none; font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: #e81123; color: white;
            }}
        """)

        self.header.setStyleSheet(
            f"color: {C['TEXT_DIM']}; "
            f"padding: {C['HEADER_PAD_TOP']}px 0px "
            f"{C['HEADER_PAD_BOT']}px {C['HEADER_PAD_LEFT']}px;"
        )

        self.editor.setStyleSheet(_build_qss(QSS_EDITOR_TPL, C))

        self.editor.verticalScrollBar().setStyleSheet(
            _build_qss(QSS_SCROLLBAR_TPL, C)
        )

        self.scroll.verticalScrollBar().setStyleSheet(
            _build_qss(QSS_SCROLLBAR_TPL, C)
        )

        for btn in self._buttons:
            btn.setStyleSheet(_build_qss(QSS_SIDEBAR_BTN_TPL, C))

        self.count_label.setStyleSheet(f"color: {C['TEXT_DIM']}; background: transparent;")
        self.tokens_label.setStyleSheet(f"color: {C['TEXT_DIM']}; background: transparent;")

        self.bottom_bar.setStyleSheet(_build_qss(QSS_BOTTOMBAR_TPL, C))

        self.search_edit.setStyleSheet(_build_qss(QSS_SEARCH_TPL, C))

        d = C["TEXT_DIM"]
        self.add_btn.setIcon(_icon("fa5s.plus", color=d))
        self.add_btn.setStyleSheet(_build_qss(QSS_BOTTOM_BTN_TPL, C))
        self.save_btn.setIcon(_icon("fa5s.save", color=d))
        self.save_btn.setStyleSheet(_build_qss(QSS_BOTTOM_BTN_TPL, C))
        self.copy_btn.setIcon(_icon("fa5s.copy", color=d))
        self.copy_btn.setStyleSheet(_build_qss(QSS_BOTTOM_BTN_TPL, C))
        self.export_btn.setIcon(_icon("fa5s.file-export", color=d))
        self.export_btn.setStyleSheet(_build_qss(QSS_BOTTOM_BTN_TPL, C))
        self._btn_size_down.setIcon(_icon("fa5s.minus", color=d))
        self._btn_size_down.setStyleSheet(_build_qss(QSS_BOTTOM_BTN_TPL, C))
        self._btn_size_up.setIcon(_icon("fa5s.plus", color=d))
        self._btn_size_up.setStyleSheet(_build_qss(QSS_BOTTOM_BTN_TPL, C))
        self.size_label.setStyleSheet(f"color: {d}; background: transparent;")
        self.settings_btn.setIcon(_icon("fa5s.cog", color=d))
        self.settings_btn.setStyleSheet(_build_qss(QSS_SETTINGS_BTN_TPL, C))

        # odśwież globalny styl QMenu
        app = QApplication.instance()
        if app:
            app.setStyleSheet(f"""
                QMenu {{
                    background-color: {C["BG_BTN"]};
                    color: {C["TEXT_MAIN"]};
                    border: 1px solid {C["SEPARATOR"]};
                    border-radius: 6px;
                    padding: 4px;
                    font-size: {C["BASE_FONT_SIZE"]}px;
                }}
                QMenu::item {{
                    padding: 6px 24px 6px 16px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {C["BG_BTN_HOVER"]};
                }}
                QMenu::item:checked {{
                    font-weight: bold;
                }}
                QMenu::indicator {{
                    width: 12px;
                    height: 12px;
                    margin-left: 4px;
                }}
                QMenu::separator {{
                    height: 1px;
                    background: {C["SEPARATOR"]};
                    margin: 4px 8px;
                }}
            """)

        self._save_config()

    def _save_config(self):
        try:
            data = {
                "theme": self._theme_name,
                "font_size": self._font_size,
            }
            if self._pin_hash and self._pin_salt:
                data["pin_hash"] = self._pin_hash
                data["pin_salt"] = self._pin_salt.hex()
            with open(self._config_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._show_data_error(f"Błąd zapisu konfiguracji: {e}")

    def _load_config(self) -> dict:
        try:
            if self._config_path().exists():
                with open(self._config_path(), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._pin_hash = data.get("pin_hash", None)
                    salt_hex = data.get("pin_salt", None)
                    self._pin_salt = bytes.fromhex(salt_hex) if salt_hex else None
                    return data
        except Exception as e:
            self._show_data_error(f"Błąd odczytu konfiguracji: {e}")
        return {}

    def _load_saved_theme(self) -> str:
        return self._load_config().get("theme", "Klasyczny")

    @property
    def _theme_colors(self) -> dict:
        return THEMES.get(self._theme_name, THEMES["Klasyczny"])

    # ─── PIN ───

    @staticmethod
    def _hash_pin(pin: str, salt: bytes = None) -> tuple[str, bytes]:
        """Hasz PIN używając PBKDF2 z losowym solą."""
        if salt is None:
            salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', pin.encode("utf-8"), salt, 100000)
        return key.hex(), salt

    @staticmethod
    def _verify_pin(pin: str, stored_hash: str, salt: bytes) -> bool:
        """Weryfikuje PIN przeciwko zapisanemu hashowi."""
        key = hashlib.pbkdf2_hmac('sha256', pin.encode("utf-8"), salt, 100000)
        return key.hex() == stored_hash

    def _pin_dialog(self, title: str, placeholder: str = "PIN") -> str | None:
        C = self._theme_colors

        dialog = DraggableDialog(self)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setFixedSize(340, 200)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        lbl = QLabel(title)
        lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
        lbl.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        layout.addWidget(lbl)

        pin_edit = QLineEdit()
        pin_edit.setPlaceholderText(placeholder)
        pin_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pin_edit.setMaxLength(4)
        pin_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{0,4}")))
        pin_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C["BG_BTN"]};
                color: {C["TEXT_MAIN"]};
                border: 2px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 10px;
                font-size: 22px;
                letter-spacing: 14px;
                selection-background-color: {C["ACCENT"]};
            }}
            QLineEdit::placeholder {{
                color: {C["TEXT_DIM"]};
                letter-spacing: 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
        """)
        pin_edit.setFont(self._make_font(22))
        pin_edit.setFocus()
        layout.addWidget(pin_edit)

        err_label = QLabel("")
        err_label.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        err_label.setStyleSheet("color: #e74c3c; background: transparent;")
        err_label.setFixedHeight(18)
        layout.addWidget(err_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {C["TEXT_DIM"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
                color: {C["TEXT_MAIN"]};
            }}
        """)

        result_holder = [None]

        def on_accept():
            val = pin_edit.text().strip()
            if len(val) != 4 or not val.isdigit():
                err_label.setText("PIN musi składać się z 4 cyfr")
                pin_edit.setFocus()
                pin_edit.selectAll()
                return
            result_holder[0] = val
            dialog.accept()

        pin_edit.returnPressed.connect(on_accept)
        btn_ok.clicked.connect(on_accept)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        dialog.exec()
        dialog.deleteLater()
        return result_holder[0]

    def _set_pin(self):
        if self._pin_hash is not None:
            current = self._pin_dialog("Podaj aktualny PIN")
            if current is None:
                return
            if not self._verify_pin(current, self._pin_hash, self._pin_salt):
                self._show_pin_error("Nieprawidłowy PIN")
                return
        new_pin = self._pin_dialog("Ustaw nowy PIN (4 cyfry)")
        if new_pin is None:
            return
        confirm = self._pin_dialog("Potwierdź nowy PIN")
        if confirm is None:
            return
        if new_pin != confirm:
            self._show_pin_error("PIN-y się różnią")
            return
        self._pin_hash, self._pin_salt = self._hash_pin(new_pin)
        self._save_config()

    def _remove_pin(self):
        if self._pin_hash is None:
            return
        current = self._pin_dialog("Podaj aktualny PIN, aby usunąć")
        if current is None:
            return
        if not self._verify_pin(current, self._pin_hash, self._pin_salt):
            self._show_pin_error("Nieprawidłowy PIN")
            return
        self._pin_hash = None
        self._pin_salt = None
        self._save_config()

    def _show_pin_error(self, msg: str):
        C = self._theme_colors
        err = DraggableDialog(self)
        err.setWindowModality(Qt.WindowModality.ApplicationModal)
        err.setFixedSize(320, 140)
        err.setStyleSheet(f"""
            QDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid #e74c3c;
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(err)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        lbl = QLabel(msg)
        lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
        lbl.setStyleSheet(f"color: #e74c3c; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        btn = QPushButton("OK")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        btn.clicked.connect(err.accept)
        layout.addWidget(btn)
        err.exec()
        err.deleteLater()

    def _show_lock_screen(self):
        if self._pin_hash is None:
            return
        C = self._theme_colors

        lock = DraggableDialog(self)
        lock.setWindowModality(Qt.WindowModality.ApplicationModal)
        lock.setFixedSize(360, 320)
        lock.setStyleSheet(f"""
            QDialog {{
                background-color: {C["BG_APP"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(lock)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        lock_icon = QLabel("Zablokowano")
        lock_icon.setFont(self._make_font(SIZES["HEADER_FONT_SIZE"], bold=True))
        lock_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lock_icon.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        layout.addWidget(lock_icon)

        subtitle = QLabel("Wprowadź PIN, aby odblokować")
        subtitle.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {C['TEXT_DIM']}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        pin_edit = QLineEdit()
        pin_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pin_edit.setMaxLength(4)
        pin_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{0,4}")))
        pin_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C["BG_BTN"]};
                color: {C["TEXT_MAIN"]};
                border: 2px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 14px;
                font-size: 28px;
                letter-spacing: 18px;
                selection-background-color: {C["ACCENT"]};
            }}
            QLineEdit::placeholder {{
                color: {C["TEXT_DIM"]};
                letter-spacing: 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QLineEdit:focus {{
                border: 2px solid {C["ACCENT"]};
            }}
        """)
        pin_edit.setFont(self._make_font(28))
        pin_edit.setPlaceholderText("----")
        pin_edit.setFocus()
        layout.addWidget(pin_edit)

        err_label = QLabel("")
        err_label.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        err_label.setStyleSheet("color: #e74c3c; background: transparent;")
        err_label.setFixedHeight(20)
        layout.addWidget(err_label)

        layout.addSpacing(4)

        unlock_btn = QPushButton("Odblokuj")
        unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 12px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        layout.addWidget(unlock_btn)

        def try_unlock():
            val = pin_edit.text().strip()
            if len(val) != 4 or not val.isdigit():
                err_label.setText("PIN musi składać się z 4 cyfr")
                pin_edit.setFocus()
                pin_edit.selectAll()
                return
            if self._verify_pin(val, self._pin_hash, self._pin_salt):
                lock.accept()
            else:
                err_label.setText("Nieprawidłowy PIN")
                pin_edit.clear()
                pin_edit.setFocus()

        unlock_btn.clicked.connect(try_unlock)
        pin_edit.returnPressed.connect(try_unlock)

        self.setEnabled(False)
        lock.exec()
        self.setEnabled(True)
        lock.deleteLater()

    # ─── operacje na wpisach ───

    def _add_note(self):
        C = self._theme_colors

        dialog = DraggableDialog(self)
        dialog.setObjectName("AddDialog")
        dialog.setFixedSize(300, 140)
        dialog.setStyleSheet(f"""
            QDialog#AddDialog {{
                background-color: {C["BG_BTN"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        edit = QLineEdit()
        edit.setPlaceholderText("Nazwa wpisu")
        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C["BG_EDITOR"]};
                color: {C["TEXT_MAIN"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                selection-background-color: {C["ACCENT"]};
            }}
            QLineEdit::placeholder {{
                color: {C["TEXT_DIM"]};
            }}
        """)
        edit.setFocus()
        layout.addWidget(edit)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_ok = QPushButton("Dodaj")
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)

        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {C["TEXT_DIM"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
                color: {C["TEXT_MAIN"]};
            }}
        """)

        edit.returnPressed.connect(dialog.accept)
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        # pozycja nad przyciskiem +
        parent_pos = self.bottom_bar.mapToGlobal(self.add_btn.pos())
        dialog.move(
            parent_pos.x() + self.add_btn.width() // 2 - dialog.width() // 2,
            parent_pos.y() - dialog.height() - 8,
        )

        result = dialog.exec()

        name = edit.text().strip()
        dialog.deleteLater()

        if result == QDialog.DialogCode.Accepted and name:
            note_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            note = {"id": note_id, "name": name.strip(), "content": "",
                    "created_at": now, "updated_at": now}
            self._notes.insert(0, note)
            self._rebuild_sidebar()
            self._select_note(note_id)
            self.editor.clear()
            self._update_counters()
            self.save_notes()
            self.search_edit.clear()
            self._do_search()

    def _confirm_delete(self, note_id: str):
        note = next((n for n in self._notes if n["id"] == note_id), None)
        if not note:
            return
        C = self._theme_colors

        dialog = DraggableDialog(self)
        dialog.setObjectName("DeleteDialog")
        dialog.setFixedSize(340, 160)
        dialog.setStyleSheet(f"""
            QDialog#DeleteDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid #e74c3c;
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        lbl = QLabel(f"Czy na pewno usunąć \"{note['name']}\"?")
        lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"]))
        lbl.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_yes = QPushButton("Usuń")
        btn_yes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_yes.setStyleSheet(f"""
            QPushButton {{
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """)

        btn_no = QPushButton("Anuluj")
        btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_no.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {C["TEXT_DIM"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
                color: {C["TEXT_MAIN"]};
            }}
        """)

        btn_yes.clicked.connect(dialog.accept)
        btn_no.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)
        layout.addLayout(btn_layout)

        center = self.geometry().center()
        dialog.move(
            center.x() - dialog.width() // 2,
            center.y() - dialog.height() // 2,
        )

        result = dialog.exec()
        dialog.deleteLater()

        if result == QDialog.DialogCode.Accepted:
            self._delete_note(note_id)

    def _delete_note(self, note_id: str):
        was_active = (self._active_note_id == note_id)
        self._notes = [n for n in self._notes if n["id"] != note_id]
        self._rebuild_sidebar()
        if was_active:
            self.header.setText("Notatnik")
            self.setWindowTitle("Anti-Spaghetti")
            self.editor.clear()
            self._active_note_id = None
        self._update_counters()
        self.save_notes()

    def _rename_note(self, note_id: str):
        note = next((n for n in self._notes if n["id"] == note_id), None)
        if note is None:
            return
        C = self._theme_colors
        dialog = DraggableDialog(self)
        dialog.setObjectName("RenameDialog")
        dialog.setFixedSize(300, 140)
        dialog.setStyleSheet(f"""
            QDialog#RenameDialog {{
                background-color: {C["BG_BTN"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        edit = QLineEdit(note["name"])
        edit.selectAll()
        edit.setPlaceholderText("Nowa nazwa")
        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C["BG_EDITOR"]};
                color: {C["TEXT_MAIN"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                selection-background-color: {C["ACCENT"]};
            }}
            QLineEdit::placeholder {{
                color: {C["TEXT_DIM"]};
            }}
        """)
        edit.setFocus()
        layout.addWidget(edit)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_ok = QPushButton("Zapisz")
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {C["TEXT_DIM"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
                color: {C["TEXT_MAIN"]};
            }}
        """)
        edit.returnPressed.connect(dialog.accept)
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        center = self.geometry().center()
        dialog.move(
            center.x() - dialog.width() // 2,
            center.y() - dialog.height() // 2,
        )
        result = dialog.exec()
        new_name = edit.text().strip()
        dialog.deleteLater()
        if result == QDialog.DialogCode.Accepted and new_name:
            note["name"] = new_name
            note["updated_at"] = datetime.now().isoformat()
            was_active = (self._active_note_id == note_id)
            self._rebuild_sidebar()
            if was_active:
                self._select_note(note_id)
            self.save_notes()

    def _select_note(self, note_id: str):
        self._sync_editor_to_note()
        self._active_note_id = note_id
        for note in self._notes:
            if note["id"] == note_id:
                self.header.setText(note["name"])
                self.setWindowTitle(f"{note['name']} — Anti-Spaghetti")
                self.editor.setPlainText(note.get("content", ""))
                break
        for btn in self._buttons:
            btn.setChecked(btn._note_id == note_id)
        self._update_counters()

    def _on_button_clicked(self):
        btn = self.sender()
        if btn is None or not isinstance(btn, SidebarButton):
            return
        self._select_note(btn._note_id)

    def _save_current(self):
        self._sync_editor_to_note()
        if self._active_note_id is not None:
            for note in self._notes:
                if note["id"] == self._active_note_id:
                    note["updated_at"] = datetime.now().isoformat()
                    break
        self.save_notes()
        self._dirty = False
        self._show_save_feedback()

    def _show_save_feedback(self):
        """Pokazuje krótkie potwierdzenie zapisu."""
        d = self._theme_colors["TEXT_DIM"]
        self.save_btn.setIcon(_icon("fa5s.check", color=d))
        QTimer.singleShot(1000, self._reset_save_icon)

    def _reset_save_icon(self):
        d = self._theme_colors["TEXT_DIM"]
        self.save_btn.setIcon(_icon("fa5s.save", color=d))

    def _copy_to_clipboard(self):
        text = self.editor.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            d = self._theme_colors["TEXT_DIM"]
            self.copy_btn.setIcon(_icon("fa5s.check", color=d))
            QTimer.singleShot(1000, self._reset_copy_icon)

    def _reset_copy_icon(self):
        d = self._theme_colors["TEXT_DIM"]
        self.copy_btn.setIcon(_icon("fa5s.copy", color=d))

    # ─── eksport notatek ───

    def _show_export_dialog(self):
        """Pokazuje dialog eksportu z wyborem formatu."""
        C = self._theme_colors

        dialog = DraggableDialog(self)
        dialog.setObjectName("ExportDialog")
        dialog.setFixedSize(380, 280)
        dialog.setStyleSheet(f"""
            QDialog#ExportDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Eksport notatek")
        title.setFont(self._make_font(SIZES["HEADER_FONT_SIZE"], bold=True))
        title.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        layout.addWidget(title)

        from PyQt6.QtWidgets import QRadioButton, QButtonGroup

        format_group = QButtonGroup(dialog)
        formats = [
            ("json", "JSON (backup \u2013 wszystkie notatki)"),
            ("md_all", "Markdown \u2013 wszystkie notatki"),
            ("md_single", "Markdown \u2013 pojedyncza notatka"),
            ("txt", "TXT \u2013 pojedyncza notatka"),
        ]

        for fmt_id, fmt_label in formats:
            rb = QRadioButton(fmt_label)
            rb.setFont(self._make_font(SIZES["BASE_FONT_SIZE"]))
            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {C['TEXT_MAIN']};
                    background: transparent;
                    spacing: 8px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid {C['ACCENT']};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {C['ACCENT']};
                }}
            """)
            rb.setChecked(fmt_id == "json")
            format_group.addButton(rb)
            rb._fmt_id = fmt_id
            layout.addWidget(rb)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_export = QPushButton("Eksportuj")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)

        btn_cancel = QPushButton("Anuluj")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {C["TEXT_DIM"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 8px;
                padding: 10px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
                color: {C["TEXT_MAIN"]};
            }}
        """)

        def do_export():
            checked = format_group.checkedButton()
            if not checked:
                return
            fmt = checked._fmt_id
            dialog.accept()
            self._execute_export(fmt)

        btn_export.clicked.connect(do_export)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        center = self.geometry().center()
        dialog.move(center.x() - dialog.width() // 2, center.y() - dialog.height() // 2)
        dialog.exec()
        dialog.deleteLater()

    def _execute_export(self, fmt: str):
        """Wykonuje eksport w wybranym formacie."""
        from PyQt6.QtWidgets import QFileDialog

        C = self._theme_colors

        if fmt == "json":
            path, _ = QFileDialog.getSaveFileName(
                self, "Eksport JSON", "antispaghetti_backup.json", "JSON (*.json)"
            )
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(self._notes, f, ensure_ascii=False, indent=2)
                    self._show_export_success(f"Zapisano {len(self._notes)} notatek")
                except Exception as e:
                    self._show_export_error(str(e))

        elif fmt == "md_single":
            if self._active_note_id is None:
                self._show_export_error("Nie wybrano notatki")
                return
            note = next((n for n in self._notes if n["id"] == self._active_note_id), None)
            if not note:
                return
            path, _ = QFileDialog.getSaveFileName(
                self, "Eksport Markdown", f"{self._sanitize_filename(note['name'])}.md", "Markdown (*.md)"
            )
            if path:
                try:
                    content = f"# {note['name']}\n\n"
                    content += f"*Utworzono: {note.get('created_at', 'nieznany')}*\n"
                    content += f"*Zaktualizowano: {note.get('updated_at', 'nieznany')}*\n\n"
                    content += note.get("content", "")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self._show_export_success(f"Zapisano: {path}")
                except Exception as e:
                    self._show_export_error(str(e))

        elif fmt == "md_all":
            path, _ = QFileDialog.getSaveFileName(
                self, "Eksport Markdown", "antispaghetti_notes.md", "Markdown (*.md)"
            )
            if path:
                try:
                    lines = ["# Anti-Spaghetti \u2013 Eksport notatek\n\n"]
                    for note in self._notes:
                        lines.append(f"## {note['name']}\n\n")
                        lines.append(f"*ID: {note['id']}*\n")
                        lines.append(f"*Utworzono: {note.get('created_at', 'nieznany')}*\n")
                        lines.append(f"*Zaktualizowano: {note.get('updated_at', 'nieznany')}*\n\n")
                        lines.append(note.get("content", ""))
                        lines.append("\n\n---\n\n")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write("".join(lines))
                    self._show_export_success(f"Zapisano {len(self._notes)} notatek")
                except Exception as e:
                    self._show_export_error(str(e))

        elif fmt == "txt":
            if self._active_note_id is None:
                self._show_export_error("Nie wybrano notatki")
                return
            note = next((n for n in self._notes if n["id"] == self._active_note_id), None)
            if not note:
                return
            path, _ = QFileDialog.getSaveFileName(
                self, "Eksport TXT", f"{self._sanitize_filename(note['name'])}.txt", "Text (*.txt)"
            )
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(note.get("content", ""))
                    self._show_export_success(f"Zapisano: {path}")
                except Exception as e:
                    self._show_export_error(str(e))

    def _show_export_success(self, msg: str):
        """Pokazuje potwierdzenie eksportu."""
        C = self._theme_colors
        dialog = DraggableDialog(self)
        dialog.setFixedSize(340, 140)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid #27ae60;
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        lbl = QLabel("Eksport zako\u0144czony")
        lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
        lbl.setStyleSheet("color: #27ae60; background: transparent;")
        layout.addWidget(lbl)

        msg_lbl = QLabel(msg)
        msg_lbl.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        msg_lbl.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        btn = QPushButton("OK")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)

        center = self.geometry().center()
        dialog.move(center.x() - dialog.width() // 2, center.y() - dialog.height() // 2)
        dialog.exec()
        dialog.deleteLater()

    def _show_export_error(self, msg: str):
        """Pokazuje błąd eksportu."""
        C = self._theme_colors
        dialog = DraggableDialog(self)
        dialog.setFixedSize(340, 140)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid #e74c3c;
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        lbl = QLabel("B\u0142\u0105d eksportu")
        lbl.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
        lbl.setStyleSheet("color: #e74c3c; background: transparent;")
        layout.addWidget(lbl)

        msg_lbl = QLabel(msg)
        msg_lbl.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        msg_lbl.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        btn = QPushButton("OK")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)

        center = self.geometry().center()
        dialog.move(center.x() - dialog.width() // 2, center.y() - dialog.height() // 2)
        dialog.exec()
        dialog.deleteLater()

    # ─── menu kontekstowe edytora i wyszukiwarki ───

    def _editor_context_menu(self, pos):
        menu = QMenu(self)
        clipboard = QApplication.clipboard()
        actions = {
            "Cofnij":   (self.editor.undo, self.editor.document().isUndoAvailable()),
            "Pon\u00f3w":  (self.editor.redo, self.editor.document().isRedoAvailable()),
        }
        for label, (slot, enabled) in actions.items():
            a = menu.addAction(label)
            a.setEnabled(enabled)
            a.triggered.connect(slot)

        menu.addSeparator()

        actions2 = {
            "Wytnij":   (self.editor.cut,   self.editor.textCursor().hasSelection()),
            "Kopiuj":   (self.editor.copy,  self.editor.textCursor().hasSelection()),
            "Wklej":    (self.editor.paste, clipboard.text() != ""),
            "Zaznacz wszystko": (self.editor.selectAll, True),
        }
        for label, (slot, enabled) in actions2.items():
            a = menu.addAction(label)
            a.setEnabled(enabled)
            a.triggered.connect(slot)
        menu.exec(self.editor.mapToGlobal(pos))

    def _search_context_menu(self, pos):
        menu = QMenu(self)
        clipboard = QApplication.clipboard()
        has_sel = len(self.search_edit.selectedText()) > 0
        actions = {
            "Wytnij":   (self.search_edit.cut,   has_sel),
            "Kopiuj":   (self.search_edit.copy,  has_sel),
            "Wklej":    (self.search_edit.paste, clipboard.text() != ""),
            "Zaznacz wszystko": (self.search_edit.selectAll, True),
        }
        for label, (slot, enabled) in actions.items():
            a = menu.addAction(label)
            a.setEnabled(enabled)
            a.triggered.connect(slot)
        menu.exec(self.search_edit.mapToGlobal(pos))

    # ─── wyszukiwanie ───

    def _on_search_text_changed(self, text: str):
        self._search_timer.start(200)

    def _do_search(self):
        text = self.search_edit.text().lower().strip()
        if not text:
            for btn in self._buttons:
                btn.setVisible(True)
            self.count_label.setText(f"{len(self._notes)} element\u00f3w")
            return

        matching_ids = set()
        for note in self._notes:
            note_name = note.get("name", "")
            note_content = note.get("content", "")
            if isinstance(note_name, str) and isinstance(note_content, str):
                if text in note_name.lower() or text in note_content.lower():
                    matching_ids.add(note["id"])

        visible_count = 0
        for btn in self._buttons:
            visible = btn._note_id in matching_ids
            btn.setVisible(visible)
            if visible:
                visible_count += 1
        self.count_label.setText(f"{visible_count} z {len(self._notes)}")

    # ─── liczniki ───

    def _on_text_changed(self):
        if self._creating_note:
            return
        self._dirty = True
        # Restartuj timer auto-zapisu
        self._auto_save_timer.start(5000)
        if self._active_note_id is None:
            text = self.editor.toPlainText()
            if text.strip():
                self._auto_create_note(text)
                return
        # Debounce - opóźnij aktualizację liczników
        if not hasattr(self, '_counter_timer'):
            self._counter_timer = QTimer(self)
            self._counter_timer.setSingleShot(True)
            self._counter_timer.timeout.connect(self._update_counters)
        self._counter_timer.start(100)

    def _auto_create_note(self, text: str):
        self._creating_note = True
        now = datetime.now().isoformat()
        first_line = text.strip().split("\n")[0].strip()
        name = first_line[:50] if first_line else f"Notatka {len(self._notes) + 1}"
        note_id = str(uuid.uuid4())
        note = {"id": note_id, "name": name, "content": text.strip(),
                "created_at": now, "updated_at": now}
        self._notes.insert(0, note)
        self._active_note_id = note_id
        self._rebuild_sidebar()
        for btn in self._buttons:
            btn.setChecked(btn._note_id == note_id)
        self.header.setText(name)
        self._dirty = False
        self._creating_note = False
        self._update_counters()

    def _update_counters(self):
        count = len(self._notes)
        self.count_label.setText(f"{count} elementów")
        text = self.editor.toPlainText()
        tokens = max(1, len(text) // 4) if text.strip() else 0
        ts = ""
        if self._active_note_id is not None:
            note = next((n for n in self._notes if n["id"] == self._active_note_id), None)
            if note and note.get("updated_at"):
                try:
                    dt = datetime.fromisoformat(note["updated_at"])
                    now = datetime.now()
                    diff = now - dt
                    if diff.total_seconds() < 60:
                        ts = " • przed chwilą"
                    elif diff.total_seconds() < 3600:
                        ts = f" • {int(diff.total_seconds() // 60)} min temu"
                    elif diff.total_seconds() < 86400:
                        ts = f" • {int(diff.total_seconds() // 3600)} godz. temu"
                    else:
                        ts = f" • {dt.strftime('%d.%m.%Y')}"
                except Exception:
                    pass
        self.tokens_label.setText(f"~{tokens} tokenów{ts}")

    # ─── zmiana kolejnosci ───

    def _reorder_notes(self, note_id: str, new_index: int):
        old_index = next(
            (i for i, n in enumerate(self._notes) if n["id"] == note_id), None
        )
        if old_index is None:
            return
        new_index = max(0, min(new_index, len(self._notes) - 1))
        note = self._notes.pop(old_index)
        self._notes.insert(new_index, note)
        self.save_notes()

    # ─── ustawienia – rozbudowane menu ───

    def _show_about(self):
        C = self._theme_colors

        dialog = DraggableDialog(self)
        dialog.setObjectName("AboutDialog")
        dialog.setFixedSize(400, 260)
        dialog.setStyleSheet(f"""
            QDialog#AboutDialog {{
                background-color: {C["BG_EDITOR"]};
                border: 1px solid {C["SEPARATOR"]};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Anti-Spaghetti")
        title.setFont(self._make_font(SIZES["HEADER_FONT_SIZE"], bold=True))
        title.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        ver = QLabel(f"v{__version__}")
        ver.setFont(self._make_font(SIZES["SMALL_FONT_SIZE"]))
        ver.setStyleSheet(f"color: {C['TEXT_DIM']}; background: transparent;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        desc = QLabel(
            "Podręczny notatnik-składnica.\n"
            "Zapisuj fragmenty tekstu – prompty,\n"
            "klucze API, przepisy, notatki."
        )
        desc.setFont(self._make_font(SIZES["BASE_FONT_SIZE"]))
        desc.setStyleSheet(f"color: {C['TEXT_MAIN']}; background: transparent;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch()

        btn_close = QPushButton("OK")
        btn_close.setFont(self._make_font(SIZES["BASE_FONT_SIZE"], bold=True))
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {C["ACCENT"]};
                color: {C["TEXT_MAIN"]};
                border: none;
                border-radius: 8px;
                padding: 8px 0px;
                font-size: {SIZES["BASE_FONT_SIZE"]}px;
            }}
            QPushButton:hover {{
                background-color: {C["BG_BTN_HOVER"]};
            }}
        """)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        center = self.geometry().center()
        dialog.move(
            center.x() - dialog.width() // 2,
            center.y() - dialog.height() // 2,
        )
        dialog.exec()
        dialog.deleteLater()

    def _on_settings_clicked(self):
        menu = QMenu(self)

        # --- Motyw ---
        theme_menu = menu.addMenu("Motyw")
        for name in THEMES:
            a = theme_menu.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == self._theme_name)
            a.triggered.connect(lambda checked, n=name: self._apply_theme(n))

        menu.addSeparator()

        # --- PIN ---
        if self._pin_hash is None:
            menu.addAction("Ustaw PIN", self._set_pin)
        else:
            pin_menu = menu.addMenu("PIN")
            pin_menu.addAction("Zmień PIN", self._set_pin)
            pin_menu.addAction("Usuń PIN", self._remove_pin)

        menu.addSeparator()

        # --- O programie ---
        menu.addAction("O programie", self._show_about)

        menu.exec(self.settings_btn.mapToGlobal(
            self.settings_btn.rect().bottomLeft()
        ))

    # ─── zamkniecie ───

    def closeEvent(self, event):
        self._sync_editor_to_note()
        self._auto_save_timer.stop()
        self._auto_save()
        try:
            self.save_notes()
        except Exception as e:
            log.error("Blad zapisu przy zamykaniu: %s", e)
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.critical(
                self, "Błąd zapisu",
                "Nie udało się zapisać notatek.\nZamknąć mimo to?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        finally:
            self._release_lock()
        event.accept()


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
def main():
    """Punkt wejścia aplikacji Anti-Spaghetti."""
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)

    font_dir = Path(__file__).parent / "fonts"
    if font_dir.exists():
        for f in font_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(f))

    font = QFont("Intel One Mono", SIZES["BASE_FONT_SIZE"])
    if not font.exactMatch():
        font = QFont("Consolas", SIZES["BASE_FONT_SIZE"])
    app.setFont(font)

    app.setStyleSheet(f"""
        QMenu {{
            background-color: {BG_BTN};
            color: {TEXT_MAIN};
            border: 1px solid {SEPARATOR};
            border-radius: 6px;
            padding: 4px;
            font-size: {SIZES["BASE_FONT_SIZE"]}px;
        }}
        QMenu::item {{
            padding: 6px 24px 6px 16px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {BG_BTN_HOVER};
        }}
        QMenu::item:checked {{
            font-weight: bold;
        }}
        QMenu::indicator {{
            width: 12px;
            height: 12px;
            margin-left: 4px;
        }}
        QMenu::separator {{
            height: 1px;
            background: {SEPARATOR};
            margin: 4px 8px;
        }}
    """)

    window = MainWindow()
    app.aboutToQuit.connect(window._release_lock)
    atexit.register(window._release_lock)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
