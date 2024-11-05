from __future__ import annotations

# SPACINGS
SPACING = 2
SMALL_SPACING = 4  # small widgets spacing (spacing between each sub-widget)
DEFAULT_SPACING = 6  # default widgets spacing (spacing between each sub-widget)
LARGE_SPACING = 10  # large spacing of each widget (spacing between each sub-widget)
SUPER_LARGE_SPACING = (
    15  # very large spacing of each widget (spacing between each sub-widget)
)
SUPER_LARGE_SPACING_2 = (
    20  # very large spacing of each widget (spacing between each sub-widget)
)
SUPER_EXTRA_LARGE_SPACING = (
    30  # extra large spacing of each widget (spacing between each sub-widget)
)
WINDOW_SPACING = SPACING

# PADDINGS
TOP_PADDING = 10  # padding between the top widget and the top frame
BOTTOM_PADDING = 5  # padding between the bottom widget and bottom of frame.
REGULAR_PADDING = 10  # padding between widgets
SMALL_PADDING = 5
VERY_SMALL_PADDING = 3
LARGE_PADDING = 15
WINDOW_SIDE_PADDING = 2  # overall padding for each window side.
WINDOW_TOP_PADDING = 2  # overall window padding at the top of frame.
WINDOW_BOTTOM_PADDING = 2  # overall window padding at the bottom of frame.
FRAMELESS_VERTICAL_PADDING = 12  # vertical padding for frameless resizers.
FRAMELESS_HORIZONTAL_PADDING = 10  # horizontal padding for frameless resizers.

# MARGINS
MARGINS = (2, 2, 2, 2)  # default left, top, right, bottom widget margins.
WINDOW_MARGINS = (
    WINDOW_SIDE_PADDING,
    WINDOW_BOTTOM_PADDING,
    WINDOW_SIDE_PADDING,
    WINDOW_TOP_PADDING,
)

BUTTON_WIDTH_ICON_SMALL = 10
BUTTON_WIDTH_ICON_REGULAR = 20
BUTTON_WIDTH_ICON_MEDIUM = 30
BUTTON_WIDTH_ICON_LARGE = 40
BUTTON_WIDTH_REGULAR_SMALL = 90
BUTTON_WIDTH_REGULAR_LARGE = 180


class Sizes:
    """
    Class that contains default sizes that can be used within UIs.
    """

    Tiny = 18
    Small = 24
    Medium = 32
    Large = 40
    Huge = 48
    SmallFontSize = 9
    MediumFontSize = 10
    LargeFontSize = 14
    Margin = 14
    Spacing = 2
    SmallSpacing = 4
    MediumSpacing = 6
    LargeSpacing = 10
    VeryLargeSpacing = 15
    HugeSpacing = 20
    VeryHugeSpacing = 30
    IndicatorWidth = 4
    RowHeight = 34
    RowSeparator = 1
    Width = 640
    Height = 480
    TitleLogoIcon = 12
    FramelessVerticalPadding = 12
    FramelessHorizontalPadding = 10
    WindowSizePadding = 6
    WindowBottomPadding = 6


class ButtonStyles:
    """
    Class that contains available button styles.
    """

    Default = 0  # default BaseButton with optional text or an icon.
    TransparentBackground = 1  # default BaseButton with a transparent background.
    IconShadow = 2  # button with a shadow underline.
    DefaultQt = 3  # default style using standard Qt PushButton.
    Rounded = 4  # rounded button with a background color and a colored icon.
    SmallLabel = 5  # small label button with a background color and a colored icon.
