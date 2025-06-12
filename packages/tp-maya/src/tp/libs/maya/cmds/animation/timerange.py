from __future__ import annotations

from maya import cmds, mel


def playback_slider_object_path() -> str:
    """
    Returns Python object that wraps Playback Slider Maya UI

    :return: Maya Playback slider path.
    """

    return mel.eval("$tmpVar=$gPlayBackSlider")


def get_range_playback() -> tuple[float, float]:
    """
    Returns the current playback range.

    :return: playback range.
    """

    return (
        cmds.playbackOptions(query=True, minTime=True),
        cmds.playbackOptions(query=True, maxTime=True),
    )


def get_selected_frame_range(time_control: str | None = None) -> tuple[float, float]:
    """
    Returns the current selected frame range.

    :param time_control: time control object path to use. If not given, global Maya time range object will be used.
    :return: selected frame range.
    """

    time_control = time_control or playback_slider_object_path()
    return cmds.timeControl(time_control, query=True, rangeArray=True)


def get_selected_or_current_frame_range(
    time_control: str | None = None,
) -> tuple[float, float]:
    """
    Returns the current selected frame range or the current frame range if frame range is selected.

    :param time_control: time control object path to use. If not given, global Maya time range object will be used.
    :return: selected or current frame range.
    """

    frame_range = get_selected_frame_range(time_control=time_control)
    start, end = frame_range

    # If start and end are the same, it means that no frame range is selected so we return the current playback range.
    if end - start == 1:
        frame_range = get_range_playback()

    return frame_range
