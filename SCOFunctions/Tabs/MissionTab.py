import webbrowser

from PyQt5 import QtWidgets

from SCOFunctions.Tabs import OverlayTabShared


class MissionTab(QtWidgets.QWidget):
    COL_LABEL = 0
    COL_TIME = 1
    COL_TECH = 2
    COL_STRENGTH = 3
    COL_SPAWN = 4
    COL_PATTERN = 5

    HEADERS = ['Label', 'Time', 'Tech', 'Strength', 'Spawn', 'Pattern']

    # Shared layout helpers (also used by BuildOrderTab)
    _hint_label = staticmethod(OverlayTabShared.hint_label)
    _subsection_label = staticmethod(OverlayTabShared.subsection_label)
    _section_title = staticmethod(OverlayTabShared.section_title)
    _section_card = staticmethod(OverlayTabShared.section_card)
    _labeled_field = staticmethod(OverlayTabShared.labeled_field)
    _vh_spinbox = staticmethod(OverlayTabShared.vh_spinbox)
    _value_with_unit = staticmethod(OverlayTabShared.value_with_unit)

    def __init__(self, parent):
        super().__init__()
        self.p = parent

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.sub_tabs = QtWidgets.QTabWidget(self)
        layout.addWidget(self.sub_tabs)

        self.tab_settings = QtWidgets.QWidget()
        self.tab_timelines = QtWidgets.QWidget()
        self.sub_tabs.addTab(self.tab_settings, 'Appearance')
        self.sub_tabs.addTab(self.tab_timelines, 'Timelines')
        self.sub_tabs.setObjectName('OverlaySubTabs')

        self._build_settings_tab()
        self._build_timelines_tab()

    def _build_settings_tab(self):
        page_layout = QtWidgets.QVBoxLayout(self.tab_settings)
        page_layout.setContentsMargins(20, 14, 20, 14)
        page_layout.setSpacing(16)

        header = QtWidgets.QVBoxLayout()
        header.setSpacing(4)
        self.la_description = QtWidgets.QLabel('Mission timeline overlay')
        self.la_description.setObjectName('OverlayPageTitle')
        header.addWidget(self.la_description)
        header.addWidget(self._hint_label(
            'Configure where and how the live mission panel appears in-game. '
            'Most changes apply immediately. Turn the feature on from the main Settings tab.'))
        page_layout.addLayout(header)

        columns = QtWidgets.QHBoxLayout()
        columns.setSpacing(14)

        placement, placement_layout = self._section_card()
        placement_layout.addLayout(self._section_title(
            'Placement',
            'Anchor the panel to a screen corner, then fine-tune with offsets.'))

        anchor_row = QtWidgets.QHBoxLayout()
        anchor_row.setSpacing(10)
        self.CB_AnchorH = QtWidgets.QComboBox()
        self.CB_AnchorH.addItems(['Left', 'Right'])
        self.CB_AnchorH.setToolTip('Which horizontal edge the panel hugs.')
        self.CB_AnchorV = QtWidgets.QComboBox()
        self.CB_AnchorV.addItems(['Top', 'Bottom'])
        self.CB_AnchorV.setToolTip('Which vertical edge the panel hugs.')
        anchor_row.addLayout(self._labeled_field('Horizontal', self.CB_AnchorH), 1)
        anchor_row.addLayout(self._labeled_field('Vertical', self.CB_AnchorV), 1)
        placement_layout.addLayout(anchor_row)

        self.SP_OffsetX = QtWidgets.QDoubleSpinBox()
        self.SP_OffsetX.setRange(0, 100)
        self.SP_OffsetX.setSingleStep(0.5)
        self.SP_OffsetX.setDecimals(2)
        self.SP_OffsetX.setFixedWidth(88)
        offset_x_wrap, self.SP_OffsetX = self._value_with_unit(
            self.SP_OffsetX, 'vh')
        self.SP_OffsetX.setToolTip(
            'Distance from the left or right edge. Values are in viewport height (vh), '
            'so they scale with your monitor resolution.')
        placement_layout.addLayout(self._labeled_field(
            'Horizontal offset', offset_x_wrap, self.SP_OffsetX.toolTip()))

        self.SP_OffsetY = QtWidgets.QDoubleSpinBox()
        self.SP_OffsetY.setRange(0, 100)
        self.SP_OffsetY.setSingleStep(0.5)
        self.SP_OffsetY.setDecimals(2)
        self.SP_OffsetY.setFixedWidth(88)
        offset_y_wrap, self.SP_OffsetY = self._value_with_unit(
            self.SP_OffsetY, 'vh')
        self.SP_OffsetY.setToolTip(
            'Distance from the top or bottom edge. Values are in viewport height (vh).')
        placement_layout.addLayout(self._labeled_field(
            'Vertical offset', offset_y_wrap, self.SP_OffsetY.toolTip()))

        fullwidth_block = QtWidgets.QVBoxLayout()
        fullwidth_block.setSpacing(4)
        self.CH_FullWidth = QtWidgets.QCheckBox('Use full-width overlay window')
        self.CH_FullWidth.setToolTip(
            'Make the overlay window span the entire monitor width.\n'
            'Required for left-side placement of the mission panel.')
        fullwidth_block.addWidget(self.CH_FullWidth)
        self.la_fullwidth = self._hint_label(
            'Needed for left-edge placement. Turn off if the overlay shows a black screen.')
        fullwidth_block.addWidget(self.la_fullwidth)
        placement_layout.addLayout(fullwidth_block)

        display, display_layout = self._section_card()
        display_layout.addLayout(self._section_title(
            'Display',
            'Opacity, panel size, and which timeline lines are shown.'))

        self.SP_Opacity = QtWidgets.QDoubleSpinBox()
        self.SP_Opacity.setRange(0.1, 1.0)
        self.SP_Opacity.setSingleStep(0.05)
        self.SP_Opacity.setDecimals(2)
        self.SP_Opacity.setFixedWidth(88)
        self.SP_Opacity.setToolTip('Opacity of the entire mission panel, including text.')
        display_layout.addLayout(self._labeled_field('Overall opacity', self.SP_Opacity))

        self.SP_BackgroundOpacity = QtWidgets.QDoubleSpinBox()
        self.SP_BackgroundOpacity.setRange(0.0, 1.0)
        self.SP_BackgroundOpacity.setSingleStep(0.05)
        self.SP_BackgroundOpacity.setDecimals(2)
        self.SP_BackgroundOpacity.setFixedWidth(88)
        self.SP_BackgroundOpacity.setToolTip('Opacity of the dark background box only.')
        display_layout.addLayout(self._labeled_field('Background opacity', self.SP_BackgroundOpacity))

        panel_width_wrap, self.SP_PanelWidth = self._vh_spinbox(
            12, 80, 1.0, decimals=1,
            tooltip='Width of the mission timeline panel. Increase to reduce line wrapping.')
        display_layout.addLayout(self._labeled_field('Panel width', panel_width_wrap))

        display_layout.addWidget(self._subsection_label('Content shown'))
        visibility = QtWidgets.QVBoxLayout()
        visibility.setSpacing(6)
        visibility.setContentsMargins(12, 0, 0, 0)
        self.CH_ShowPrevious = QtWidgets.QCheckBox('Previous event')
        self.CH_ShowPrevious.setToolTip('Show the most recently passed timeline event.')
        self.CH_ShowUpcoming = QtWidgets.QCheckBox('Upcoming events')
        self.CH_ShowUpcoming.setToolTip('Show the next few events after the current one.')
        visibility.addWidget(self.CH_ShowPrevious)
        visibility.addWidget(self.CH_ShowUpcoming)
        display_layout.addLayout(visibility)

        self.SP_UpcomingCount = QtWidgets.QSpinBox()
        self.SP_UpcomingCount.setRange(1, 3)
        self.SP_UpcomingCount.setFixedWidth(88)
        self.SP_UpcomingCount.setToolTip(
            'How many upcoming events to show, including the NEXT line (1-3).')
        display_layout.addLayout(self._labeled_field(
            'Upcoming count', self.SP_UpcomingCount, self.SP_UpcomingCount.toolTip()))

        display_layout.addWidget(self._subsection_label('Typography'))
        font_next_wrap, self.SP_FontNext = self._vh_spinbox(
            0.5, 6.0, 0.05,
            tooltip='Font size for the highlighted NEXT event line.')
        display_layout.addLayout(self._labeled_field('NEXT line', font_next_wrap))

        font_other_wrap, self.SP_FontOther = self._vh_spinbox(
            0.5, 6.0, 0.05,
            tooltip='Font size for mission name, previous event, and upcoming events.')
        display_layout.addLayout(self._labeled_field('Other text', font_other_wrap))

        columns.addWidget(placement, 1)
        columns.addWidget(display, 1)
        page_layout.addLayout(columns)

        footer = QtWidgets.QFrame()
        footer.setObjectName('OverlayFooterBar')
        footer.setAutoFillBackground(True)
        footer.setFrameShape(QtWidgets.QFrame.StyledPanel)
        footer.setFrameShadow(QtWidgets.QFrame.Plain)
        footer_layout = QtWidgets.QVBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(10)

        footer_layout.addLayout(self._section_title(
            'Timeline data',
            'Attack waves and objectives differ by difficulty. Edit timings on the Timelines tab.'))

        footer_controls = QtWidgets.QHBoxLayout()
        footer_controls.setSpacing(12)

        difficulty_col = QtWidgets.QVBoxLayout()
        difficulty_col.setSpacing(4)
        difficulty_row = QtWidgets.QHBoxLayout()
        difficulty_row.setSpacing(10)
        difficulty_label = QtWidgets.QLabel('Overlay difficulty')
        difficulty_label.setObjectName('OverlayFieldLabel')
        difficulty_label.setMinimumWidth(132)
        self.CB_OverlayDifficulty = QtWidgets.QComboBox()
        self.CB_OverlayDifficulty.addItems(['Auto', 'Casual', 'Normal', 'Hard', 'Brutal'])
        self.CB_OverlayDifficulty.setMinimumWidth(140)
        self.CB_OverlayDifficulty.setToolTip(
            'Which difficulty timings the live overlay uses.\n'
            'Auto reads difficulty from the game when available; otherwise Brutal is used.\n'
            'If timings are missing for the selected difficulty, the next harder set is used.\n'
            'Changes apply immediately during a game.')
        self.CB_OverlayDifficulty.currentIndexChanged.connect(self.p.on_mission_overlay_difficulty_changed)
        difficulty_row.addWidget(difficulty_label)
        difficulty_row.addWidget(self.CB_OverlayDifficulty)
        difficulty_row.addStretch()
        difficulty_col.addLayout(difficulty_row)
        self.la_difficulty_note = self._hint_label(
            'Auto is recommended unless you want to preview a specific difficulty.')
        difficulty_col.addWidget(self.la_difficulty_note)
        footer_controls.addLayout(difficulty_col, 1)

        button_col = QtWidgets.QHBoxLayout()
        button_col.setSpacing(8)
        self.BT_Apply = QtWidgets.QPushButton('Apply')
        self.BT_Apply.setObjectName('OverlayPrimaryButton')
        self.BT_Apply.setMinimumWidth(88)
        self.BT_Apply.clicked.connect(self.p.saveSettings)
        self.CH_Preview = QtWidgets.QPushButton('Preview overlay')
        self.CH_Preview.setObjectName('OverlaySecondaryButton')
        self.CH_Preview.setCheckable(True)
        self.CH_Preview.setMinimumWidth(120)
        self.CH_Preview.setToolTip('Show a sample mission panel on the overlay to test placement.')
        self.CH_Preview.toggled.connect(self.p.toggle_mission_overlay_preview)
        button_col.addWidget(self.BT_Apply)
        button_col.addWidget(self.CH_Preview)
        footer_controls.addLayout(button_col)

        footer_layout.addLayout(footer_controls)
        page_layout.addWidget(footer)

        self.la_attribution = self._hint_label(
            'Default Brutal timings from '
            '<a href="https://starcraft2coop.com/missions/">starcraft2coop.com</a> '
            '(CC-BY-NC-SA-4.0, Aommaster)')
        self.la_attribution.setOpenExternalLinks(False)
        self.la_attribution.linkActivated.connect(lambda: webbrowser.open('https://starcraft2coop.com/missions/'))
        page_layout.addWidget(self.la_attribution)
        page_layout.addStretch()

    def _build_timelines_tab(self):
        page_layout = QtWidgets.QVBoxLayout(self.tab_timelines)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(10)

        self.gb_editor = QtWidgets.QFrame()
        self.gb_editor.setAutoFillBackground(True)
        self.gb_editor.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.gb_editor.setFrameShadow(QtWidgets.QFrame.Plain)
        editor_layout = QtWidgets.QVBoxLayout(self.gb_editor)
        editor_layout.setContentsMargins(14, 12, 14, 12)
        editor_layout.setSpacing(10)

        self.la_editor = QtWidgets.QLabel(
            '<b>Timeline data editor</b> — pick a difficulty, then edit attack waves and objectives separately')
        editor_layout.addWidget(self.la_editor)

        selectors = QtWidgets.QHBoxLayout()
        selectors.setSpacing(10)
        selectors.addWidget(QtWidgets.QLabel('Mission'))
        self.CB_Mission = QtWidgets.QComboBox()
        self.CB_Mission.setToolTip('Mission to edit')
        self.CB_Mission.currentIndexChanged.connect(self.p.load_mission_timeline_table)
        selectors.addWidget(self.CB_Mission, 1)

        selectors.addWidget(QtWidgets.QLabel('Difficulty'))
        self.CB_Difficulty = QtWidgets.QComboBox()
        self.CB_Difficulty.setToolTip('Difficulty to edit')
        self.CB_Difficulty.addItems(['Casual', 'Normal', 'Hard', 'Brutal'])
        self.CB_Difficulty.setCurrentText('Brutal')
        self.CB_Difficulty.currentIndexChanged.connect(self.p.load_mission_timeline_table)
        selectors.addWidget(self.CB_Difficulty)
        editor_layout.addLayout(selectors)

        self.timeline_type_tabs = QtWidgets.QTabWidget()

        self.TW_AttackWaves = self._make_timeline_table()
        self.TW_Objectives = self._make_timeline_table()

        tab_waves = QtWidgets.QWidget()
        waves_layout = QtWidgets.QVBoxLayout(tab_waves)
        waves_layout.setContentsMargins(0, 0, 0, 0)
        scroll_waves = QtWidgets.QScrollArea()
        scroll_waves.setWidgetResizable(True)
        scroll_waves.setWidget(self.TW_AttackWaves)
        waves_layout.addWidget(scroll_waves)

        tab_objectives = QtWidgets.QWidget()
        objectives_layout = QtWidgets.QVBoxLayout(tab_objectives)
        objectives_layout.setContentsMargins(0, 0, 0, 0)
        scroll_objectives = QtWidgets.QScrollArea()
        scroll_objectives.setWidgetResizable(True)
        scroll_objectives.setWidget(self.TW_Objectives)
        objectives_layout.addWidget(scroll_objectives)

        self.timeline_type_tabs.addTab(tab_waves, 'Attack waves')
        self.timeline_type_tabs.addTab(tab_objectives, 'Objectives')
        editor_layout.addWidget(self.timeline_type_tabs, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(8)

        self.BT_Add = QtWidgets.QPushButton('Add row')
        self.BT_Add.clicked.connect(self.p.mission_timeline_add_row)
        buttons.addWidget(self.BT_Add)

        self.BT_Remove = QtWidgets.QPushButton('Remove selected')
        self.BT_Remove.clicked.connect(self.p.mission_timeline_remove_rows)
        buttons.addWidget(self.BT_Remove)

        self.BT_SaveTimelines = QtWidgets.QPushButton('Save')
        self.BT_SaveTimelines.setToolTip('Save timeline edits to MissionTimelines.json')
        self.BT_SaveTimelines.clicked.connect(self.p.save_mission_timeline_table)
        buttons.addWidget(self.BT_SaveTimelines)

        self.BT_ResetMission = QtWidgets.QPushButton('Reset mission')
        self.BT_ResetMission.clicked.connect(self.p.reset_mission_timeline_mission)
        buttons.addWidget(self.BT_ResetMission)

        self.BT_ResetAll = QtWidgets.QPushButton('Reset all')
        self.BT_ResetAll.clicked.connect(self.p.reset_mission_timeline_all)
        buttons.addWidget(self.BT_ResetAll)

        buttons.addStretch()
        editor_layout.addLayout(buttons)
        page_layout.addWidget(self.gb_editor, 1)

    def _make_timeline_table(self):
        tw = QtWidgets.QTableWidget()
        tw.setColumnCount(len(self.HEADERS))
        tw.setHorizontalHeaderLabels(self.HEADERS)
        tw.horizontalHeader().setStretchLastSection(True)
        tw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        return tw
