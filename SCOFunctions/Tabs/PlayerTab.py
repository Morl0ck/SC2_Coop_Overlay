from functools import partial

from PyQt5 import QtWidgets, QtGui, QtCore
import SCOFunctions.MUserInterface as MUI
from SCOFunctions.Settings import Setting_manager as SM


class PlayerTab(QtWidgets.QWidget):
    HEADING_HEIGHT = 31

    def __init__(self, parent, TabWidget):
        super().__init__()
        self.p = parent
        self.filter_players_running = False
        self.player_winrate_UI_dict = dict()
        self.last_ally_player = None
        self.showing_players = 50

        # Scroll
        self.SC_PlayersScrollArea = QtWidgets.QScrollArea(self)
        self.SC_PlayersScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.SC_PlayersScrollArea.setFrameShadow(QtWidgets.QFrame.Plain)
        self.SC_PlayersScrollArea.setWidgetResizable(True)
        self.SC_PlayersScrollArea.verticalScrollBar().valueChanged.connect(self.scrollbar_moved)

        self.SC_PlayersScrollAreaContents = QtWidgets.QWidget()
        self.SC_PlayersScrollAreaContents.setGeometry(QtCore.QRect(0, 31, 961, 530))
        self.SC_PlayersScrollAreaContentsLayout = QtWidgets.QVBoxLayout()
        self.SC_PlayersScrollAreaContentsLayout.setAlignment(QtCore.Qt.AlignTop)
        self.SC_PlayersScrollAreaContentsLayout.setContentsMargins(10, 0, 0, 0)
        self.SC_PlayersScrollAreaContentsLayout.setSpacing(0)

        # Heading
        self.WD_WinratesHeading = QtWidgets.QWidget(self)
        self.WD_WinratesHeading.setGeometry(QtCore.QRect(0, 0, 981, 31))
        self.WD_WinratesHeading.setStyleSheet("QLabel {font-weight:bold}")
        self.WD_WinratesHeading.setAutoFillBackground(True)
        self.WD_WinratesHeading.setBackgroundRole(QtGui.QPalette.Background)
        self.WD_WinratesHeading.p = self

        self.LA_Name = MUI.SortingQLabel(self.WD_WinratesHeading)
        self.LA_Name.setText('Name')
        self.LA_Name.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.LA_Name.setGeometry(QtCore.QRect(30, 0, 100, 31))
        self.LA_Name.clicked.connect(partial(self.sort_players, self.LA_Name))

        self.LA_Wins = MUI.SortingQLabel(self.WD_WinratesHeading, reverse=True)
        self.LA_Wins.setText('Wins')
        self.LA_Wins.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_Wins.setGeometry(QtCore.QRect(145, 0, 50, 31))
        self.LA_Wins.clicked.connect(partial(self.sort_players, self.LA_Wins))

        self.LA_Losses = MUI.SortingQLabel(self.WD_WinratesHeading, reverse=True)
        self.LA_Losses.setText('Losses')
        self.LA_Losses.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_Losses.setGeometry(QtCore.QRect(215, 0, 45, 31))
        self.LA_Losses.clicked.connect(partial(self.sort_players, self.LA_Losses))

        self.LA_Winrate = MUI.SortingQLabel(self.WD_WinratesHeading, reverse=True)
        self.LA_Winrate.setText('Winrate')
        self.LA_Winrate.setGeometry(QtCore.QRect(270, 0, 51, 31))
        self.LA_Winrate.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_Winrate.clicked.connect(partial(self.sort_players, self.LA_Winrate))

        self.LA_PL_APM = MUI.SortingQLabel(self.WD_WinratesHeading, reverse=True)
        self.LA_PL_APM.setText('APM')
        self.LA_PL_APM.setGeometry(QtCore.QRect(325, 0, 51, 31))
        self.LA_PL_APM.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_PL_APM.setToolTip('Median APM')
        self.LA_PL_APM.clicked.connect(partial(self.sort_players, self.LA_PL_APM))

        self.LA_PL_Kills = MUI.SortingQLabel(self.WD_WinratesHeading, reverse=True)
        self.LA_PL_Kills.setText('Kills')
        self.LA_PL_Kills.setGeometry(QtCore.QRect(380, 0, 51, 31))
        self.LA_PL_Kills.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_PL_Kills.setToolTip('Median percent of kills')
        self.LA_PL_Kills.clicked.connect(partial(self.sort_players, self.LA_PL_Kills))

        self.LA_PL_Commander = MUI.SortingQLabel(self.WD_WinratesHeading)
        self.LA_PL_Commander.setText('#1 Com')
        self.LA_PL_Commander.setGeometry(QtCore.QRect(430, 0, 81, 31))
        self.LA_PL_Commander.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_PL_Commander.setToolTip('The most played commander')
        self.LA_PL_Commander.clicked.connect(partial(self.sort_players, self.LA_PL_Commander))

        self.LA_PL_Frequency = MUI.SortingQLabel(self.WD_WinratesHeading, reverse=True)
        self.LA_PL_Frequency.setText('Frequency')
        self.LA_PL_Frequency.setGeometry(QtCore.QRect(495, 0, 81, 31))
        self.LA_PL_Frequency.setAlignment(QtCore.Qt.AlignCenter)
        self.LA_PL_Frequency.setToolTip('The most played commander frequency')
        self.LA_PL_Frequency.clicked.connect(partial(self.sort_players, self.LA_PL_Frequency))

        self.LA_Wins.activate()

        self.LA_Note = QtWidgets.QLabel("Player note", self.WD_WinratesHeading)
        self.LA_Note.setGeometry(QtCore.QRect(620, 0, 100, 31))
        self.LA_Note.setAlignment(QtCore.Qt.AlignCenter)

        # Search
        self.ED_Player_seach = QtWidgets.QLineEdit(self.WD_WinratesHeading)
        self.ED_Player_seach.setGeometry(QtCore.QRect(740, 5, 160, 20))
        self.ED_Player_seach.setAlignment(QtCore.Qt.AlignCenter)
        self.ED_Player_seach.setPlaceholderText("Search")
        self.ED_Player_seach.setToolTip("Search for players")
        self.ED_Player_seach.textChanged.connect(self.filter_players)

        self.bt_games_search = QtWidgets.QPushButton(self.WD_WinratesHeading)
        self.bt_games_search.setGeometry(QtCore.QRect(910, 3, 25, 25))
        self.bt_games_search.setStyleSheet("font-weight: normal")
        self.bt_games_search.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, 'SP_FileDialogContentsView')))
        self.bt_games_search.clicked.connect(self.filter_players)
        self.bt_games_search.setShortcut("Return")

        self.PlayerTabLine = MUI.Cline(self.WD_WinratesHeading)
        self.PlayerTabLine.setGeometry(QtCore.QRect(20, 30, 921, 1))

        # Wait
        self.LA_Winrates_Wait = QtWidgets.QLabel(self)
        self.LA_Winrates_Wait.setGeometry(QtCore.QRect(0, 0, self.SC_PlayersScrollAreaContents.width(), self.SC_PlayersScrollAreaContents.height()))
        self.LA_Winrates_Wait.setText('<b>Please wait. This can take few minutes the first time.<br>Analyzing your replays.</b>')
        self.LA_Winrates_Wait.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)

        self.update_scroll_layout()

    def update_scroll_layout(self):
        if self.width() <= 0 or self.height() <= 0:
            return
        self.WD_WinratesHeading.setGeometry(QtCore.QRect(0, 0, self.width(), self.HEADING_HEIGHT))
        self.PlayerTabLine.setGeometry(QtCore.QRect(20, self.HEADING_HEIGHT - 1, self.width() - 59, 1))
        self.SC_PlayersScrollArea.setGeometry(
            QtCore.QRect(0, self.HEADING_HEIGHT, max(self.width() - 5, 0), max(self.height() - self.HEADING_HEIGHT, 0)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scroll_layout()

    def _sorted_player_names(self):
        if not hasattr(self.p, 'winrate_data') or not self.p.winrate_data:
            return []

        players = list(self.p.winrate_data.keys())
        if self not in MUI.SortingQLabel.active:
            return players

        sort_by = MUI.SortingQLabel.active[self].value
        reverse = MUI.SortingQLabel.active[self].reverse

        if sort_by == 'Name':
            players.sort(key=str.lower, reverse=reverse)
            return players

        def total(player, index):
            return self.p.winrate_data[player]['total'][index]

        def winrate(player):
            wins, losses = total(player, 0), total(player, 1)
            if wins + losses == 0:
                return 0
            return wins / (wins + losses)

        key_funcs = {
            'Wins': lambda player: total(player, 0),
            'Losses': lambda player: total(player, 1),
            'Winrate': winrate,
            'APM': lambda player: total(player, 2),
            'Kills': lambda player: total(player, 5),
            '#1 Com': lambda player: total(player, 3),
            'Frequency': lambda player: total(player, 4),
        }
        key_func = key_funcs.get(sort_by, lambda player: total(player, 0))
        players.sort(key=key_func, reverse=reverse)
        return players

    def _reorder_player_widgets(self):
        if not self.player_winrate_UI_dict:
            return
        for player in self._sorted_player_names():
            if player not in self.player_winrate_UI_dict:
                continue
            entry = self.player_winrate_UI_dict[player]
            self.SC_PlayersScrollAreaContentsLayout.removeWidget(entry.widget)
        for player in self._sorted_player_names():
            if player in self.player_winrate_UI_dict:
                self.SC_PlayersScrollAreaContentsLayout.addWidget(self.player_winrate_UI_dict[player].widget)

    def sort_players(self, caller=None):
        if type(caller) is MUI.SortingQLabel:
            caller.activate()
        self._reorder_player_widgets()

    def scrollbar_moved(self):
        """ Adds new players if we scrolled down"""
        if not self.SC_PlayersScrollArea.verticalScrollBar().value() > 0.95 * self.SC_PlayersScrollArea.verticalScrollBar().maximum():
            return

        self.showing_players += 5
        self.filter_players()

    def try_reducing_players(self):
        """ Tries to reduce the number of visible players"""
        if self.SC_PlayersScrollArea.verticalScrollBar().value() < 0.5 * self.SC_PlayersScrollArea.verticalScrollBar().maximum():
            self.showing_players = 50

    def put_player_first(self, player):
        """ Moves a player to the top spot in the player tab.
            Returns the last player on top (if any) to its position. """

        # Return the old player
        if self.last_ally_player is not None:
            w = self.player_winrate_UI_dict[self.last_ally_player]
            self.SC_PlayersScrollAreaContentsLayout.removeWidget(w.widget)

            # Find the position where to put it back
            wins = w.wins
            for idx, pplayer in enumerate(self.player_winrate_UI_dict):
                if wins >= self.player_winrate_UI_dict[pplayer].wins and idx > 0:
                    self.SC_PlayersScrollAreaContentsLayout.insertWidget(idx + 1, w.widget)
                    break

            # Color back
            w.highlight(False)

        # New player to top
        self.last_ally_player = player
        if player in self.player_winrate_UI_dict:
            # If it's there remove
            w = self.player_winrate_UI_dict[player]
            self.SC_PlayersScrollAreaContentsLayout.removeWidget(w.widget)

        else:
            # It's not there, create new one
            self.player_winrate_UI_dict[player] = MUI.PlayerEntry(player,
                                                                    self.p.winrate_data[player],
                                                                    SM.settings['player_notes'].get(player, None),
                                                                    self.SC_PlayersScrollAreaContents) #yapf: disable
            w = self.player_winrate_UI_dict[player]

        # Insert to top, show and change colors
        self.SC_PlayersScrollAreaContentsLayout.insertWidget(0, w.widget)
        w.highlight(True)
        w.widget.show()

    def update(self, winrate_data):
        """ Updates player tab based on provide winrate data """
        if self.LA_Winrates_Wait is not None:
            self.LA_Winrates_Wait.deleteLater()
            self.LA_Winrates_Wait = None

        self.try_reducing_players()

        # Create new or update top self.showing_players players
        for idx, player in enumerate(self._sorted_player_names()):
            if idx >= self.showing_players:
                break
            if not player in self.player_winrate_UI_dict:
                self.player_winrate_UI_dict[player] = MUI.PlayerEntry(player,
                                                                      winrate_data[player],
                                                                      SM.settings['player_notes'].get(player, None),
                                                                      self.SC_PlayersScrollAreaContents) #yapf: disable
                self.SC_PlayersScrollAreaContentsLayout.addWidget(self.player_winrate_UI_dict[player].widget)
            else:
                self.player_winrate_UI_dict[player].update_winrates(winrate_data[player])

        self._reorder_player_widgets()

        # Show top self.showing_players and hide the rest
        visible = set(self._sorted_player_names()[:self.showing_players])
        for player in self.player_winrate_UI_dict:
            if player in visible:
                self.player_winrate_UI_dict[player].show()
            else:
                self.player_winrate_UI_dict[player].hide()

        # Hide players not in winrate data
        for player in self.player_winrate_UI_dict:
            if not player in winrate_data:
                self.player_winrate_UI_dict[player].hide()

        self.SC_PlayersScrollAreaContents.setLayout(self.SC_PlayersScrollAreaContentsLayout)
        self.SC_PlayersScrollArea.setWidget(self.SC_PlayersScrollAreaContents)

    def filter_players(self):
        """ Filters only players with string in name or note """
        self.filter_players_running = True
        text = self.ED_Player_seach.text().lower()
        idx = 0
        created = 0
        matched = []

        self.try_reducing_players()

        for player in tuple(self.player_winrate_UI_dict):
            self.player_winrate_UI_dict[player].hide()

        for player in self._sorted_player_names():
            if text in player.lower():
                matched.append(player)

        for player, note in SM.settings['player_notes'].items():
            if player in matched or player not in self.p.winrate_data:
                continue
            if text in note.lower():
                matched.append(player)

        for player in matched:
            if idx >= self.showing_players:
                break

            if created > 100:
                self.p.wait_ms(5)
                created = 0

            if player not in self.player_winrate_UI_dict and player in self.p.winrate_data:
                created += 1
                self.player_winrate_UI_dict[player] = MUI.PlayerEntry(player,
                                                                    self.p.winrate_data[player],
                                                                    SM.settings['player_notes'].get(player, None),
                                                                    self.SC_PlayersScrollAreaContents) #yapf: disable
                self.SC_PlayersScrollAreaContentsLayout.addWidget(self.player_winrate_UI_dict[player].widget)
            if player in self.player_winrate_UI_dict:
                self.player_winrate_UI_dict[player].show()
            idx += 1

        self._reorder_player_widgets()
        self.filter_players_running = False