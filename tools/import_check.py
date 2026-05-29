import importlib

try:
    importlib.import_module('modules.main_window')
    importlib.import_module('modules.dashboard_ui')
    print('IMPORTS_OK')
except Exception as e:
    print('IMPORT_ERROR:', e)
