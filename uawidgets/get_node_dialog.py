from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTreeView, QDialog, QVBoxLayout, QDialogButtonBox, QAbstractItemView, QPushButton
from PyQt5.QtCore import Qt

from opcua import Node

from uawidgets.tree_widget import TreeWidget


class GetNodeButton(QPushButton):
    """
    Create Button which will query a node
    """

    value_changed = pyqtSignal(Node)

    def __init__(self, parent, currentnode, startnode):
        text = currentnode.get_browse_name().to_string()
        QPushButton.__init__(self, text, parent)
        self.current_node = currentnode
        self.start_node = startnode
        self.clicked.connect(self.get_new_node)

    def get_new_node(self):
        node, ok = GetNodeDialog.getNode(self, self.start_node)
        if ok:
            self.current_node = node
            self.setText(self.current_node.get_browse_name().to_string())
            self.value_changed.emit(self.current_node)

    def get_node(self):
        return self.current_node


class GetNodeDialog(QDialog):
    def __init__(self, parent, startnode):
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

    def get_node(self):
        return self.tree.get_current_node()

    @staticmethod
    def getNode(parent, startnode):
        dialog = GetNodeDialog(parent, startnode)
        result = dialog.exec_()
        node = dialog.get_node()
        return node, result == QDialog.Accepted
