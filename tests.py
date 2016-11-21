
import unittest
import sys
import time
sys.path.insert(0, "python-opcua")  # necessary on travis
sys.path.insert(0, ".")

from opcua import ua, Server

from PyQt5.QtCore import QTimer, QSettings, QModelIndex, Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QTreeView, QAbstractItemDelegate
from PyQt5.QtTest import QTest

from uawidgets.attrs_widget import AttrsWidget


class TestAttrsWidget(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self.server.start()
        self.widget = AttrsWidget(QTreeView())

    def tearDown(self):
        self.server.stop()

    def modify_item(self, text, val, match_to_use=0):
        """
        modify the current item and set its displayed value to 'val'
        """
        idxlist = self.widget.model.match(self.widget.model.index(0, 0), Qt.DisplayRole, text, match_to_use + 1, Qt.MatchStartsWith | Qt.MatchRecursive)
        if not idxlist:
            raise RuntimeError("Item with text '{}' not found".format(text))
        idx = idxlist[match_to_use]
        self.widget.view.setCurrentIndex(idx)
        idx = idx.sibling(0, 1)
        self.widget.view.edit(idx)
        editor = self.widget.view.focusWidget()
        editor.setText(val)
        self.widget.view.commitData(editor)
        self.widget.view.closeEditor(editor, QAbstractItemDelegate.NoHint)
        self.widget.view.reset()

    def modify_value(self, val):
        self.modify_item("Value", val, 1)

    def test_display_objects_node(self):
        objects = self.server.nodes.objects
        self.widget.show_attrs(objects)
        self.modify_item("BrowseName", "5:titi")
        self.assertEqual(objects.get_browse_name().to_string(), "5:titi")
        self.modify_item("BrowseName", "0:Objects")  # restore states for other tests

    def test_display_var_double(self):
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        self.modify_value("8.45")
        self.assertEqual(myvar.get_value(), 8.45)

    def test_display_var_bytes(self):
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar_bytes", b"jkl", ua.VariantType.ByteString)
        self.widget.show_attrs(myvar)
        self.modify_value("titi")
        self.assertEqual(myvar.get_value(), b"titi")

    def ZZZ_test_change_data_type(self):  # need to find a way to modify combo box with QTest
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        self.modify_item("DataType", "Float")
        print("DT", myvar.get_data_type())
        self.assertEqual(myvar.get_(), b"titi")






if __name__ == "__main__":
    app = QApplication(sys.argv)
    unittest.main()


