"""
Shared layout helpers for the overlay settings tabs (Mission Overlay, Build
Order). Widgets created here use feature-neutral `Overlay*` object names that
are styled in `MTheming.overlay_tab_stylesheet()`.
"""
from PyQt5 import QtCore, QtWidgets


def hint_label(text):
    label = QtWidgets.QLabel(text)
    label.setWordWrap(True)
    label.setObjectName('OverlayHintLabel')
    return label


def subsection_label(text):
    label = QtWidgets.QLabel(text)
    label.setObjectName('OverlaySubsectionLabel')
    return label


def section_title(text, subtitle=None):
    block = QtWidgets.QVBoxLayout()
    block.setSpacing(2)
    block.setContentsMargins(0, 0, 0, 0)

    title = QtWidgets.QLabel(text)
    title.setObjectName('OverlaySectionTitle')
    block.addWidget(title)

    if subtitle:
        block.addWidget(hint_label(subtitle))
    return block


def section_card():
    card = QtWidgets.QFrame()
    card.setObjectName('OverlaySectionCard')
    card.setAutoFillBackground(True)
    card.setFrameShape(QtWidgets.QFrame.StyledPanel)
    card.setFrameShadow(QtWidgets.QFrame.Plain)
    layout = QtWidgets.QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 16)
    layout.setSpacing(10)
    return card, layout


def labeled_field(label_text, widget, tooltip=None):
    row = QtWidgets.QHBoxLayout()
    row.setSpacing(10)
    label = QtWidgets.QLabel(label_text)
    label.setObjectName('OverlayFieldLabel')
    label.setMinimumWidth(132)
    label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    if tooltip:
        label.setToolTip(tooltip)
        widget.setToolTip(tooltip)
    row.addWidget(label)
    row.addWidget(widget, 1)
    return row


def value_with_unit(widget, unit):
    row = QtWidgets.QHBoxLayout()
    row.setSpacing(6)
    row.setContentsMargins(0, 0, 0, 0)
    row.addWidget(widget)
    unit_label = QtWidgets.QLabel(unit)
    unit_label.setObjectName('OverlayUnitLabel')
    row.addWidget(unit_label)
    row.addStretch()
    wrapper = QtWidgets.QWidget()
    wrapper.setLayout(row)
    return wrapper, widget


def vh_spinbox(min_val, max_val, step, decimals=2, tooltip=None):
    spin = QtWidgets.QDoubleSpinBox()
    spin.setRange(min_val, max_val)
    spin.setSingleStep(step)
    spin.setDecimals(decimals)
    spin.setFixedWidth(88)
    if tooltip:
        spin.setToolTip(tooltip)
    return value_with_unit(spin, 'vh')
