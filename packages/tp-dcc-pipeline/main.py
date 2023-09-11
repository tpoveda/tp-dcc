import os
import sys
import inspect

# Do not import other modules that use tp-dcc framework
from tp.tools.pipeline import app


def compile_resources():
    from tp.common.resources import utils
    root_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    resources_qrc_file = os.path.join(root_path, 'resources', 'resources.qrc')
    resources_py_fie = os.path.join(root_path, 'resources.py')
    utils.create_python_qrc_file(resources_qrc_file, resources_py_fie)


def main():

    # register environment variables
    os.environ['TPDCC_ADMIN'] = 'True'
    os.environ['TPDCC_ENV_DEV'] = 'True'
    os.environ['TPDCC_TOOLS_ROOT'] = r'E:\tools\dev\tp-dcc-tools'
    os.environ['TPDCC_DEPS_ROOT'] = r'E:\tools\dev\tp-dcc-tools\venv310\Lib\site-packages'

    root_python_path = os.path.abspath(os.path.join(os.environ['TPDCC_TOOLS_ROOT'], 'bootstrap', 'python'))
    if root_python_path not in sys.path:
        sys.path.append(root_python_path)

    # compile resources
    compile_resources()
    import resources
    resources.qInitResources()

    # we create the Pipeline Application instance
    pipeline_app = app.PipelineApplication(sys.argv)

    # load framework
    import tp.bootstrap
    tp.bootstrap.init(package_version_file='package_version_standalone.config')

    # import other modules
    from tp.tools.pipeline.views import mainwindow

    main_window = mainwindow.MainWindow()
    main_window.show()

    return pipeline_app.exec()


if __name__ == '__main__':
    main()
