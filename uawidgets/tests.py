
import unittest
import sys
print("SYS:PATH", sys.path)
sys.path.insert(0, "python-opcua")
sys.path.insert(0, "..")

from opcua import ua, Server

from PyQt5.QtCore import QTimer, QSettings, QModelIndex, Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QTreeView
from PyQt5.QtTest import QTest

from attrs_widget import AttrsWidget


class TestAttrsWidget(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self.server.start()
        self.widget = AttrsWidget(QTreeView())

    def tearDown(self):
        self.server.stop()

    def test_add_folder(self):
        objects = self.server.nodes.objects
        self.widget.show_attrs(objects)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    unittest.main()


