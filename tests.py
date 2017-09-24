
import unittest
import sys
import time
sys.path.insert(0, "python-opcua")  # necessary on travis
sys.path.insert(0, ".")

from opcua import ua, Server

from PyQt5.QtCore import QTimer, QSettings, QModelIndex, Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QTreeView, QAbstractItemDelegate, QTableView
from PyQt5.QtTest import QTest

from uawidgets.attrs_widget import AttrsWidget
from uawidgets.refs_widget import RefsWidget


class TestRefsWidget(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:48409/freeopcua/server/")
        self.server.start()
        self.widget = RefsWidget(QTableView())

    def tearDown(self):
        self.server.stop()

    def test_1(self):
        o = self.server.nodes.objects
        self.widget.show_refs(o)


class TestAttrsWidget(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self.server.start()
        self.widget = AttrsWidget(QTreeView())

    def tearDown(self):
        self.server.stop()

    def find_item(self, text):
        idxlist = self.widget.model.match(self.widget.model.index(0, 0), Qt.DisplayRole, text,  1, Qt.MatchExactly | Qt.MatchRecursive)
        idx = idxlist[0]
        return idx

    def modify_item(self, text, val, match_to_use=0):
        """
        modify the current item and set its displayed value to 'val'
        """
        idxlist = self.widget.model.match(self.widget.model.index(0, 0), Qt.DisplayRole, text, match_to_use + 1, Qt.MatchExactly | Qt.MatchRecursive)
        if not idxlist:
            raise RuntimeError("Item with text '{}' not found".format(text))
        idx = idxlist[match_to_use]
        self.widget.view.setCurrentIndex(idx)
        idx = idx.sibling(idx.row(), 1)
        self.widget.view.edit(idx)
        editor = self.widget.view.focusWidget()
        if not editor:
            print(app.focusWidget())
            print("NO EDITOR WIDGET")
            #QTest.keyClick(self.widget.view, Qt.Key_Return)
            from IPython import embed 
            embed()
            raise RuntimeError("Could not get editor widget!, it does not have the focus")

        if hasattr(editor, "_current_node"):
            editor._current_node = val
        elif hasattr(editor, "setCurrentText"):
            editor.setCurrentText(val)
        else:
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

    def test_change_data_type(self):
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        dtype = myvar.get_data_type()
        self.assertEqual(dtype, ua.NodeId(ua.ObjectIds.Double))
        new_dtype = ua.NodeId(ua.ObjectIds.String)
        self.modify_item("DataType", self.server.get_node(new_dtype))
        self.assertEqual(myvar.get_data_type(), new_dtype)

        # now try to write a value which is a string
        self.modify_value("mystring")
        self.assertEqual(myvar.get_value(), "mystring")

    def test_change_value_rank(self):  # need to find a way to modify combo box with QTest
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        rank = myvar.get_value_rank()
        self.modify_item("ValueRank", "ThreeDimensions")
        self.assertEqual(myvar.get_value_rank(), ua.ValueRank.ThreeDimensions)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    unittest.main()


