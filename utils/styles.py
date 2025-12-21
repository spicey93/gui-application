"""Centralized style constants and utilities."""
from pathlib import Path
from typing import Dict, Optional


class AppStyles:
    """Centralized application styles."""
    
    # Font families
    FONT_FAMILY = '"Tahoma", "Arial", sans-serif'
    
    # Font sizes
    FONT_SIZE_TINY = "9px"
    FONT_SIZE_SMALL = "10px"
    FONT_SIZE_NORMAL = "11px"
    FONT_SIZE_MEDIUM = "12px"
    FONT_SIZE_LARGE = "16px"
    FONT_SIZE_XLARGE = "20px"
    FONT_SIZE_XXLARGE = "24px"
    
    # Colors
    COLOR_TEXT = "#000000"
    COLOR_TEXT_GRAY = "#808080"
    COLOR_ERROR = "red"
    COLOR_SUCCESS = "green"
    COLOR_PLACEHOLDER = "gray"
    
    # Spacing
    SPACING_TINY = "5px"
    SPACING_SMALL = "10px"
    SPACING_MEDIUM = "15px"
    SPACING_LARGE = "20px"
    
    # Button sizes
    BUTTON_HEIGHT_SMALL = "30px"
    BUTTON_HEIGHT_MEDIUM = "35px"
    
    @staticmethod
    def label_style(size: str = FONT_SIZE_NORMAL, bold: bool = False, color: str = COLOR_TEXT) -> str:
        """Generate label style string."""
        style = f"font-family: {AppStyles.FONT_FAMILY}; font-size: {size}; color: {color};"
        if bold:
            style += " font-weight: bold;"
        return style
    
    @staticmethod
    def title_style(size: str = FONT_SIZE_XXLARGE) -> str:
        """Generate title style string."""
        return AppStyles.label_style(size, bold=True)
    
    @staticmethod
    def input_style(size: str = FONT_SIZE_NORMAL, padding: str = "3px") -> str:
        """Generate input field style string."""
        return f"font-family: {AppStyles.FONT_FAMILY}; font-size: {size}; padding: {padding};"
    
    @staticmethod
    def status_error_style() -> str:
        """Generate error status label style."""
        return AppStyles.label_style(AppStyles.FONT_SIZE_TINY, color=AppStyles.COLOR_ERROR)
    
    @staticmethod
    def status_success_style() -> str:
        """Generate success status label style."""
        return AppStyles.label_style(AppStyles.FONT_SIZE_TINY, color=AppStyles.COLOR_SUCCESS)
    
    @staticmethod
    def placeholder_style(size: str = FONT_SIZE_MEDIUM) -> str:
        """Generate placeholder text style."""
        return AppStyles.label_style(size, color=AppStyles.COLOR_PLACEHOLDER)


def load_theme_stylesheet() -> str:
    """
    Load the Windows XP theme stylesheet from file.
    
    Returns:
        The stylesheet content as a string, or empty string if file not found
    """
    stylesheet_path = Path(__file__).parent.parent / "styles" / "xp_theme.qss"
    if stylesheet_path.exists():
        with open(stylesheet_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def apply_theme(widget) -> None:
    """
    Apply the Windows XP theme to a widget (window, dialog, etc.).
    
    Args:
        widget: The widget to apply the theme to
    """
    stylesheet = load_theme_stylesheet()
    if stylesheet:
        widget.setStyleSheet(stylesheet)


