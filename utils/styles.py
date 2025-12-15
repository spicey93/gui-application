"""Centralized style constants and utilities."""
from typing import Dict


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

