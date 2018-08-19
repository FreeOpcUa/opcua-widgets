from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtWidgets import QTreeView, QDialog, QHBoxLayout, QVBoxLayout, QDialogButtonBox, QAbstractItemView, QPushButton, QLineEdit, QWidget
from PyQt5.QtCore import Qt

from opcua import Node, ua

from uawidgets.tree_widget import TreeWidget


class GetNodeTextButton(QWidget):
    """
    Create a text field with  a button which will query a node
    """

    def __init__(self, parent, currentnode, startnode):
        QWidget.__init__(self, parent)
        #QWidget.__init__(self)
        if currentnode.nodeid.is_null():
            text = "Null"
        else:
            text = currentnode.nodeid.to_string()
        self.lineEdit = QLineEdit(parent)
        self.lineEdit.setText(text)
        self.button = QPushButton(parent)
        self.button.setText("...")
        self.button.setMinimumWidth(5)
        self.layout = QHBoxLayout(parent)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.lineEdit)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        self.server = currentnode.server
        self.start_node = startnode
        self.button.clicked.connect(self.get_new_node)

    def get_new_node(self):
        node = self.get_node()
        node, ok = GetNodeDialog.getNode(self, self.start_node, currentnode=node)
        if ok:
            self.lineEdit.setText(node.nodeid.to_string())
        return node, ok

    def get_node(self):
        text = self.lineEdit.text()
        if text and text not in ("None", "Null"):
            current = ua.NodeId.from_string(text)
        else:
            current = ua.NodeId() 
        return Node(self.server, current)



class GetNodeButton(QPushButton):
    """
    Create Button which will query a node
    """

    value_changed = pyqtSignal(Node)

    def __init__(self, parent, currentnode, startnode):
        text = "Null"
        try:
            text = currentnode.get_browse_name().to_string()
        except ua.UaError:
            pass
        QPushButton.__init__(self, text, parent)
        self._current_node = currentnode
        self.start_node = startnode
        self.clicked.connect(self.get_new_node)

    def get_new_node(self):
        node, ok = GetNodeDialog.getNode(self, self.start_node, currentnode=self._current_node)
        if ok:
            self._current_node = node
            self.setText(self._current_node.get_browse_name().to_string())
            self.value_changed.emit(self._current_node)
        return node, ok

    def get_node(self):
        return self._current_node


class GetNodeDialog(QDialog):
    def __init__(self, parent, startnode, currentnode=None):
        QDialog.__init__(self, parent)

        layout = QVBoxLayout(self)
        
        self.treeview = QTreeView(self)
        self.treeview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree = TreeWidget(self.treeview)
        self.tree.set_root_node(startnode)
        layout.addWidget(self.treeview)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(self.buttons)
        self.resize(800, 600)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.treeview.activated.connect(self.accept)

        if currentnode:
            self.tree.expand_to_node(currentnode)


    def get_node(self):
        return self.tree.get_current_node()

    @staticmethod
    def getNode(parent, startnode, currentnode=None):
        dialog = GetNodeDialog(parent, startnode, currentnode)
        result = dialog.exec_()
        node = dialog.get_node()
        return node, result == QDialog.Accepted


class GetDataTypeNodeButton(GetNodeButton):
    """
    Specialized GetNodeButton for getting a data type
    Create Button which will query a node
    """

    def __init__(self, parent, server, settings, dtype=None):
        self.settings = settings #We pass settings because we cannot create QSettings before __inint__ of super()
        base_data_type = server.get_node(ua.ObjectIds.BaseDataType)
        if dtype is None:
            dtype = self.settings.value("last_datatype", None)
        if dtype is None:
            current_type = server.get_node(ua.ObjectIds.Float)
        else:
            current_type = server.get_node(dtype)
        GetNodeButton.__init__(self, parent, current_type, base_data_type)

    def get_new_node(self):
        node, ok = GetNodeButton.get_new_node(self)
        if ok:
            self.settings.setValue("last_datatype", node.nodeid.to_string())
        return node, ok


