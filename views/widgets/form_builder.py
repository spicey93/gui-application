"""Form field builder utilities for creating consistent form layouts."""
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QComboBox, QDateEdit,
    QDoubleSpinBox, QSpinBox, QTextEdit, QCheckBox, QWidget
)
from PySide6.QtCore import Qt, QDate
from typing import Optional, List, Union, Callable


class FormFieldBuilder:
    """Helper class for creating consistent form fields with labels."""
    
    # Standard label width for consistency
    DEFAULT_LABEL_WIDTH = 150
    
    # Standard font sizes
    FONT_SIZE_SMALL = "11px"
    FONT_SIZE_MEDIUM = "12px"
    FONT_SIZE_LARGE = "16px"
    
    @staticmethod
    def create_labeled_field(
        label_text: str,
        widget: QWidget,
        label_width: int = DEFAULT_LABEL_WIDTH,
        font_size: str = FONT_SIZE_SMALL,
        label_bold: bool = False,
        stretch_widget: bool = True
    ) -> QHBoxLayout:
        """
        Create a horizontal layout with a label and widget.
        
        Args:
            label_text: Text for the label
            widget: The input widget (QLineEdit, QComboBox, etc.)
            label_width: Minimum width for the label
            font_size: Font size for both label and widget
            label_bold: Whether the label should be bold
            stretch_widget: Whether the widget should stretch to fill space
        
        Returns:
            QHBoxLayout containing the label and widget
        """
        layout = QHBoxLayout()
        
        # Create label
        label = QLabel(label_text)
        label.setMinimumWidth(label_width)
        style = f"font-size: {font_size};"
        if label_bold:
            style += " font-weight: bold;"
        label.setStyleSheet(style)
        layout.addWidget(label)
        
        # Style widget
        widget.setStyleSheet(f"font-size: {font_size};")
        
        # Add widget to layout
        if stretch_widget:
            layout.addWidget(widget, stretch=1)
        else:
            layout.addWidget(widget)
        
        return layout
    
    @staticmethod
    def create_line_edit_field(
        label_text: str,
        initial_value: str = "",
        placeholder: Optional[str] = None,
        label_width: int = DEFAULT_LABEL_WIDTH,
        font_size: str = FONT_SIZE_SMALL,
        label_bold: bool = False
    ) -> tuple:
        """
        Create a labeled QLineEdit field.
        
        Returns:
            Tuple of (layout, line_edit_widget)
        """
        line_edit = QLineEdit(initial_value)
        if placeholder:
            line_edit.setPlaceholderText(placeholder)
        
        layout = FormFieldBuilder.create_labeled_field(
            label_text, line_edit, label_width, font_size, label_bold
        )
        
        return layout, line_edit
    
    @staticmethod
    def create_combo_field(
        label_text: str,
        items: Optional[List[str]] = None,
        editable: bool = False,
        current_value: Optional[str] = None,
        label_width: int = DEFAULT_LABEL_WIDTH,
        font_size: str = FONT_SIZE_SMALL,
        label_bold: bool = False
    ) -> tuple:
        """
        Create a labeled QComboBox field.
        
        Returns:
            Tuple of (layout, combo_box_widget)
        """
        combo = QComboBox()
        combo.setEditable(editable)
        
        if items:
            combo.addItems(items)
        
        if current_value:
            index = combo.findText(current_value)
            if index >= 0:
                combo.setCurrentIndex(index)
            elif editable:
                combo.setCurrentText(current_value)
        
        layout = FormFieldBuilder.create_labeled_field(
            label_text, combo, label_width, font_size, label_bold
        )
        
        return layout, combo
    
    @staticmethod
    def create_date_field(
        label_text: str,
        initial_date: Optional[QDate] = None,
        calendar_popup: bool = True,
        label_width: int = DEFAULT_LABEL_WIDTH,
        font_size: str = FONT_SIZE_SMALL,
        label_bold: bool = False
    ) -> tuple:
        """
        Create a labeled QDateEdit field.
        
        Returns:
            Tuple of (layout, date_edit_widget)
        """
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(calendar_popup)
        if initial_date:
            date_edit.setDate(initial_date)
        else:
            date_edit.setDate(QDate.currentDate())
        
        layout = FormFieldBuilder.create_labeled_field(
            label_text, date_edit, label_width, font_size, label_bold
        )
        
        return layout, date_edit
    
    @staticmethod
    def create_spinbox_field(
        label_text: str,
        value_type: str = "double",
        initial_value: float = 0.0,
        min_value: float = -999999999.99,
        max_value: float = 999999999.99,
        decimals: int = 2,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        label_width: int = DEFAULT_LABEL_WIDTH,
        font_size: str = FONT_SIZE_SMALL,
        label_bold: bool = False
    ) -> tuple:
        """
        Create a labeled QDoubleSpinBox or QSpinBox field.
        
        Args:
            value_type: "double" or "int"
        
        Returns:
            Tuple of (layout, spinbox_widget)
        """
        if value_type == "double":
            spinbox = QDoubleSpinBox()
            spinbox.setDecimals(decimals)
        else:
            spinbox = QSpinBox()
        
        spinbox.setRange(min_value, max_value)
        spinbox.setValue(initial_value)
        
        if prefix:
            spinbox.setPrefix(prefix)
        if suffix:
            spinbox.setSuffix(suffix)
        
        layout = FormFieldBuilder.create_labeled_field(
            label_text, spinbox, label_width, font_size, label_bold
        )
        
        return layout, spinbox
    
    @staticmethod
    def create_checkbox_field(
        label_text: str,
        initial_checked: bool = False,
        font_size: str = FONT_SIZE_SMALL
    ) -> tuple:
        """
        Create a labeled QCheckBox field.
        
        Returns:
            Tuple of (layout, checkbox_widget)
        """
        checkbox = QCheckBox(label_text)
        checkbox.setChecked(initial_checked)
        checkbox.setStyleSheet(f"font-size: {font_size};")
        
        layout = QHBoxLayout()
        layout.addWidget(checkbox)
        layout.addStretch()
        
        return layout, checkbox
    
    @staticmethod
    def create_readonly_field(
        label_text: str,
        value: str,
        label_width: int = DEFAULT_LABEL_WIDTH,
        font_size: str = FONT_SIZE_SMALL,
        label_bold: bool = False
    ) -> QHBoxLayout:
        """
        Create a read-only labeled field (just label + value label).
        
        Returns:
            QHBoxLayout containing the label and value
        """
        layout = QHBoxLayout()
        
        # Create label
        label = QLabel(label_text)
        label.setMinimumWidth(label_width)
        style = f"font-size: {font_size};"
        if label_bold:
            style += " font-weight: bold;"
        label.setStyleSheet(style)
        layout.addWidget(label)
        
        # Create value label
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: {font_size};")
        layout.addWidget(value_label)
        layout.addStretch()
        
        return layout
