import sys
import unittest
from typing import Any

from asyncua import ua
from asyncua.sync import Server
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QApplication, QTreeView, QAbstractItemDelegate, QTableView

from uawidgets.attrs_widget import AttrsWidget
from uawidgets.refs_widget import RefsWidget


class TestRefsWidget(unittest.TestCase):
    def setUp(self) -> None:
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:48409/freeopcua/server/")
        self.server.start()
        self.widget = RefsWidget(QTableView())

    def tearDown(self) -> None:
        self.server.stop()

    def test_1(self) -> None:
        o = self.server.nodes.objects
        self.widget.show_refs(o)


class TestAttrsWidget(unittest.TestCase):
    def setUp(self) -> None:
        self.server = Server()
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self.server.start()
        self.widget = AttrsWidget(QTreeView())

    def tearDown(self) -> None:
        self.server.stop()

    def find_item(self, text: str) -> QModelIndex:
        idxlist = self.widget.model.match(
            self.widget.model.index(0, 0),
            Qt.ItemDataRole.DisplayRole, text, 1,
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        return idxlist[0]

    def modify_item(self, text: str, val: Any, match_to_use: int = 0) -> None:
        """
        modify the current item and set its displayed value to 'val'
        """
        idxlist = self.widget.model.match(
            self.widget.model.index(0, 0),
            Qt.ItemDataRole.DisplayRole, text, match_to_use + 1,
            Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive,
        )
        if not idxlist:
            raise RuntimeError(f"Item with text '{text}' not found")
        idx = idxlist[match_to_use]
        self.widget.view.setCurrentIndex(idx)
        idx = idx.sibling(idx.row(), 1)
        self.widget.view.edit(idx)
        editor = self.widget.view.focusWidget()
        if not editor:
            raise RuntimeError("Could not get editor widget!, it does not have the focus")

        if hasattr(editor, "_current_node"):
            editor._current_node = val
        elif hasattr(editor, "setCurrentText"):
            editor.setCurrentText(val)
        else:
            editor.setText(val)  # type: ignore[attr-defined]
        self.widget.view.commitData(editor)
        self.widget.view.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)
        self.widget.view.reset()

    def modify_value(self, val: Any) -> None:
        self.modify_item("Value", val, 1)

    def test_display_objects_node(self) -> None:
        objects = self.server.nodes.objects
        self.widget.show_attrs(objects)
        self.modify_item("BrowseName", "5:titi")
        self.assertEqual(objects.read_browse_name().to_string(), "5:titi")
        self.modify_item("BrowseName", "0:Objects")

    def test_display_var_double(self) -> None:
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        self.modify_value("8.45")
        self.assertEqual(myvar.read_value(), 8.45)

    def test_display_var_bytes(self) -> None:
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar_bytes", b"jkl", ua.VariantType.ByteString)
        self.widget.show_attrs(myvar)
        self.modify_value("titi")
        self.assertEqual(myvar.read_value(), b"titi")

    def test_change_data_type(self) -> None:
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        dtype = myvar.read_data_type()
        self.assertEqual(dtype, ua.NodeId(ua.ObjectIds.Double))
        new_dtype = ua.NodeId(ua.ObjectIds.String)
        self.modify_item("DataType", self.server.get_node(new_dtype))
        self.assertEqual(myvar.read_data_type(), new_dtype)

        self.modify_value("mystring")
        self.assertEqual(myvar.read_value(), "mystring")

    def test_change_value_rank(self) -> None:
        objects = self.server.nodes.objects
        myvar = objects.add_variable(1, "myvar1", 9.99, ua.VariantType.Double)
        self.widget.show_attrs(myvar)
        self.modify_item("ValueRank", "ThreeDimensions")
        self.assertEqual(myvar.read_value_rank(), ua.ValueRank.ThreeDimensions)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    unittest.main()
