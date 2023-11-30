from __future__ import annotations

import os
import time
import typing
import logging
import tempfile
from datetime import datetime
from typing import Iterator, Any

from overrides import override

from tp.core import log
from tp.bootstrap import log as bootstrap_logger
from tp.libs.rig.frag.core import blueprint, metadata, rig

if typing.TYPE_CHECKING:
    from tp.libs.rig.frag.core.blueprint import BlueprintFile
    from tp.libs.rig.frag.core.action import BuildStep, BuildAction

logger = log.rigLogger


class BlueprintBuilder:
    """
    Blueprint Builder that handles the build of a blueprint into a full rig.
    """

    def __init__(self, blueprint_file: BlueprintFile, debug: bool | None = None, log_dir: str | None = None):
        super().__init__()

        self._blueprint_file = blueprint_file
        self._debug = debug if debug is not None else self.blueprint.setting(blueprint.BlueprintSettings.DebugBuild)
        self._builder_name = 'Builder'
        self._phase: str | None = None
        self._current_build_step_path: str | None = None
        self._generator: Iterator[dict] | None = None
        self._iteration_result: dict = {}

        self._is_started = False
        self._is_finished = False
        self._is_running = False
        self._is_canceled = False
        self._cancel_on_interrupt = True
        self._start_time = 0.0
        self._end_time = 0.0
        self._elapsed_time = 0.0
        self._show_progress_ui = True
        self._progress_title = 'Building Blueprint'

        self._rig: Any = None
        self._rig_name: str = self.blueprint.setting(blueprint.BlueprintSettings.RigName)
        self._rig_metadata: dict = {}

        # Current context that should be associated with any warnings or errors that occur.
        self._log_context = {}
        self._warnings: list[logging.LogRecord] = []
        self._errors: list[logging.LogRecord] = []

        # Logger for this build and handlers.
        self._logger = bootstrap_logger.get_logger('frag.build')
        self._logger.setLevel(logging.DEBUG if self._debug else logging.INFO)
        self._logger.handlers.clear()
        self._build_log_handler = BlueprintBuildLogHandler(self)
        self._logger.addHandler(self._build_log_handler)
        self._file_handler: logging.FileHandler | None = None
        self.setup_file_logger(log_dir)

    @classmethod
    def pre_build_validate(cls, blueprint_file: BlueprintFile) -> bool:
        """
        Performs a quick pre-build validation on given blueprint to ensure building can at least be started.

        :param BlueprintFile blueprint_file: blueprint file instance.
        :return: True if blueprint pre validation was successful; False otherwise.
        :rtype: bool
        """

        if not blueprint_file or not blueprint_file.blueprint:
            logger.error('No blueprint was given')
            return False

        if not blueprint_file.blueprint.setting(blueprint.BlueprintSettings.RigName):
            logger.error('Rig name is not set')
            return False

        if not blueprint_file.blueprint.root_step.has_any_children():
            logger.error('Blueprint has no actions. Create new actions to begin.')
            return False

        return True

    @property
    def blueprint(self) -> blueprint.Blueprint:
        """
        Getter method that returns the blueprint instance associated to this builder.

        :return: blueprint to build.
        :rtype: blueprint.Blueprint
        """

        return self._blueprint_file.blueprint

    @property
    def name(self) -> str:
        """
        Getter method that returns the name of this builder used in logs.

        :return: builder name.
        :rtype: str
        """

        return self._builder_name

    @property
    def current_build_step_path(self) -> str:
        """
        Getter method that returns the current build step path.

        :return: current build step path.
        :rtype: str
        """

        return self._current_build_step_path

    @property
    def phase(self) -> str | None:
        """
        Getter method that returns th current building phase ('setup', 'actions' or 'finished').

        :return: build pahse.
        :rtype: str
        """

        return self._phase

    @property
    def rig(self) -> Any:
        """
        Getter method that returns rig root node.

        :return: rig root node.
        :rtype: Any
        """

        return self._rig

    @rig.setter
    def rig(self, value: Any):
        """
        Setter method that sets current rig to be built by this builder.

        :param Any value: rig to be built.
        """

        self._rig = value
        if self._rig:
            self._rig_metadata = metadata.metadata(self._rig, rig.RIG_METACLASS)

    def setup_file_logger(self, log_dir: str | None = None):
        """
        Creates a file handler for the log of this builder.

        :param str log_dir: optional directory where logger will be created.
        """

        log_dir = log_dir or tempfile.gettempdir()

        date_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        rig_name = self.blueprint.setting(blueprint.BlueprintSettings.RigName, 'test')
        log_file_name = f'frag_build_{rig_name}_{date_str}.log'
        log_file = os.path.join(log_dir, log_file_name)
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

        self._file_handler = logging.FileHandler(log_file)
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(log_formatter)

        self._logger.addHandler(self._file_handler)

    def close_file_logger(self):
        """
        Closes file logger handler.
        """

        self._file_handler.close()

    def remove_log_handlers(self):
        """
        Removes this blueprint builder log handlers.
        """
        self._logger.handlers.clear()

    def start(self, run: bool = True) -> bool:
        """
        Starts the build for the current blueprint.

        :param bool run: whether to automatically run the build once it is started or wait for `run` to be called
            manually.
        :return: True if the build was started; False otherwise.
        :rtype: bool
        """

        if self._is_started:
            self._logger.warning('Builder has already been started')
            return False
        if self._is_finished:
            self._logger.error('Cannot re-start a builder that has already finished, make a new builder')
            return False
        if self._is_canceled:
            self._logger.warning('Builder was cancelled, create a new instance to build again')
            return False

        self._is_started = True

        self._start_time = time.time()
        start_message = self.start_build_log_message()
        if start_message:
            self._logger.info(start_message)

        self._generator = self.build_generator()

        if run:
            self.run()

        return True

    def action_iterator(self) -> Iterator[tuple[BuildStep, BuildAction, int]]:
        """
        Generator function that yields all build actions in the blueprint.

        :return: generator that yields a tuple of build step, build action and variant index for every action within
            the blueprint.
        :rtype: Iterator[tuple[BuildStep, BuildAction, int]]
        """

        for step in self.blueprint.root_step.iterate_children():
            self._log_context = dict(step=step)
            try:
                index = 0
                for action in step.iterate_actions(self.blueprint.config()):
                    yield step, action, index
                    index += 1
            except Exception as err:
                self._logger.error(str(err), exc_info=True)
        self._log_context.clear()

    def build_generator(self) -> Iterator[dict]:
        """
        Main iterator for performing all build operations.
        Runs all build steps and build actions in order.

        :return: iterated build steps and build actions.
        :rtype: Iterator[dict]
        """

        def _generate_all_actions() -> list[tuple[BuildStep, BuildAction, int]]:
            """
            Internal function that expaands all build actions to perform all build steps and their variants.

            :return: list with tuples containing generated built step, its action and the result duration.
            :rtype: list[tuple[BuildStep, BuildAction, int]]
            """

            start_time = time.time()
            result = list(self.action_iterator())
            end_time = time.time()
            duration = end_time - start_time
            self._logger.info('Generated {} actions (%.03fs)', len(result), duration)

            return result

        self.clear_validate_results()

        yield dict(index=1, total=100, phase='setup', status='Retrieve Actions')
        all_actions = _generate_all_actions()
        action_count = len(all_actions)

        for index, (step, action, action_index) in enumerate(all_actions):
            self._current_build_step_path = step.full_path()
            yield dict(index=index, total=action_count, phase='actions', status=self._current_build_step_path)
            action.builder = self
            action.rig = self.rig
            self._log_context = dict(step=step, action=action, action_inde=action_index)
            self.run_build_action(step, action, action_index, index, action_count)
            self._log_context.clear()

        yield dict(index=action_count, total=action_count, phase='finished', status='Finished')

    def run_build_action(self, step: BuildStep, action: BuildAction, action_index: int, index: int, action_count: int):
        """

        :param step:
        :param action:
        :param action_index:
        :param index:
        :param action_count:
        :return:
        """

        start_time = time.time()
        try:
            action.run()
        except Exception as err:
            action.logger.error(str(err), exc_info=True)
            if action.should_abort_on_error():
                self._logger.error(
                    'An error occurred, and this action returned True from `should_abort_on_error`, cancelling build')
                self.cancel()
                return
        end_time = time.time()
        duration = end_time - start_time

        path = step.full_path()
        self._logger.info('[%s/%s] %s[%d] (%.03fs)', index + 1, action_count, path, action_index, duration)

    def pause(self):
        """
        Pauses the current build.
        """

        self._is_running = False

    def run(self):
        """
        Continue current build.

        ..note:: builder must be started by calling `start` first before this can be called.
        """

        if self._is_running:
            self._logger.error('Build is already running.')
            return
        if not self._is_started:
            self._logger.error('Build hsa not been started yet.')
            return
        if self._is_finished:
            self._logger.error('Build has already finished.')
            return

        self._is_running = True

        if self._show_progress_ui:
            # cmds.progressWindow(title=self._progress_title, minValue=0, progress=0, isInterruptable=True)
            pass

        while True:
            self.next()
            if self._show_progress_ui:
                # cmds.progressWindow(
                #     edit=True, progress=self._iteration_result['index'], maxValue=self._iteration_result['total'],
                #     status=self._iteration_result['status'],)
                pass
            if not self._is_running:
                break
            if self.should_interrupt():
                if self._cancel_on_interrupt:
                    self.cancel()
                break

        if self._show_progress_ui:
            # cmds.progressWindow(edit=True, status=None)
            # cmds.progressWindow(endProgress=True)
            pass

        self._is_running = False

    def next(self):
        """
        Performs the next step of the build.
        """

        self._iteration_result = next(self._generator)
        self._phase = self._iteration_result['phase']
        if self._phase == 'finished':
            self.finish()

    def should_interrupt(self) -> bool:
        """
        Returns whether the running build should be interrupted.

        :return: True if build should be interrupted; False otherwise.
        :rtype: bool
        """

        if self._show_progress_ui:
            # return cmds.progressWindow(query=True, isCancelled=True)
            pass

        return False

    def cancel(self):
        """
        Cancels build.
        """

        if self._is_started and not self._is_finished:
            self._is_running = False
            self._is_canceled = True

            self._build_end()

            cancel_message = self.cancel_build_log_message()
            level = logging.WARNING if self.has_errors() else logging.INFO
            self._logger.log(level, cancel_message)

            self.close_file_logger()
            self.remove_log_handlers()

            # in_view_message = self.cancel_build_in_view_message()
            # in_view_kwargs = {}
            # if self.has_errors():
            #     in_view_kwargs = dict(backColor=0xAA8336, fadeStayTime=3000)
            # cmds.inViewMessage(assistMessage=in_view_msg, position="topCenter", fade=True, **in_view_kwargs)

    def finish(self):
        """
        Finishes the build.
        """

        self._is_running = False
        self._is_finished = True

        self._build_end()

        finish_message = self.finish_build_log_message()
        level = logging.WARNING if self.has_errors() else logging.INFO
        self._logger.log(level, finish_message)

        self.close_file_logger()
        self.remove_log_handlers()

        # in_view_message = self.finish_build_in_view_message()
        # in_view_kwargs = {}
        # if self.has_errors():
        #     in_view_kwargs = dict(backColor=0xAA8336, fadeStayTime=3000)
        # cmds.inViewMessage(assistMessage=in_view_msg, position="topCenter", fade=True, **in_view_kwargs)

    def start_build_log_message(self) -> str:
        """
        Returns the log message that should appear when build process starts.

        :return: start build log message.
        :rtype: str
        """

        return f'Started building rig: {self._rig_name} (debug={self._debug})'

    def cancel_build_log_message(self) -> str:
        """
        Returns the log message that should appear when build process is cancelled by user.

        :return: cancel build log message.
        :rtype: str
        """

        return f'Cancelled build of rig {self._rig_name} with {self.error_summary()} ({self._elapsed_time:.3f}s)'

    def finish_build_log_message(self) -> str:
        """
        Returns the log message that should appear when build process ends.

        :return: end build log message.
        :rtype: str
        """

        return f'Built rig: {self._rig_name} with {self.error_summary()} ({self._elapsed_time:.3f}s)'

    def cancel_build_in_view_message(self) -> str:
        """
        Returns the view message that should appear when build process is cancelled by user.

        :return: cancel build view message.
        :rtype: str
        """

        return f'Build cancelled with {self.error_summary()}' if self.has_errors() else 'Build cancelled'

    def finish_build_in_view_message(self) -> str:
        """
        Returns the view message that should appear when build process ends.

        :return: end build view message.
        :rtype: str
        """

        return f'Build finished with {self.error_summary()}' if self.has_errors() else 'Build successful'

    def has_errors(self) -> bool:
        """
        Returns whether builder has generated errors during the build process.

        :return: True if there are built errors; False otherwise.
        :rtype: bool
        """

        return bool(self._errors)

    def error_summary(self) -> str:
        """
        Returns a string representing the number of warnings and errors. More specifically:
            - "no errors" if no warnings or errors occurred.
            - "{count} warnings" if only warnings occurred.
            - "{count} errors" if any errors occurred.

        :return: summary string.
        :rtype: str
        """

        if self._errors:
            count = len(self._errors)
            return f'{count} error{"s" if count > 1 else ""}'
        elif self._warnings:
            count = len(self._warnings)
            return f'{count} warning{"s" if count > 1 else ""}'

        return 'no errors'

    def notify_log(self, record: logging.LogRecord):
        """
        Tracks warnings and errors and parse extra information to be able to present it in the build results.

        :param logging.LogRecord record: log record.
        """

        def _update_log_with_context(_record: logging.LogRecord):
            """
            Internal function that updates a warning or error log with the current context.

            :param logging.LogRecord _record: logging record.
            """

            extra = {}

            build_step: BuildStep = self._log_context.get('step')
            if build_step:
                extra['step_path'] = build_step.full_path()

            build_action: BuildAction = self._log_context.get('action')
            if build_action:
                extra['action_data'] = build_action.serialize()

            record.__dict__.update(extra)

        def _log_step() -> BuildStep | None:
            """
            Internal function that returns the current build step that should be associated with any warnings or errors.
            """

            return self._log_context['step'] if 'step' in self._log_context else self.blueprint.root_step

        if not self._is_started or self._is_finished or self._is_canceled:
            return

        if record.levelno < logging.WARNING:
            return

        _update_log_with_context(record)
        self._errors.append(record)
        step = _log_step()
        if step:
            step.add_validate_error(record)

    def clear_validate_results(self):
        """
        Clears the results of any previous validation or build.
        """

        self.blueprint.root_step.clear_validate_results()
        for step in self.blueprint.root_step.iterate_children():
            step.clear_validate_results()

    def apply_rig_metadata(self):
        """
        Applies the pending rig metadata.

        ..info:: Only called after the build is done as an optimization, but the pending metadata can be accessed at
            anytime from this builder.
        """

        if not self._rig:
            return

        metadata.set_metadata(self._rig, rig.RIG_METACLASS, self._rig_metadata, undoable=False)

    def _build_end(self):
        """
        Internal function that is called once build is completed.
        """

        self.apply_rig_metadata()

        # cmds.select(clear=True)

        self._end_time = time.time()
        self._elapsed_time = self._end_time - self._start_time


class BlueprintBuildLogHandler(logging.Handler):
    """
    Logger handler that sends logs to the blueprint builder so that it can track warnings and errors.
    """

    def __init__(self, builder: BlueprintBuilder):
        super().__init__()

        self._builder = builder

    @override
    def emit(self, record: logging.LogRecord) -> None:
        if not self._builder:
            return
        self._builder.notify_log(record)


class BlueprintValidator(BlueprintBuilder):
    """
    Blueprint builder that runs validation for all build steps within a blueprint.
    """

    def __init__(self, blueprint_file: BlueprintFile, debug: bool | None = None, log_dir: str | None = None):
        super().__init__(blueprint_file, debug=debug, log_dir=log_dir)

        self._builder_name = 'Validator'
        self._progress_title = 'Validating Blueprint'
        self._show_progress_ui = False
