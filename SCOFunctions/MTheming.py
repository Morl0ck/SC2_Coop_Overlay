from dataclasses import dataclass
from PyQt5 import QtCore, QtGui, QtWidgets


@dataclass
class Colors:
    """ Dataclass for colors used in the app.
    It's separate from a palette used by PyQt5 """

    msg = "#555"
    msg_success = "green"
    msg_failure = 'red'
    chat_main = '#55f'
    chat_other = '#558F22'
    player_highlight = "#55f"
    game_defeat = '#f44'
    game_weekly = '#00971e'


MColors = Colors()

TITLE_BAR_HEIGHT = 24
MAIN_TAB_WIDGET_ID = 'MainTabWidget'
TAB_BORDER = '#555'
TAB_INACTIVE_BG = '#373737'
TAB_ACTIVE_BG = '#454545'


def dark_tab_stylesheet() -> str:
    """Offset tabs below the custom title bar and keep the active tab flush with the pane."""
    h = TITLE_BAR_HEIGHT
    main = f'QTabWidget#{MAIN_TAB_WIDGET_ID}'
    return (
        f"{main}::tab-bar {{ subcontrol-origin: margin; top: {h}px; }}"
        f"{main}::pane {{ subcontrol-origin: margin; top: {h - 1}px; border: 1px solid {TAB_BORDER};"
        f" background: {TAB_ACTIVE_BG}; }}"
        f"{main} QTabBar::tab {{ background: {TAB_INACTIVE_BG}; color: white; border: 1px solid {TAB_BORDER};"
        f" border-bottom-color: {TAB_BORDER}; padding: 5px 10px; }}"
        f"{main} QTabBar::tab:selected {{ background: {TAB_ACTIVE_BG}; border-bottom-color: {TAB_ACTIVE_BG};"
        f" margin-bottom: -1px; padding-bottom: 6px; }}"
        f"{main} QTabBar::tab:!selected {{ margin-top: 2px; }}"
    )


def overlay_tab_stylesheet() -> str:
    """ Shared styling for the overlay settings tabs (Mission Overlay, Build Order). """
    card_bg = '#404040'
    card_border = '#666'
    accent = '#4791ff'
    text_primary = '#f0f0f0'
    text_secondary = '#c8c8c8'
    text_muted = '#a8a8a8'
    return (
        f"QLabel#OverlayPageTitle {{ color: {text_primary}; font-size: 16px; font-weight: 600; }}"
        f"QLabel#OverlaySectionTitle {{ color: {text_primary}; font-size: 13px; font-weight: 600; }}"
        f"QLabel#OverlayFieldLabel {{ color: {text_primary}; }}"
        f"QLabel#OverlaySubsectionLabel {{ color: {text_secondary}; font-size: 11px; font-weight: 600; }}"
        f"QLabel#OverlayHintLabel {{ color: {text_secondary}; font-size: 11px; }}"
        f"QLabel#OverlayHintLabel a {{ color: {accent}; }}"
        f"QLabel#OverlayUnitLabel {{ color: {text_muted}; }}"
        f"QFrame#OverlaySectionCard, QFrame#OverlayFooterBar {{"
        f" background: {card_bg}; border: 1px solid {card_border}; border-radius: 4px; }}"
        f"QTabWidget#OverlaySubTabs::pane {{ border: 1px solid {card_border}; background: {TAB_ACTIVE_BG};"
        f" border-radius: 4px; top: -1px; }}"
        f"QTabWidget#OverlaySubTabs QTabBar::tab {{ background: {TAB_INACTIVE_BG}; color: {text_primary};"
        f" padding: 6px 14px; border: 1px solid {card_border}; border-bottom: none; margin-right: 2px; }}"
        f"QTabWidget#OverlaySubTabs QTabBar::tab:selected {{ background: {TAB_ACTIVE_BG};"
        f" border-bottom: 1px solid {TAB_ACTIVE_BG}; }}"
        f"QPushButton#OverlayPrimaryButton {{ background: {accent}; color: white; font-weight: 600;"
        f" border: 1px solid #3a7fd8; padding: 6px 14px; }}"
        f"QPushButton#OverlayPrimaryButton:hover {{ background: #5aa0ff; }}"
        f"QPushButton#OverlaySecondaryButton {{ padding: 6px 14px; }}"
        f"QPushButton#OverlaySecondaryButton:checked {{ background: #555; border: 1px solid #777; }}"
    )


def stats_tab_stylesheet() -> str:
    card_bg = '#404040'
    card_border = '#666'
    text_primary = '#f0f0f0'
    text_secondary = '#c8c8c8'
    return (
        f"QFrame#StatsFilterCard {{ background: {card_bg}; border: 1px solid {card_border}; border-radius: 4px; }}"
        f"QLabel#StatsSectionTitle {{ color: {text_primary}; font-weight: 600; font-size: 12px; }}"
        f"QLabel#StatsSummaryLabel {{ color: {text_secondary}; font-size: 11px; }}"
        f"QLabel#StatsHintLabel {{ color: {text_secondary}; }}"
        f"QTabWidget#StatsResultsTabs::pane {{ border: 1px solid {card_border}; background: {TAB_ACTIVE_BG};"
        f" border-radius: 4px; top: -1px; }}"
    )


def refresh_scroll_tab_layouts(main):
    """Re-fit scroll areas after the window gains the custom title bar."""
    for tab in (main.TAB_Players, main.TAB_Games, main.TAB_Mutations):
        if hasattr(tab, 'update_scroll_layout'):
            tab.update_scroll_layout()
    if hasattr(main, 'TAB_Stats') and hasattr(main.TAB_Stats, 'update_results_layout'):
        main.TAB_Stats.update_results_layout()


def set_dark_theme(main, app, tab, version):
    MColors.msg = "#ccc"
    MColors.msg_success = '#4f4'
    MColors.msg_failure = '#f44'
    MColors.chat_main = '#4791ff'
    MColors.chat_other = '#20DE49'
    MColors.player_highlight = '#77f'
    MColors.game_weekly = '#4bc53b'

    DARK0 = QtGui.QColor(33, 33, 33)
    DARK1 = QtGui.QColor(55, 55, 55)
    ALT = QtGui.QColor(83, 83, 83)
    LINK = QtGui.QColor(200, 200, 200)
    ORG = QtGui.QColor(255, 125, 0)

    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)

    dark_palette.setColor(QtGui.QPalette.Button, DARK1)
    dark_palette.setColor(QtGui.QPalette.Background, DARK1)  # far background
    dark_palette.setColor(QtGui.QPalette.Base, DARK0)  # bg of checkboxes, edit fields

    dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)

    dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    dark_palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.white)
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    dark_palette.setColor(QtGui.QPalette.AlternateBase, ALT)
    dark_palette.setColor(QtGui.QPalette.Link, LINK)

    dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtCore.Qt.darkGray)
    dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Foreground, QtCore.Qt.darkGray)
    dark_palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtCore.Qt.darkGray)

    app.setStyle('Fusion')
    app.setPalette(dark_palette)

    # Remove title bar because it cannot by stylized
    tab.dark_mode_active = True
    tab.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Window)
    tab.show()

    # Update title and show new button
    tab.title_bar.new_title.setText(f"StarCraft Co-op Overlay (v{str(version)[0]}.{str(version)[1:]})")
    tab.title_bar.show()
    tab.title_bar.activate()
    tab.setFixedSize(980, 610 + TITLE_BAR_HEIGHT)
    refresh_scroll_tab_layouts(main)

    # Small tweaks
    main.TAB_Games.WD_RecentGamesHeading.setStyleSheet('background-color: #454545; font-weight: bold')
    main.TAB_Games.GameTabLine.setStyleSheet('background-color: #777')
    main.TAB_Games.ed_games_search.setStyleSheet('QLineEdit {background-color: #333; font-weight: normal}'
                                                 'QToolTip {color:black; background-color: #ffffe1; font-weight: normal}')

    main.TAB_Players.WD_WinratesHeading.setStyleSheet("QWidget {background-color: #454545} QLabel {font-weight: bold}")
    main.TAB_Players.PlayerTabLine.setStyleSheet('background-color: #777')
    main.TAB_Players.ED_Player_seach.setStyleSheet('QLineEdit {background-color: #333}'
                                                   'QToolTip {color:black; background-color: #ffffe1; font-weight: normal}')

    main.TAB_Randomizer.BT_RNG_Description.setEnabled(True)

    tab.setStyleSheet(dark_tab_stylesheet()
                      + overlay_tab_stylesheet()
                      + stats_tab_stylesheet()
                      + "QScrollArea > QWidget > QWidget {background: #454545}"
                      "QPushButton {background: #454545}"
                      "QScrollArea QLineEdit {background: #333}"
                      "QToolTip {color: black; background-color: #ffffe1; font-weight: normal}")
