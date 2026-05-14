all:
	pyside6-rcc uawidgets/resources.qrc -o uawidgets/resources.py
	sed -i 's/from PySide6 import QtCore/from PyQt6 import QtCore/' uawidgets/resources.py
