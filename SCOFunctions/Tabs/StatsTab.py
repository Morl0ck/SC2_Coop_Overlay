from functools import partial
from PyQt5 import QtWidgets, QtGui, QtCore
import SCOFunctions.MUserInterface as MUI
from SCOFunctions.MLogging import Logger

logger = Logger('STATS', Logger.levels.INFO)


class StatsTab(QtWidgets.QWidget):
    @staticmethod
    def _section_title(text):
        label = QtWidgets.QLabel(text)
        label.setObjectName('StatsSectionTitle')
        return label

    @staticmethod
    def _summary_label(text=''):
        label = QtWidgets.QLabel(text)
        label.setObjectName('StatsSummaryLabel')
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        return label

    @staticmethod
    def _filter_column(title, widgets):
        column = QtWidgets.QVBoxLayout()
        column.setSpacing(4)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(StatsTab._section_title(title))
        for widget in widgets:
            column.addWidget(widget)
        column.addStretch()
        return column

    def __init__(self, parent):
        super().__init__()
        self.p = parent
        self.stats_maps_UI_dict = dict()
        self.stats_region_UI_dict = dict()
        self.stats_mycommander_UI_dict = dict()
        self.stats_allycommander_UI_dict = dict()

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        self.FR_Stats = QtWidgets.QFrame(self)
        self.FR_Stats.setObjectName('StatsFilterCard')
        filters = QtWidgets.QVBoxLayout(self.FR_Stats)
        filters.setContentsMargins(14, 12, 14, 12)
        filters.setSpacing(10)

        self.CH_DiffCasual = QtWidgets.QCheckBox('Casual')
        self.CH_DiffCasual.setChecked(True)
        self.CH_DiffCasual.stateChanged.connect(self.generate_stats)

        self.CH_DiffNormal = QtWidgets.QCheckBox('Normal')
        self.CH_DiffNormal.setChecked(True)
        self.CH_DiffNormal.stateChanged.connect(self.generate_stats)

        self.CH_DiffHard = QtWidgets.QCheckBox('Hard')
        self.CH_DiffHard.setChecked(True)
        self.CH_DiffHard.stateChanged.connect(self.generate_stats)

        self.CH_DiffBrutal = QtWidgets.QCheckBox('Brutal')
        self.CH_DiffBrutal.setChecked(True)
        self.CH_DiffBrutal.stateChanged.connect(self.generate_stats)

        self.CH_DiffBrutalPlus = QtWidgets.QCheckBox('Brutal+')
        self.CH_DiffBrutalPlus.setChecked(True)
        self.CH_DiffBrutalPlus.stateChanged.connect(self.generate_stats)

        self.CH_Region_NA = QtWidgets.QCheckBox('Americas')
        self.CH_Region_NA.setChecked(True)
        self.CH_Region_NA.stateChanged.connect(self.generate_stats)

        self.CH_Region_EU = QtWidgets.QCheckBox('Europe')
        self.CH_Region_EU.setChecked(True)
        self.CH_Region_EU.stateChanged.connect(self.generate_stats)

        self.CH_Region_KR = QtWidgets.QCheckBox('Asia')
        self.CH_Region_KR.setChecked(True)
        self.CH_Region_KR.stateChanged.connect(self.generate_stats)

        self.CH_Region_CN = QtWidgets.QCheckBox('China')
        self.CH_Region_CN.setChecked(True)
        self.CH_Region_CN.stateChanged.connect(self.generate_stats)

        self.CH_TypeNormal = QtWidgets.QCheckBox('Normal games')
        self.CH_TypeNormal.setChecked(True)
        self.CH_TypeNormal.stateChanged.connect(self.generate_stats)

        self.CH_TypeMutation = QtWidgets.QCheckBox('Mutations')
        self.CH_TypeMutation.setChecked(True)
        self.CH_TypeMutation.stateChanged.connect(self.generate_stats)

        self.CH_TypeWins = QtWidgets.QCheckBox('Wins only')
        self.CH_TypeWins.setChecked(False)
        self.CH_TypeWins.stateChanged.connect(self.generate_stats)

        self.CH_AllHistoric = QtWidgets.QCheckBox('Override folder selection')
        self.CH_AllHistoric.setChecked(True)
        self.CH_AllHistoric.setToolTip('Shows stats from all replays regardless of which folder is selected')
        self.CH_AllHistoric.stateChanged.connect(self.generate_stats)

        self.CH_DualMain = QtWidgets.QCheckBox('Include multi-box games')
        self.CH_DualMain.setChecked(False)
        self.CH_DualMain.setToolTip('Include games where both players belong to your accounts')
        self.CH_DualMain.stateChanged.connect(self.generate_stats)

        self.CH_Sub15 = QtWidgets.QCheckBox('Include levels 1-14')
        self.CH_Sub15.setChecked(True)
        self.CH_Sub15.setToolTip('Include games where the main player was level 1-14')
        self.CH_Sub15.stateChanged.connect(self.generate_stats)

        self.CH_Over15 = QtWidgets.QCheckBox('Include levels 15+')
        self.CH_Over15.setChecked(True)
        self.CH_Over15.setToolTip('Include games where the main player was level 15+')
        self.CH_Over15.stateChanged.connect(self.generate_stats)

        filter_columns = QtWidgets.QHBoxLayout()
        filter_columns.setSpacing(18)
        filter_columns.addLayout(self._filter_column('Difficulty', [
            self.CH_DiffCasual, self.CH_DiffNormal, self.CH_DiffHard, self.CH_DiffBrutal, self.CH_DiffBrutalPlus,
        ]))
        filter_columns.addLayout(self._filter_column('Region', [
            self.CH_Region_NA, self.CH_Region_EU, self.CH_Region_KR, self.CH_Region_CN,
        ]))
        filter_columns.addLayout(self._filter_column('Game type', [
            self.CH_TypeNormal, self.CH_TypeMutation, self.CH_TypeWins,
        ]))
        filter_columns.addLayout(self._filter_column('Scope', [
            self.CH_AllHistoric, self.CH_DualMain,
        ]))
        filter_columns.addLayout(self._filter_column('Account level', [
            self.CH_Sub15, self.CH_Over15,
        ]))
        filter_columns.addStretch()
        filters.addLayout(filter_columns)

        constraints_row = QtWidgets.QHBoxLayout()
        constraints_row.setSpacing(16)

        self.FR_DateTime = QtWidgets.QWidget(self.FR_Stats)
        constraints = QtWidgets.QGridLayout(self.FR_DateTime)
        constraints.setContentsMargins(0, 0, 0, 0)
        constraints.setHorizontalSpacing(10)
        constraints.setVerticalSpacing(6)

        self.LA_GameLength = self._section_title('Game length (minutes)')
        self.LA_ReplayDate = self._section_title('Replay date')
        constraints.addWidget(self.LA_GameLength, 0, 0, 1, 2)
        constraints.addWidget(self.LA_ReplayDate, 0, 3, 1, 2)

        self.SP_MinGamelength = QtWidgets.QSpinBox()
        self.SP_MinGamelength.setMinimum(0)
        self.SP_MinGamelength.setMaximum(1000)
        self.SP_MinGamelength.setProperty('value', 0)
        self.SP_MinGamelength.valueChanged.connect(self.generate_stats)
        self.LA_Minimum = QtWidgets.QLabel('Minimum')
        constraints.addWidget(self.SP_MinGamelength, 1, 0)
        constraints.addWidget(self.LA_Minimum, 1, 1)

        self.TM_FromDate = QtWidgets.QDateEdit()
        self.TM_FromDate.setDateTime(QtCore.QDateTime(QtCore.QDate(2015, 11, 10), QtCore.QTime(0, 0, 0)))
        self.TM_FromDate.setDisplayFormat('d/M/yyyy')
        self.TM_FromDate.dateChanged.connect(self.generate_stats)
        self.LA_From = QtWidgets.QLabel('From')
        constraints.addWidget(self.LA_From, 1, 3)
        constraints.addWidget(self.TM_FromDate, 1, 4)

        self.SP_MaxGamelength = QtWidgets.QSpinBox()
        self.SP_MaxGamelength.setMinimum(0)
        self.SP_MaxGamelength.setMaximum(1000)
        self.SP_MaxGamelength.setProperty('value', 0)
        self.SP_MaxGamelength.valueChanged.connect(self.generate_stats)
        self.LA_Maximum = QtWidgets.QLabel('Maximum')
        constraints.addWidget(self.SP_MaxGamelength, 2, 0)
        constraints.addWidget(self.LA_Maximum, 2, 1)

        self.TM_ToDate = QtWidgets.QDateEdit()
        self.TM_ToDate.setDateTime(QtCore.QDateTime(QtCore.QDate(2030, 12, 30), QtCore.QTime(0, 0, 0)))
        self.TM_ToDate.setDisplayFormat('d/M/yyyy')
        self.TM_ToDate.dateChanged.connect(self.generate_stats)
        self.LA_To = QtWidgets.QLabel('To')
        constraints.addWidget(self.LA_To, 2, 3)
        constraints.addWidget(self.TM_ToDate, 2, 4)

        self.ED_PlayerName = QtWidgets.QLineEdit()
        self.ED_PlayerName.setAlignment(QtCore.Qt.AlignLeft)
        self.ED_PlayerName.setToolTip('Filter by ally player name.\nYou can use ? and * as wildcards.')
        self.ED_PlayerName.setPlaceholderText('Filter by ally player name')
        self.ED_PlayerName.textChanged.connect(self.generate_stats)
        constraints.addWidget(self.ED_PlayerName, 3, 3, 1, 2)

        constraints_row.addWidget(self.FR_DateTime, 1)

        summary_col = QtWidgets.QVBoxLayout()
        summary_col.setSpacing(4)
        self.LA_GamesFound = self._summary_label()
        self.LA_IdentifiedPlayers = self._summary_label()
        self.BT_FA_dump = QtWidgets.QPushButton('Dump Data')
        self.BT_FA_dump.setToolTip('Dumps all replay data to "replay_data_dump.json" file')
        self.BT_FA_dump.setEnabled(False)
        summary_col.addStretch()
        summary_col.addWidget(self.LA_GamesFound)
        summary_col.addWidget(self.LA_IdentifiedPlayers)
        summary_col.addWidget(self.BT_FA_dump, 0, QtCore.Qt.AlignRight)
        constraints_row.addLayout(summary_col)
        filters.addLayout(constraints_row)

        root.addWidget(self.FR_Stats)

        ##### RESULTS #####
        self.TABW_StatResults = QtWidgets.QTabWidget()
        self.TABW_StatResults.setObjectName('StatsResultsTabs')

        ### TAB Maps
        self.TAB_Maps = QtWidgets.QWidget()
        self.GB_MapsOverview = QtWidgets.QFrame(self.TAB_Maps)
        self.WD_Heading = MUI.MapEntry(self.GB_MapsOverview,
                                       0,
                                       'Map name',
                                       'Fastest',
                                       'Avg',
                                       'Wins',
                                       'Losses',
                                       'Freq',
                                       'Bonus',
                                       bold=True,
                                       button=False,
                                       sort=self.map_sort_update)

        self.QB_FastestMap = MUI.FastestMap(self.TAB_Maps)

        self.LA_Stats_Wait = QtWidgets.QLabel(self.TAB_Maps)
        self.LA_Stats_Wait.setText('<b>Please wait. This can take few minutes the first time.<br>Analyzing your replays.</b>')
        self.LA_Stats_Wait.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)

        ### TAB Difficulty & Regions
        self.TAB_DifficultyRegions = QtWidgets.QWidget()
        self.LA_Difficulty_header = MUI.DifficultyEntry('Difficulty',
                                                        'Wins',
                                                        'Losses',
                                                        'Winrate',
                                                        50,
                                                        0,
                                                        bold=True,
                                                        line=True,
                                                        parent=self.TAB_DifficultyRegions)
        self.ProgressionStatsHeading = MUI.RegionStats('Region', {
            'Defeat': 'Losses',
            'Victory': 'Wins',
            'frequency': 'Frequency',
            'max_asc': 'Ascension level',
            'max_com': 'Maxed commanders',
            'winrate': 'Winrate',
            'prestiges': 'Prestiges unlocked'
        },
                                                       0,
                                                       parent=self.TAB_DifficultyRegions,
                                                       bold=True,
                                                       line=True)

        ### TAB Commanders
        self.TAB_MyCommanders = QtWidgets.QWidget()
        self.MyCommanderHeading = MUI.CommanderEntry('Commander',
                                                     'Freq',
                                                     'Wins',
                                                     'Losses',
                                                     'Win%',
                                                     'APM',
                                                     'Kills',
                                                     2,
                                                     bold=True,
                                                     button=False,
                                                     parent=self.TAB_MyCommanders,
                                                     sort=self.my_commander_sort_update)

        ### TAB Allied Commanders
        self.TAB_AlliedCommanders = QtWidgets.QWidget()
        self.LA_AlliedCommanders = self._summary_label('* Frequency has been corrected for your commander preferences')
        self.LA_AlliedCommanders.setParent(self.TAB_AlliedCommanders)

        self.AlliedCommanderHeading = MUI.CommanderEntry('Allied commander',
                                                         'Freq',
                                                         'Wins',
                                                         'Losses',
                                                         'Win%',
                                                         'APM',
                                                         'Kills',
                                                         2,
                                                         bold=True,
                                                         button=False,
                                                         parent=self.TAB_AlliedCommanders,
                                                         sort=self.ally_commander_sort_update)

        # Full analysis
        self.TAB_FullAnalysis = QtWidgets.QWidget()
        fa_layout = QtWidgets.QVBoxLayout(self.TAB_FullAnalysis)
        fa_layout.setContentsMargins(14, 12, 14, 12)
        fa_layout.setSpacing(10)

        self.CH_FA_description = QtWidgets.QLabel(
            'Run full analysis to get more accurate game lengths and APM, and see additional statistics '
            'related to player and unit kills, bonus objectives and other.<br><br>'
            '<b>Warning! This might take a long time and the PC will be less responsive.</b>')
        self.CH_FA_description.setWordWrap(True)
        self.CH_FA_description.setObjectName('StatsHintLabel')
        fa_layout.addWidget(self.CH_FA_description)

        fa_buttons = QtWidgets.QHBoxLayout()
        fa_buttons.setSpacing(8)
        self.BT_FA_run = QtWidgets.QPushButton('Run')
        self.BT_FA_run.setEnabled(False)
        self.BT_FA_stop = QtWidgets.QPushButton('Pause')
        self.BT_FA_stop.clicked.connect(self.p.stop_full_analysis)
        self.BT_FA_stop.setEnabled(False)
        self.BT_FA_redo = QtWidgets.QPushButton('Delete parsed data')
        self.BT_FA_redo.clicked.connect(self.p.redo_full_analysis)
        self.BT_FA_redo.setToolTip(
            'WARNING!\nThis will delete all parsed data and start the analysis anew.\n'
            'This might be useful after an update to the parser.')
        fa_buttons.addWidget(self.BT_FA_run)
        fa_buttons.addWidget(self.BT_FA_stop)
        fa_buttons.addStretch()
        fa_buttons.addWidget(self.BT_FA_redo)
        fa_layout.addLayout(fa_buttons)

        self.CH_FA_atstart = QtWidgets.QCheckBox('Continue full analysis at start')
        fa_layout.addWidget(self.CH_FA_atstart)

        self.CH_FA_status = QtWidgets.QLabel()
        self.CH_FA_status.setObjectName('StatsHintLabel')
        self.CH_FA_status.setWordWrap(True)
        fa_layout.addWidget(self.CH_FA_status)
        fa_layout.addStretch()

        # Putting it together
        self.TABW_StatResults.addTab(self.TAB_Maps, 'Maps')
        self.TABW_StatResults.addTab(self.TAB_AlliedCommanders, 'Allied commanders')
        self.TABW_StatResults.addTab(self.TAB_MyCommanders, 'My commanders')
        self.TABW_StatResults.addTab(self.TAB_DifficultyRegions, 'Difficulty and regions')
        self.TABW_StatResults.addTab(self.TAB_FullAnalysis, 'Full analysis')

        root.addWidget(self.TABW_StatResults, 1)

        self.TABW_StatResults.setCurrentIndex(0)
        self.TABW_StatResults.currentChanged.connect(self.switched_tab)
        self.update_results_layout()

    def update_results_layout(self):
        if self.TAB_Maps.width() <= 0 or self.TAB_Maps.height() <= 0:
            return
        margin = 8
        w = self.TAB_Maps.width()
        h = self.TAB_Maps.height()
        list_w = min(470, max((w - margin * 3) // 2, 280))
        detail_w = max(w - list_w - margin * 3, 280)
        panel_h = max(h - margin * 2, 200)
        self.GB_MapsOverview.setGeometry(margin, margin, list_w, panel_h)
        self.QB_FastestMap.setGeometry(margin + list_w + margin, margin, detail_w, panel_h)
        if self.LA_Stats_Wait is not None:
            self.LA_Stats_Wait.setGeometry(margin, margin, list_w, panel_h)
        if hasattr(self, 'LA_AlliedCommanders'):
            footnote_w = min(400, self.TAB_AlliedCommanders.width() - 16)
            self.LA_AlliedCommanders.setGeometry(
                max(self.TAB_AlliedCommanders.width() - footnote_w - margin, margin),
                max(self.TAB_AlliedCommanders.height() - 24, 0),
                footnote_w,
                20)

    def clear_wait_message(self):
        """Remove the analysis placeholder without leaving a stale Qt wrapper."""
        if self.LA_Stats_Wait is None:
            return
        self.LA_Stats_Wait.deleteLater()
        self.LA_Stats_Wait = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_results_layout()

    def generate_stats(self):
        """ Generate stats and passes data to be shown"""

        if self.p.CAnalysis is None:
            logger.error('Mass analysis hasn\'t finished yet')
            return

        # Check
        if self.CH_AllHistoric.isChecked():
            self.p.CAnalysis.update_data(showAll=True)
        else:
            self.p.CAnalysis.update_data(showAll=False)

        # Filter
        include_mutations = True if self.CH_TypeMutation.isChecked() else False
        include_normal_games = True if self.CH_TypeNormal.isChecked() else False

        difficulty_filter = set()
        if not self.CH_DiffCasual.isChecked():
            difficulty_filter.add('Casual')
        if not self.CH_DiffNormal.isChecked():
            difficulty_filter.add('Normal')
        if not self.CH_DiffHard.isChecked():
            difficulty_filter.add('Hard')
        if not self.CH_DiffBrutal.isChecked():
            difficulty_filter.add('Brutal')
        if not self.CH_DiffBrutalPlus.isChecked():
            difficulty_filter = difficulty_filter.union({1, 2, 3, 4, 5, 6})

        region_filter = set()
        if not self.CH_Region_NA.isChecked():
            region_filter.add('NA')
        if not self.CH_Region_EU.isChecked():
            region_filter.add('EU')
        if not self.CH_Region_KR.isChecked():
            region_filter.add('KR')
        if not self.CH_Region_CN.isChecked():
            region_filter.add('CN')

        mindate = self.TM_FromDate.date().toPyDate().strftime('%Y%m%d%H%M%S')
        mindate = None if mindate == '20151110000000' else int(mindate)
        maxdate = self.TM_ToDate.date().toPyDate().strftime('%Y%m%d%H%M%S')
        maxdate = None if maxdate == '20301230000000' else int(maxdate)

        minlength = None if self.SP_MinGamelength.value() == 0 else self.SP_MinGamelength.value()
        maxLength = None if self.SP_MaxGamelength.value() == 0 else self.SP_MaxGamelength.value()

        player = None if self.ED_PlayerName.text() == '' else self.ED_PlayerName.text().lower()

        winsonly = self.CH_TypeWins.isChecked()

        include_both_main = True if self.CH_DualMain.isChecked() else False
        sub_15 = True if self.CH_Sub15.isChecked() else False
        over_15 = True if self.CH_Over15.isChecked() else False

        ### Analyse
        analysis = self.p.CAnalysis.analyse_replays(include_mutations=include_mutations,
                                                    include_normal_games=include_normal_games,
                                                    difficulty_filter=difficulty_filter,
                                                    region_filter=region_filter,
                                                    mindate=mindate,
                                                    maxdate=maxdate,
                                                    minlength=minlength,
                                                    maxLength=maxLength,
                                                    sub_15=sub_15,
                                                    over_15=over_15,
                                                    include_both_main=include_both_main,
                                                    player=player,
                                                    winsonly=winsonly)

        self.LA_GamesFound.setText(f"Games found: {analysis['games']}")

        ### Map stats
        self.map_analysis = analysis['MapData']
        self.map_sort_update()

        ### Difficulty stats & region stats
        if hasattr(self, 'stats_difficulty_UI_dict'):
            for item in set(self.stats_difficulty_UI_dict.keys()):
                self.stats_difficulty_UI_dict[item].deleteLater()
                del self.stats_difficulty_UI_dict[item]
        else:
            self.stats_difficulty_UI_dict = dict()

        difficulties = ['Casual', 'Normal', 'Hard', 'Brutal', 'B+1', 'B+2', 'B+3', 'B+4', 'B+5', 'B+6']
        idx = 0
        AllDiff = {'Victory': 0, 'Defeat': 0}
        for difficulty in difficulties:
            if difficulty in analysis['DifficultyData']:
                line = True if idx + 1 == len(analysis['DifficultyData']) else False
                self.stats_difficulty_UI_dict[difficulty] = MUI.DifficultyEntry(difficulty.replace('B+', 'Brutal+'),
                                                                                analysis['DifficultyData'][difficulty]['Victory'],
                                                                                analysis['DifficultyData'][difficulty]['Defeat'],
                                                                                f"{100*analysis['DifficultyData'][difficulty]['Winrate']:.0f}%",
                                                                                50,
                                                                                idx * 18 + 20,
                                                                                bg=idx % 2,
                                                                                parent=self.TAB_DifficultyRegions,
                                                                                line=line)
                idx += 1
                AllDiff['Victory'] += analysis['DifficultyData'][difficulty]['Victory']
                AllDiff['Defeat'] += analysis['DifficultyData'][difficulty]['Defeat']

        AllDiff['Winrate'] = f"{100*AllDiff['Victory']/(AllDiff['Victory'] + AllDiff['Defeat']):.0f}%" if (AllDiff['Victory'] +
                                                                                                           AllDiff['Defeat']) > 0 else '-'

        self.stats_difficulty_UI_dict['All'] = MUI.DifficultyEntry('Σ',
                                                                   AllDiff['Victory'],
                                                                   AllDiff['Defeat'],
                                                                   AllDiff['Winrate'],
                                                                   50,
                                                                   idx * 18 + 23,
                                                                   parent=self.TAB_DifficultyRegions)

        # Region stats
        for item in set(self.stats_region_UI_dict.keys()):
            self.stats_region_UI_dict[item].deleteLater()
            del self.stats_region_UI_dict[item]

        for idx, region in enumerate(analysis['RegionData']):
            self.stats_region_UI_dict[region] = MUI.RegionStats(region,
                                                                analysis['RegionData'][region],
                                                                20 + idx * 18,
                                                                bg=True if idx % 2 else False,
                                                                parent=self.TAB_DifficultyRegions)

        ### Commander stats
        self.my_commander_analysis = analysis['CommanderData']
        self.my_commander_sort_update()

        ### Ally commander stats
        self.ally_commander_analysis = analysis['AllyCommanderData']
        self.ally_commander_sort_update()

        ### Unit stats
        if self.p.CAnalysis.full_analysis_finished:
            self.update_unit_stats(analysis['UnitData'])

    def update_unit_stats(self, unit_data):
        """ Update unit stats """

        # Create tab if it's not there yey
        if not hasattr(self, 'TAB_CommUnitStats'):
            self.TAB_CommUnitStats = QtWidgets.QWidget()
            self.TABW_StatResults.insertTab(4, self.TAB_CommUnitStats, "Unit stats")

        # Update commander units widget
        if not hasattr(self, 'WD_unit_stats'):
            self.WD_unit_stats = MUI.UnitStats(unit_data, parent=self.TAB_CommUnitStats)
        else:
            self.WD_unit_stats.unit_data = unit_data
            self.WD_unit_stats.update_units()

        # Amon unit tab
        if not hasattr(self, 'TAB_AmonUnitStats'):
            self.TAB_AmonUnitStats = QtWidgets.QWidget()
            self.TABW_StatResults.insertTab(5, self.TAB_AmonUnitStats, "Amon stats")

        # Update amon units widget
        if not hasattr(self, 'WD_amon_unit_stats'):
            self.WD_amon_unit_stats = MUI.AmonUnitStats(unit_data['amon'], parent=self.TAB_AmonUnitStats)
        else:
            self.WD_amon_unit_stats.update_data(unit_data['amon'])

    def switched_tab(self, idx):
        """ Updating bg depends whether a unit is visible, this break when switched to another tab.
        This function updates background for Amon's units when you switch to the tab"""
        self.update_results_layout()
        if idx == 5:
            self.WD_amon_unit_stats.update_backgrounds()

    def map_sort_update(self, caller=None):
        # Delete buttons if not required
        for item in set(self.stats_maps_UI_dict):
            self.stats_maps_UI_dict[item].deleteLater()
            del self.stats_maps_UI_dict[item]

        # Sort maps
        trans_dict = {'Freq': 'frequency', 'Wins': 'Victory', 'Losses': 'Defeat', 'Win%': 'winrate', 'Avg': 'average_victory_time', 'Bonus': 'bonus'}

        if type(caller) is MUI.SortingQLabel:
            caller.activate()

        sort_by = MUI.SortingQLabel.active[self.GB_MapsOverview].value
        reverse = MUI.SortingQLabel.active[self.GB_MapsOverview].reverse

        if sort_by == 'Map name':
            self.map_analysis = {k: v for k, v in sorted(self.map_analysis.items(), reverse=reverse)}
        elif sort_by == 'Fastest':
            self.map_analysis = {k: v for k, v in sorted(self.map_analysis.items(), key=lambda x: x[1]['Fastest']['length'], reverse=reverse)}
        else:
            self.map_analysis = {k: v for k, v in sorted(self.map_analysis.items(), key=lambda x: x[1][trans_dict[sort_by]], reverse=reverse)}

        # Add map buttons & update the fastest map
        idx = 0
        for m in self.map_analysis:
            idx += 1
            self.stats_maps_UI_dict[m] = MUI.MapEntry(self.GB_MapsOverview,
                                                      idx * 25,
                                                      m,
                                                      self.map_analysis[m]['Fastest']['length'],
                                                      self.map_analysis[m]['average_victory_time'],
                                                      self.map_analysis[m]['Victory'],
                                                      self.map_analysis[m]['Defeat'],
                                                      self.map_analysis[m]['frequency'],
                                                      self.map_analysis[m]['bonus'],
                                                      bg=idx % 2 == 0)

            self.stats_maps_UI_dict[m].bt_button.clicked.connect(partial(self.map_link_update, mapname=m, fdict=self.map_analysis[m]['Fastest']))

        # Try to show the last visible fastest map if it's there
        if hasattr(self, 'last_fastest_map') and self.last_fastest_map in self.map_analysis:
            self.map_link_update(self.last_fastest_map, self.map_analysis[self.last_fastest_map]['Fastest'])

        elif len(self.map_analysis) > 0:
            for m in self.map_analysis:
                self.map_link_update(m, self.map_analysis[m]['Fastest'])
                break

        # Show/hide the fastest map accordingly
        if len(self.map_analysis) == 0:
            self.QB_FastestMap.hide()
        else:
            self.QB_FastestMap.show()

    def my_commander_sort_update(self, caller=None):
        """ Creates and updates widgets for my commander stats """
        translate = {'APM': 'MedianAPM', 'Win%': 'Winrate', 'Losses': 'Defeat', 'Wins': 'Victory', 'Freq': 'Frequency', 'Kills': 'KillFraction'}

        if type(caller) is MUI.SortingQLabel:
            caller.activate()

        sort_by = MUI.SortingQLabel.active[self.TAB_MyCommanders].value
        reverse = MUI.SortingQLabel.active[self.TAB_MyCommanders].reverse

        if sort_by == 'Commander':
            self.my_commander_analysis = {k: v for k, v in sorted(self.my_commander_analysis.items(), reverse=reverse)}
        else:
            self.my_commander_analysis = {
                k: v
                for k, v in sorted(self.my_commander_analysis.items(), key=lambda x: x[1][translate[sort_by]], reverse=reverse)
            }

        for item in set(self.stats_mycommander_UI_dict.keys()):
            self.stats_mycommander_UI_dict[item].deleteLater()
            del self.stats_mycommander_UI_dict[item]

        idx = 0
        spacing = 21
        firstCommander = None
        for co in self.my_commander_analysis:
            if co == 'any':
                continue
            if firstCommander is None:
                firstCommander = co
            self.stats_mycommander_UI_dict[co] = MUI.CommanderEntry(co,
                                                                    f"{100*self.my_commander_analysis[co]['Frequency']:.1f}%",
                                                                    self.my_commander_analysis[co]['Victory'],
                                                                    self.my_commander_analysis[co]['Defeat'],
                                                                    f"{100*self.my_commander_analysis[co]['Winrate']:.0f}%",
                                                                    f"{self.my_commander_analysis[co]['MedianAPM']:.0f}",
                                                                    f"{100*self.my_commander_analysis[co].get('KillFraction',0):.0f}%",
                                                                    idx * spacing + 23,
                                                                    parent=self.TAB_MyCommanders,
                                                                    bg=True if idx % 2 == 1 else False)

            self.stats_mycommander_UI_dict[co].bt_button.clicked.connect(partial(self.detailed_my_commander_stats_update, co))
            idx += 1

        self.stats_mycommander_UI_dict['any'] = MUI.CommanderEntry('Σ',
                                                                   f"{100*self.my_commander_analysis['any']['Frequency']:.0f}%",
                                                                   self.my_commander_analysis['any']['Victory'],
                                                                   self.my_commander_analysis['any']['Defeat'],
                                                                   f"{100*self.my_commander_analysis['any']['Winrate']:.0f}%",
                                                                   f"{self.my_commander_analysis['any']['MedianAPM']:.0f}",
                                                                   f"{100*self.my_commander_analysis['any'].get('KillFraction',0):.0f}%",
                                                                   idx * spacing + 23,
                                                                   parent=self.TAB_MyCommanders,
                                                                   button=False)

        # Update details
        if hasattr(self, 'my_detailed_info') and self.my_detailed_info is not None:
            self.my_detailed_info.deleteLater()
            self.my_detailed_info = None

        if hasattr(self, 'my_commander_clicked') and self.my_commander_clicked in self.my_commander_analysis:
            self.my_detailed_info = MUI.CommanderStats(self.my_commander_clicked, self.my_commander_analysis, parent=self.TAB_MyCommanders)
        elif len(self.my_commander_analysis) > 1:
            self.my_detailed_info = MUI.CommanderStats(firstCommander, self.my_commander_analysis, parent=self.TAB_MyCommanders)

    def detailed_my_commander_stats_update(self, commander):
        """ Updates my commander details"""
        self.my_commander_clicked = commander
        if hasattr(self, 'my_detailed_info') and self.my_detailed_info is not None:
            self.my_detailed_info.deleteLater()
            self.my_detailed_info = None
        self.my_detailed_info = MUI.CommanderStats(commander, self.my_commander_analysis, parent=self.TAB_MyCommanders)

    def ally_commander_sort_update(self, caller=None):
        """ Creates and updates widgets for allu commander stats """
        translate = {'APM': 'MedianAPM', 'Win%': 'Winrate', 'Losses': 'Defeat', 'Wins': 'Victory', 'Freq': 'Frequency', 'Kills': 'KillFraction'}

        if type(caller) is MUI.SortingQLabel:
            caller.activate()

        sort_by = MUI.SortingQLabel.active[self.TAB_AlliedCommanders].value
        reverse = MUI.SortingQLabel.active[self.TAB_AlliedCommanders].reverse

        if sort_by == 'Allied commander':
            self.ally_commander_analysis = {k: v for k, v in sorted(self.ally_commander_analysis.items(), reverse=reverse)}
        else:
            self.ally_commander_analysis = {
                k: v
                for k, v in sorted(self.ally_commander_analysis.items(), key=lambda x: x[1][translate[sort_by]], reverse=reverse)
            }

        for item in set(self.stats_allycommander_UI_dict.keys()):
            self.stats_allycommander_UI_dict[item].deleteLater()
            del self.stats_allycommander_UI_dict[item]

        idx = 0
        spacing = 21
        firstCommander = None
        for co in self.ally_commander_analysis:
            if co == 'any':
                continue
            if firstCommander is None:
                firstCommander = co
            self.stats_allycommander_UI_dict[co] = MUI.CommanderEntry(co,
                                                                      f"{100*self.ally_commander_analysis[co]['Frequency']:.1f}%",
                                                                      self.ally_commander_analysis[co]['Victory'],
                                                                      self.ally_commander_analysis[co]['Defeat'],
                                                                      f"{100*self.ally_commander_analysis[co]['Winrate']:.0f}%",
                                                                      f"{self.ally_commander_analysis[co]['MedianAPM']:.0f}",
                                                                      f"{100*self.ally_commander_analysis[co].get('KillFraction',0):.0f}%",
                                                                      idx * spacing + 23,
                                                                      parent=self.TAB_AlliedCommanders,
                                                                      bg=True if idx % 2 == 1 else False)

            self.stats_allycommander_UI_dict[co].bt_button.clicked.connect(partial(self.detailed_ally_commander_stats_update, co))
            idx += 1

        self.stats_allycommander_UI_dict['any'] = MUI.CommanderEntry('Σ',
                                                                     f"{100*self.ally_commander_analysis['any']['Frequency']:.0f}%",
                                                                     self.ally_commander_analysis['any']['Victory'],
                                                                     self.ally_commander_analysis['any']['Defeat'],
                                                                     f"{100*self.ally_commander_analysis['any']['Winrate']:.0f}%",
                                                                     f"{self.ally_commander_analysis['any']['MedianAPM']:.0f}",
                                                                     f"{100*self.ally_commander_analysis['any'].get('KillFraction',0):.0f}%",
                                                                     idx * spacing + 23,
                                                                     parent=self.TAB_AlliedCommanders,
                                                                     button=False)

        # Update details
        if hasattr(self, 'ally_detailed_info') and self.ally_detailed_info is not None:
            self.ally_detailed_info.deleteLater()
            self.ally_detailed_info = None

        if hasattr(self, 'ally_commander_clicked') and self.ally_commander_clicked in self.ally_commander_analysis:
            self.ally_detailed_info = MUI.CommanderStats(self.ally_commander_clicked, self.ally_commander_analysis, parent=self.TAB_AlliedCommanders)
        elif len(self.ally_commander_analysis) > 1:
            self.ally_detailed_info = MUI.CommanderStats(firstCommander, self.ally_commander_analysis, parent=self.TAB_AlliedCommanders)

    def detailed_ally_commander_stats_update(self, commander):
        """ Updates allied commander details"""
        self.ally_commander_clicked = commander
        if hasattr(self, 'ally_detailed_info') and self.ally_detailed_info is not None:
            self.ally_detailed_info.deleteLater()
            self.ally_detailed_info = None
        self.ally_detailed_info = MUI.CommanderStats(commander, self.ally_commander_analysis, parent=self.TAB_AlliedCommanders)

    def map_link_update(self, mapname=None, fdict=None):
        """ Updates the fastest map to clicked map """
        if len(fdict) <= 1:
            self.QB_FastestMap.hide()
        else:
            self.QB_FastestMap.update_data(mapname, fdict, self.p.CAnalysis.main_handles)
            self.last_fastest_map = mapname
