import os
import sys
import inspect


def get_root_path():
	return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


vendor_path = os.path.join(get_root_path(), 'vendor')
if os.path.isdir(vendor_path) and vendor_path not in sys.path:
	sys.path.append(vendor_path)