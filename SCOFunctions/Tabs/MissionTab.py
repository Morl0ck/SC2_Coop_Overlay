import webbrowser

from PyQt5 import QtCore, QtWidgets


class MissionTab(QtWidgets.QWidget):
    COL_KIND = 0
    COL_LABEL = 1
    COL_CASUAL = 2
    COL_NORMAL = 3
    COL_HARD = 4
    COL_BRUTAL = 5
    COL_TECH = 6
    COL_STRENGTH = 7
    COL_SPAWN = 8
    COL_PATTERN = 9

    HEADERS = ['Kind', 'Label', 'Casual', 'Normal', 'Hard', 'Brutal', 'Tech', 'Strength', 'Spawn', 'Pattern']

    def __init__(self, parent):
        super().__init__()
        self.p = parent

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.sub_tabs = QtWidgets.QTabWidget(self)
        layout.addWidget(self.sub_tabs)

        self.tab_settings = QtWidgets.QWidget()
        self.tab_timelines = QtWidgets.QWidget()
        self.sub_tabs.addTab(self.tab_settings, 'Settings')
        self.sub_tabs.addTab(self.tab_timelines, 'Timelines')

        self._build_settings_tab()
        self._build_timelines_tab()

    def _build_settings_tab(self):
        page = self.tab_settings

        self.gb = QtWidgets.QFrame(page)
        self.gb.setAutoFillBackground(True)
        self.gb.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.gb.setFrameShadow(QtWidgets.QFrame.Plain)
        self.gb.setGeometry(QtCore.QRect(10, 10, 560, 360))

        self.la_description = QtWidgets.QLabel(self.gb)
        self.la_description.setGeometry(QtCore.QRect(14, 10, self.gb.width() - 28, 50))
        self.la_description.setAlignment(QtCore.Qt.AlignTop)
        self.la_description.setWordWrap(True)
        self.la_description.setText(
            '<b>Mission timeline overlay</b><br>'
            'Placement and appearance of the live panel. Changes apply immediately. '
            'Enable the feature in the <b>Settings</b> tab.')

        self.CH_FullWidth = QtWidgets.QCheckBox(self.gb)
        self.CH_FullWidth.setGeometry(QtCore.QRect(320, 58, 230, 20))
        self.CH_FullWidth.setText('Full-width overlay')
        self.CH_FullWidth.setToolTip(
            'Make the overlay window span the entire monitor width.\n'
            'Required for left-side placement of the mission panel.')

        self.la_fullwidth = QtWidgets.QLabel(self.gb)
        self.la_fullwidth.setGeometry(QtCore.QRect(320, 78, 230, 40))
        self.la_fullwidth.setWordWrap(True)
        self.la_fullwidth.setText(
            '<span style="color:gray;font-size:11px">Needed for left-edge placement. '
            'Turn off if you see a black screen.</span>')

        col1 = 16
        col2 = 180
        row = 58
        row_h = 28

        self._label('Horizontal anchor', col1, row, self.gb)
        self.CB_AnchorH = QtWidgets.QComboBox(self.gb)
        self.CB_AnchorH.setGeometry(QtCore.QRect(col2, row, 120, 22))
        self.CB_AnchorH.addItems(['Left', 'Right'])

        row += row_h
        self._label('Vertical anchor', col1, row, self.gb)
        self.CB_AnchorV = QtWidgets.QComboBox(self.gb)
        self.CB_AnchorV.setGeometry(QtCore.QRect(col2, row, 120, 22))
        self.CB_AnchorV.addItems(['Top', 'Bottom'])

        row += row_h
        self._label('Horizontal offset (vh)', col1, row, self.gb)
        self.SP_OffsetX = QtWidgets.QDoubleSpinBox(self.gb)
        self.SP_OffsetX.setGeometry(QtCore.QRect(col2, row, 80, 22))
        self.SP_OffsetX.setRange(0, 100)
        self.SP_OffsetX.setSingleStep(0.5)

        row += row_h
        self._label('Vertical offset (vh)', col1, row, self.gb)
        self.SP_OffsetY = QtWidgets.QDoubleSpinBox(self.gb)
        self.SP_OffsetY.setGeometry(QtCore.QRect(col2, row, 80, 22))
        self.SP_OffsetY.setRange(0, 100)
        self.SP_OffsetY.setSingleStep(0.5)

        row += row_h
        self._label('Opacity', col1, row, self.gb)
        self.SP_Opacity = QtWidgets.QDoubleSpinBox(self.gb)
        self.SP_Opacity.setGeometry(QtCore.QRect(col2, row, 80, 22))
        self.SP_Opacity.setRange(0.1, 1.0)
        self.SP_Opacity.setSingleStep(0.05)

        row += row_h
        self.CH_ShowPrevious = QtWidgets.QCheckBox(self.gb)
        self.CH_ShowPrevious.setGeometry(QtCore.QRect(col1, row, 250, 20))
        self.CH_ShowPrevious.setText('Show previous event')

        row += row_h
        self.CH_ShowNext = QtWidgets.QCheckBox(self.gb)
        self.CH_ShowNext.setGeometry(QtCore.QRect(col1, row, 250, 20))
        self.CH_ShowNext.setText('Show next / upcoming events')

        row += row_h
        self._label('Font size: NEXT (vh)', col1, row, self.gb)
        self.SP_FontNext = QtWidgets.QDoubleSpinBox(self.gb)
        self.SP_FontNext.setGeometry(QtCore.QRect(col2, row, 80, 22))
        self.SP_FontNext.setRange(0.5, 6.0)
        self.SP_FontNext.setSingleStep(0.05)

        row += row_h
        self._label('Font size: others (vh)', col1, row, self.gb)
        self.SP_FontOther = QtWidgets.QDoubleSpinBox(self.gb)
        self.SP_FontOther.setGeometry(QtCore.QRect(col2, row, 80, 22))
        self.SP_FontOther.setRange(0.5, 6.0)
        self.SP_FontOther.setSingleStep(0.05)

        row += row_h
        self.BT_Apply = QtWidgets.QPushButton(self.gb)
        self.BT_Apply.setGeometry(QtCore.QRect(col1, row, 70, 26))
        self.BT_Apply.setText('Apply')
        self.BT_Apply.clicked.connect(self.p.saveSettings)

        self.CH_Preview = QtWidgets.QPushButton(self.gb)
        self.CH_Preview.setGeometry(QtCore.QRect(col1 + 80, row, 110, 26))
        self.CH_Preview.setText('Preview overlay')
        self.CH_Preview.setCheckable(True)
        self.CH_Preview.setToolTip('Show a sample mission panel on the overlay to test placement')
        self.CH_Preview.toggled.connect(self.p.toggle_mission_overlay_preview)

        row += row_h + 4
        self.la_attribution = QtWidgets.QLabel(self.gb)
        self.la_attribution.setGeometry(QtCore.QRect(14, row, self.gb.width() - 28, 22))
        self.la_attribution.setText(
            'Brutal timings from <a href="https://starcraft2coop.com/missions/">starcraft2coop.com</a> '
            '(CC-BY-NC-SA-4.0, Aommaster)')
        self.la_attribution.setOpenExternalLinks(False)
        self.la_attribution.linkActivated.connect(lambda: webbrowser.open('https://starcraft2coop.com/missions/'))

    def _build_timelines_tab(self):
        page = self.tab_timelines

        self.gb_editor = QtWidgets.QFrame(page)
        self.gb_editor.setAutoFillBackground(True)
        self.gb_editor.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.gb_editor.setFrameShadow(QtWidgets.QFrame.Plain)
        self.gb_editor.setGeometry(QtCore.QRect(10, 10, 930, 500))

        self.la_editor = QtWidgets.QLabel(self.gb_editor)
        self.la_editor.setGeometry(QtCore.QRect(14, 8, 500, 18))
        self.la_editor.setText('<b>Timeline data editor</b> (live overlay uses Brutal times)')

        self.CB_Mission = QtWidgets.QComboBox(self.gb_editor)
        self.CB_Mission.setGeometry(QtCore.QRect(14, 32, 320, 22))
        self.CB_Mission.setToolTip('Mission to edit')
        self.CB_Mission.currentIndexChanged.connect(self.p.load_mission_timeline_table)

        self.scroll_timeline = QtWidgets.QScrollArea(self.gb_editor)
        self.scroll_timeline.setGeometry(QtCore.QRect(14, 60, 902, 390))
        self.scroll_timeline.setWidgetResizable(True)
        self.scroll_timeline.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_timeline.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.TW_Timeline = QtWidgets.QTableWidget()
        self.TW_Timeline.setColumnCount(len(self.HEADERS))
        self.TW_Timeline.setHorizontalHeaderLabels(self.HEADERS)
        self.TW_Timeline.horizontalHeader().setStretchLastSection(True)
        self.TW_Timeline.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.TW_Timeline.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.scroll_timeline.setWidget(self.TW_Timeline)

        btn_y = 458
        self.BT_Add = QtWidgets.QPushButton(self.gb_editor)
        self.BT_Add.setGeometry(QtCore.QRect(14, btn_y, 90, 26))
        self.BT_Add.setText('Add event')
        self.BT_Add.clicked.connect(self.p.mission_timeline_add_row)

        self.BT_Remove = QtWidgets.QPushButton(self.gb_editor)
        self.BT_Remove.setGeometry(QtCore.QRect(110, btn_y, 100, 26))
        self.BT_Remove.setText('Remove selected')
        self.BT_Remove.clicked.connect(self.p.mission_timeline_remove_rows)

        self.BT_SaveTimelines = QtWidgets.QPushButton(self.gb_editor)
        self.BT_SaveTimelines.setGeometry(QtCore.QRect(220, btn_y, 70, 26))
        self.BT_SaveTimelines.setText('Save')
        self.BT_SaveTimelines.setToolTip('Save timeline edits to MissionTimelines.json')
        self.BT_SaveTimelines.clicked.connect(self.p.save_mission_timeline_table)

        self.BT_ResetMission = QtWidgets.QPushButton(self.gb_editor)
        self.BT_ResetMission.setGeometry(QtCore.QRect(300, btn_y, 100, 26))
        self.BT_ResetMission.setText('Reset mission')
        self.BT_ResetMission.clicked.connect(self.p.reset_mission_timeline_mission)

        self.BT_ResetAll = QtWidgets.QPushButton(self.gb_editor)
        self.BT_ResetAll.setGeometry(QtCore.QRect(410, btn_y, 80, 26))
        self.BT_ResetAll.setText('Reset all')
        self.BT_ResetAll.clicked.connect(self.p.reset_mission_timeline_all)

    def _label(self, text, x, y, parent):
        la = QtWidgets.QLabel(parent)
        la.setGeometry(QtCore.QRect(x, y, 160, 20))
        la.setText(text)
        return la
