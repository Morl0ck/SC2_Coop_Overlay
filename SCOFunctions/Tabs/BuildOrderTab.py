import webbrowser

from PyQt5 import QtCore, QtWidgets

from SCOFunctions.BuildOrderStore import commander_names
from SCOFunctions.CommanderOCR import commander_display_name
from SCOFunctions.SC2Dictionaries.BuildOrders import build_orders_defaults
from SCOFunctions.Tabs import OverlayTabShared


class BuildOrderTab(QtWidgets.QWidget):
    # Shared layout helpers (also used by MissionTab)
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
        self.tab_editor = QtWidgets.QWidget()
        self.sub_tabs.addTab(self.tab_settings, 'Appearance')
        self.sub_tabs.addTab(self.tab_editor, 'Build Orders')
        self.sub_tabs.setObjectName('OverlaySubTabs')

        self._build_settings_tab()
        self._build_editor_tab()

    def _build_settings_tab(self):
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        page = QtWidgets.QWidget()
        page_layout = QtWidgets.QVBoxLayout(page)
        page_layout.setContentsMargins(20, 14, 20, 14)
        page_layout.setSpacing(16)

        outer = QtWidgets.QVBoxLayout(self.tab_settings)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        scroll.setWidget(page)

        header = QtWidgets.QVBoxLayout()
        header.setSpacing(4)
        self.la_description = QtWidgets.QLabel('Build order overlay')
        self.la_description.setObjectName('OverlayPageTitle')
        header.addWidget(self.la_description)
        header.addWidget(self._hint_label(
            'Shows your commander build order on the left during the first few minutes of a game. '
            'Commander is auto-detected from the co-op lobby selection screen (a second after you click), '
            'with a default fallback. Turn the feature on from the main Settings tab.'))
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
        self.CB_AnchorV = QtWidgets.QComboBox()
        self.CB_AnchorV.addItems(['Top', 'Bottom'])
        anchor_row.addLayout(self._labeled_field('Horizontal', self.CB_AnchorH), 1)
        anchor_row.addLayout(self._labeled_field('Vertical', self.CB_AnchorV), 1)
        placement_layout.addLayout(anchor_row)

        self.SP_OffsetX = QtWidgets.QDoubleSpinBox()
        self.SP_OffsetX.setRange(0, 100)
        self.SP_OffsetX.setSingleStep(0.5)
        self.SP_OffsetX.setDecimals(2)
        self.SP_OffsetX.setFixedWidth(88)
        offset_x_wrap, self.SP_OffsetX = self._value_with_unit(self.SP_OffsetX, 'vh')
        placement_layout.addLayout(self._labeled_field('Horizontal offset', offset_x_wrap))

        self.SP_OffsetY = QtWidgets.QDoubleSpinBox()
        self.SP_OffsetY.setRange(0, 100)
        self.SP_OffsetY.setSingleStep(0.5)
        self.SP_OffsetY.setDecimals(2)
        self.SP_OffsetY.setFixedWidth(88)
        offset_y_wrap, self.SP_OffsetY = self._value_with_unit(self.SP_OffsetY, 'vh')
        placement_layout.addLayout(self._labeled_field('Vertical offset', offset_y_wrap))

        fullwidth_block = QtWidgets.QVBoxLayout()
        fullwidth_block.setSpacing(4)
        self.CH_FullWidth = QtWidgets.QCheckBox('Use full-width overlay window')
        self.CH_FullWidth.setToolTip(
            'Make the overlay window span the entire monitor width.\n'
            'Required for left-side placement of the build order panel.')
        fullwidth_block.addWidget(self.CH_FullWidth)
        fullwidth_block.addWidget(self._hint_label(
            'Needed for left-edge placement. Turn off if the overlay shows a black screen.'))
        placement_layout.addLayout(fullwidth_block)
        placement_layout.addStretch()

        display, display_layout = self._section_card()
        display_layout.addLayout(self._section_title(
            'Display',
            'Opacity, panel size, and how long the build order stays visible.'))

        self.SP_Opacity = QtWidgets.QDoubleSpinBox()
        self.SP_Opacity.setRange(0.1, 1.0)
        self.SP_Opacity.setSingleStep(0.05)
        self.SP_Opacity.setDecimals(2)
        self.SP_Opacity.setFixedWidth(88)
        display_layout.addLayout(self._labeled_field('Overall opacity', self.SP_Opacity))

        self.SP_BackgroundOpacity = QtWidgets.QDoubleSpinBox()
        self.SP_BackgroundOpacity.setRange(0.0, 1.0)
        self.SP_BackgroundOpacity.setSingleStep(0.05)
        self.SP_BackgroundOpacity.setDecimals(2)
        self.SP_BackgroundOpacity.setFixedWidth(88)
        display_layout.addLayout(self._labeled_field('Background opacity', self.SP_BackgroundOpacity))

        panel_width_wrap, self.SP_PanelWidth = self._vh_spinbox(12, 80, 1.0, decimals=1)
        display_layout.addLayout(self._labeled_field('Panel width', panel_width_wrap))

        self.SP_DisplayMinutes = QtWidgets.QDoubleSpinBox()
        self.SP_DisplayMinutes.setRange(1.0, 15.0)
        self.SP_DisplayMinutes.setSingleStep(0.5)
        self.SP_DisplayMinutes.setDecimals(1)
        self.SP_DisplayMinutes.setFixedWidth(88)
        self.SP_DisplayMinutes.setToolTip('Hide the build order panel after this many in-game minutes.')
        display_minutes_wrap, self.SP_DisplayMinutes = self._value_with_unit(self.SP_DisplayMinutes, 'min')
        display_layout.addLayout(self._labeled_field(
            'Display duration', display_minutes_wrap, self.SP_DisplayMinutes.toolTip()))

        self.SP_MaxSteps = QtWidgets.QSpinBox()
        self.SP_MaxSteps.setRange(0, 50)
        self.SP_MaxSteps.setFixedWidth(88)
        self.SP_MaxSteps.setToolTip('Maximum steps to show (0 = show all).')
        display_layout.addLayout(self._labeled_field('Max steps', self.SP_MaxSteps))

        display_layout.addWidget(self._subsection_label('Typography'))
        font_title_wrap, self.SP_FontTitle = self._vh_spinbox(0.5, 6.0, 0.05)
        display_layout.addLayout(self._labeled_field('Commander title', font_title_wrap))
        font_step_wrap, self.SP_FontStep = self._vh_spinbox(0.5, 6.0, 0.05)
        display_layout.addLayout(self._labeled_field('Step text', font_step_wrap))
        display_layout.addStretch()

        columns.addWidget(placement, 1, QtCore.Qt.AlignTop)
        columns.addWidget(display, 1, QtCore.Qt.AlignTop)
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
            'Commander detection',
            'OCR reads the co-op lobby a second after you click (commander, prestige, difficulty). '
            'Tesseract OCR must be installed separately. If detection fails, the default commander is used.'))

        detect_row = QtWidgets.QHBoxLayout()
        detect_row.setSpacing(12)
        self.CH_OcrEnabled = QtWidgets.QCheckBox('Enable lobby OCR auto-detect')
        detect_row.addWidget(self.CH_OcrEnabled)

        self.CB_DefaultCommander = QtWidgets.QComboBox()
        for name in commander_names():
            self.CB_DefaultCommander.addItem(commander_display_name(name), name)
        detect_row.addLayout(self._labeled_field('Default commander', self.CB_DefaultCommander), 1)
        footer_layout.addLayout(detect_row)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(8)
        self.BT_TestOcr = QtWidgets.QPushButton('Test detection')
        self.BT_TestOcr.setObjectName('OverlaySecondaryButton')
        self.BT_TestOcr.setToolTip('Open the co-op lobby (commander selection) screen, then click this to test detection.')
        self.BT_TestOcr.clicked.connect(self.p.test_build_order_ocr)
        self.LA_OcrResult = QtWidgets.QLabel('')
        self.LA_OcrResult.setObjectName('OverlayHintLabel')
        button_row.addWidget(self.BT_TestOcr)
        button_row.addWidget(self.LA_OcrResult, 1)
        footer_layout.addLayout(button_row)

        action_row = QtWidgets.QHBoxLayout()
        action_row.setSpacing(8)
        self.BT_Apply = QtWidgets.QPushButton('Apply')
        self.BT_Apply.setObjectName('OverlayPrimaryButton')
        self.BT_Apply.setMinimumWidth(88)
        self.BT_Apply.clicked.connect(self.p.saveSettings)
        self.CH_Preview = QtWidgets.QPushButton('Preview overlay')
        self.CH_Preview.setObjectName('OverlaySecondaryButton')
        self.CH_Preview.setCheckable(True)
        self.CH_Preview.setMinimumWidth(120)
        self.CH_Preview.setToolTip('Show a sample build order panel on the overlay.')
        self.CH_Preview.toggled.connect(self.p.toggle_build_order_preview)
        action_row.addWidget(self.BT_Apply)
        action_row.addWidget(self.CH_Preview)
        action_row.addStretch()
        footer_layout.addLayout(action_row)

        page_layout.addWidget(footer)

        self.la_attribution = self._hint_label(
            'Default build orders from '
            '<a href="https://starcraft2coop.com/commanders/">starcraft2coop.com</a> '
            '(CC-BY-NC-SA-4.0, Aommaster)')
        self.la_attribution.setOpenExternalLinks(False)
        self.la_attribution.linkActivated.connect(lambda: webbrowser.open('https://starcraft2coop.com/commanders/'))
        page_layout.addWidget(self.la_attribution)

    def _build_editor_tab(self):
        page_layout = QtWidgets.QVBoxLayout(self.tab_editor)
        page_layout.setContentsMargins(20, 14, 20, 14)
        page_layout.setSpacing(12)

        page_layout.addLayout(self._section_title(
            'Custom build orders',
            'Choose a commander, edit your build order, and toggle whether to use your custom list instead of the bundled default.'))

        selector_row = QtWidgets.QHBoxLayout()
        selector_row.setSpacing(10)
        self.CB_Commander = QtWidgets.QComboBox()
        for name in commander_names():
            self.CB_Commander.addItem(commander_display_name(name), name)
        self.CB_Commander.currentIndexChanged.connect(self.p.load_build_order_editor)
        selector_row.addLayout(self._labeled_field('Commander', self.CB_Commander), 1)
        page_layout.addLayout(selector_row)

        self.CH_UseCustom = QtWidgets.QCheckBox('Use custom build order for this commander')
        page_layout.addWidget(self.CH_UseCustom)

        page_layout.addWidget(self._subsection_label('Bundled default (read-only)'))
        self.TE_Default = QtWidgets.QPlainTextEdit()
        self.TE_Default.setReadOnly(True)
        self.TE_Default.setMaximumHeight(140)
        page_layout.addWidget(self.TE_Default)

        page_layout.addWidget(self._subsection_label('Your custom build order (one step per line)'))
        self.TE_Custom = QtWidgets.QPlainTextEdit()
        self.TE_Custom.setPlaceholderText('14 Supply Depot\n16 Barracks\n...')
        page_layout.addWidget(self.TE_Custom, 1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(8)
        self.BT_SaveBuildOrder = QtWidgets.QPushButton('Save build order')
        self.BT_SaveBuildOrder.setObjectName('OverlayPrimaryButton')
        self.BT_SaveBuildOrder.clicked.connect(self.p.save_build_order_editor)
        self.BT_ResetCustom = QtWidgets.QPushButton('Clear custom')
        self.BT_ResetCustom.setObjectName('OverlaySecondaryButton')
        self.BT_ResetCustom.clicked.connect(self.p.reset_build_order_custom)
        buttons.addWidget(self.BT_SaveBuildOrder)
        buttons.addWidget(self.BT_ResetCustom)
        buttons.addStretch()
        page_layout.addLayout(buttons)

    def set_default_steps(self, commander: str) -> None:
        default = build_orders_defaults.get(commander, {})
        steps = default.get('steps', [])
        self.TE_Default.setPlainText('\n'.join(steps))

    def get_custom_text(self) -> str:
        return self.TE_Custom.toPlainText().strip()

    def set_custom_text(self, text: str) -> None:
        self.TE_Custom.setPlainText(text or '')

    def current_commander(self) -> str:
        return self.CB_Commander.currentData() or self.CB_Commander.currentText()
