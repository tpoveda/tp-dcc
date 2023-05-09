#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains theme implementation
"""

from tp.core import log
from tp.common.python import helpers, color, path
from tp.common.resources import cache, color as qt_color
from tp.common.qt import consts, dpi

logger = log.tpLogger


def solve_value(theme_data, attribute_name):
    """
    Solves a theme given attribute value withing the given theme data.

    :param dict or Theme theme_data: theme dictionary data we want to retrieve value of.
    :param str attribute_name: name of the attribute to retrieve.
    :return: object
    """

    # Import here to avoid cyclic imports
    from tp.common.resources import api as resources

    style_attribute_name = attribute_name if attribute_name.startswith('@') else '@{}'.format(attribute_name)
    setting = theme_data.get(style_attribute_name)
    if isinstance(setting, int):
        return setting
    elif helpers.is_string(setting):
        if setting.startswith('^'):
            # return int(setting[1:])
            return dpi.dpi_scale(int(setting[1:]))
        elif setting.startswith('@^'):
            return dpi.dpi_scale(int(setting[2:]))
        elif 'icon' in style_attribute_name.lower():
            style = theme_data.get('style', 'default')
            resource_path = resources.get('icons', style, str(setting))
            if path.is_file(resource_path):
                return resource_path
        if color.string_is_hex(setting):
            try:
                color_list = color.hex_to_rgba(setting)
                return 'rgba({}, {}, {}, {})'.format(
                    color_list[0], color_list[1], color_list[2], color_list[3])
            except ValueError:
                # this exception will be raised if we try to convert an attribute that is not a color.
                return setting

    return theme_data.get(attribute_name)


def fade_color(color_to_fade, alpha):
    """
    Function that fades given color based on given alpha and return value ready to be used by styles.

    :param  str or list(float) or QColor color_to_fade: color to fade.
    :param str alpha: fade alpha value as percentage (10%, 5%, etc)
    :return: new faded color as string
    :rtype: str
    """

    color_to_fade = qt_color.Color(color_to_fade)
    return 'rgba({}, {}, {}, {})'.format(color_to_fade.red(), color_to_fade.green(), color_to_fade.blue(), alpha)


class Theme(dict):

    EXTENSION = '.yml'

    def __init__(self, name, data_dict=None):
        super(Theme, self).__init__()

        data_dict = data_dict or dict()
        overrides = data_dict.get('overrides', dict())
        overrides = {key if key.startswith('@') else '@{}'.format(key): value for key, value in overrides.items()}

        self._name = name
        self._style = data_dict.get('style', 'default')
        self._accent_color = data_dict.get('accent_color', '#26BBFF')
        self._default_size = consts.Sizes.SMALL

        # initialize default theme properties
        self['style'] = self._style
        self.update(**self._init_default_options())
        self.update(**self._init_colors())
        self.update(**self._init_sizes())
        self.update(**self._init_fonts())
        self.update(**self._init_icons())
        self.update(**self._update_accent_color())
        self.update(**overrides)

    def __getattr__(self, item):
        return solve_value(self, item)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def style(self):
        return self._style

    @property
    def default_size(self):
        return self._default_size

    @default_size.setter
    def default_size(self, value):
        self._default_size = value

    @property
    def accent_color(self):
        return self._accent_color

    @accent_color.setter
    def accent_color(self, value):
        self._accent_color = value
        self.update(**self._update_accent_color())

    def _init_default_options(self):
        """
        Internal function that initializes and returns default theme options.
        """

        # Import here to avoid cyclic imports
        from tp.common import qt

        data = dict(
            dpi=1,
            unit='px',
            PRIMARY_FONT=qt.font_db().primary_font(consts.Sizes.MEDIUM_FONT_SIZE)[0].family(),
            SECONDARY_FONT=qt.font_db().secondary_font(consts.Sizes.SMALL_FONT_SIZE)[0].family()
        )
        data = {'@{}'.format(key).upper(): value for key, value in data.items()}

        return data

    def _init_colors(self):
        """
        Internal function that initializes and returns initial colors
        """

        info_color = consts.Colors.BLUE
        success_color = consts.Colors.GREEN
        processing_color = consts.Colors.BLUE
        warning_color = consts.Colors.GOLD
        error_color = consts.Colors.RED

        data = dict(
            accent_color=consts.Colors.BLUE,
            info_color=info_color,
            success_color=success_color,
            processing_color=processing_color,
            warning_color=warning_color,
            error_color=error_color,
            info_1=fade_color(info_color, '15%'),
            info_2=qt_color.generate_color(info_color, 2),
            info_3=fade_color(info_color, '35%'),
            info_4=qt_color.generate_color(info_color, 4),
            info_5=qt_color.generate_color(info_color, 5),
            info_6=qt_color.generate_color(info_color, 6),
            info_7=qt_color.generate_color(info_color, 7),
            info_8=qt_color.generate_color(info_color, 8),
            info_9=qt_color.generate_color(info_color, 9),
            info_10=qt_color.generate_color(info_color, 10),
            success_1=fade_color(success_color, '15%'),
            success_2=qt_color.generate_color(success_color, 2),
            success_3=fade_color(success_color, '35%'),
            success_4=qt_color.generate_color(success_color, 4),
            success_5=qt_color.generate_color(success_color, 5),
            success_6=qt_color.generate_color(success_color, 6),
            success_7=qt_color.generate_color(success_color, 7),
            success_8=qt_color.generate_color(success_color, 8),
            success_9=qt_color.generate_color(success_color, 9),
            success_10=qt_color.generate_color(success_color, 10),
            warning_1=fade_color(warning_color, '15%'),
            warning_2=qt_color.generate_color(warning_color, 2),
            warning_3=fade_color(warning_color, '35%'),
            warning_4=qt_color.generate_color(warning_color, 4),
            warning_5=qt_color.generate_color(warning_color, 5),
            warning_6=qt_color.generate_color(warning_color, 6),
            warning_7=qt_color.generate_color(warning_color, 7),
            warning_8=qt_color.generate_color(warning_color, 8),
            warning_9=qt_color.generate_color(warning_color, 9),
            warning_10=qt_color.generate_color(warning_color, 10),
            error_1=fade_color(error_color, '15%'),
            error_2=qt_color.generate_color(error_color, 2),
            error_3=fade_color(error_color, '35%'),
            error_4=qt_color.generate_color(error_color, 4),
            error_5=qt_color.generate_color(error_color, 5),
            error_6=qt_color.generate_color(error_color, 6),
            error_7=qt_color.generate_color(error_color, 7),
            error_8=qt_color.generate_color(error_color, 8),
            error_9=qt_color.generate_color(error_color, 9),
            error_10=qt_color.generate_color(error_color, 10),
            transparent=consts.Colors.rgb(consts.Colors.TRANSPARENT)
        )
        data = {'@{}'.format(key).upper(): value for key, value in data.items()}

        return data

    def _init_sizes(self):
        """
        Internal function that initializes all theme sizes
        """

        tiny = consts.Sizes.TINY
        small = consts.Sizes.SMALL
        medium = consts.Sizes.MEDIUM
        large = consts.Sizes.LARGE
        huge = consts.Sizes.HUGE

        data = dict(
            border_radius_large=8,
            border_radius_base=4,
            border_radius_small=2,
            tiny=tiny,
            small=small,
            medium=medium,
            large=large,
            huge=huge,
            tiny_icon=tiny - 8,
            small_icon=small - 10,
            medium_icon=medium - 12,
            large_icon=large - 16,
            huge_icon=huge - 20,
            window_dragger_rounded_corners=5,
            window_dragger_font_size=12,
            window_rounded_corners=5,
            button_padding=4
        )
        data = {'@{}'.format(key).upper(): value for key, value in data.items()}

        return data

    def _init_fonts(self):
        """
        Internal function that initializes all theme fonts
        """

        font_size_base = 14

        data = dict(
            font_family='"Roboto","BlinkMacSystemFont","Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",' \
                        '"Helvetica Neue","Helvetica,Arial,sans-serif"',
            font_size_base=font_size_base,
            font_size_large=font_size_base + 2,
            font_size_small=font_size_base - 2,
            h1_size=int(font_size_base * 2.71),
            h2_size=int(font_size_base * 2.12),
            h3_size=int(font_size_base * 1.71),
            h4_size=int(font_size_base * 1.41),
            h5_size=int(font_size_base * 1.12)
        )
        data = {'@{}'.format(key).upper(): value for key, value in data.items()}

        return data

    def _init_icons(self):
        """
        Internal function that initializes all theme icons
        """

        data = dict(
            radio_checked_icon='radio_button_checked.png',
            radio_unchecked_icon='radio_button_unchecked.png',
            up_icon='collapse.png',
            down_icon='expand.png',
            up_arrow_icon='up_arrow.png',
            down_arrow_icon='down_arrow.png',
            down_arrow_svg_icon='down_arrow.svg',
            down_arrow_white_svg_icon='down_arrow_white.svg',
            up_arrow_svg_icon='up_arrow.svg',
            up_arrow_white_svg_icon='up_arrow_white.svg',
            radio_svg_icon='radio.svg',
            unradio_svg_icon='unradio.svg',
            left_icon='back.png',
            right_icon='next.png',
            calendar_icon='calendar.png',
            check_icon='check.png',
            uncheck_icon='uncheck.png',
            check_svg_icon='check.svg',
            uncheck_svg_icon='uncheck.svg',
            splitter_icon='splitter.png',
            vline_icon='vline.png',
            branch_closed_icon='branch_closed.png',
            branch_more_icon='branch_more.png',
            branch_open_icon='branch_open.png',
            branch_end_icon='branch_end.png',
            down_triangle_svg_icon='down_triangle.svg',
            down_triangle_white_svg_icon='down_triangle_white.svg',
            right_triangle_svg_icon='right_triangle.svg',
            right_triangle_white_svg_icon='right_triangle_white.svg',
            progress_pattern_svg_icon='progress_pattern.svg',
            cross_svg_icon='cross.svg',
            cross_white_svg_icon='cross_white.svg'
        )
        data = {'@{}'.format(key).upper(): value for key, value in data.items()}

        return data

    def _update_accent_color(self):
        """
        Internal function that updates the dynamically generated acent color levels.

        :param str or list(float) or QColor accent_color: new accent color.
        """

        accent_color = qt_color.convert_to_hex(self._accent_color)
        data = dict(
            accent_color=accent_color,
            accent_color_1=qt_color.generate_color(accent_color, 1),
            accent_color_2=qt_color.generate_color(accent_color, 2),
            accent_color_3=qt_color.generate_color(accent_color, 3),
            accent_color_4=qt_color.generate_color(accent_color, 4),
            accent_color_5=qt_color.generate_color(accent_color, 5),
            accent_color_6=qt_color.generate_color(accent_color, 6),
            accent_color_7=qt_color.generate_color(accent_color, 7),
            accent_color_8=qt_color.generate_color(accent_color, 8),
            accent_color_9=qt_color.generate_color(accent_color, 9),
            accent_color_10=qt_color.generate_color(accent_color, 10)
        )
        data = {'@{}'.format(key).upper(): value for key, value in data.items()}

        return data


ThemeCache = cache.CacheResource(Theme)
