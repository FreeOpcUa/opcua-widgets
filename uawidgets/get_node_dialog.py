from PyQt5.QtWidgets import QTreeView, QDialog, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt

from uawidgets.tree_widget import TreeWidget


class GetNodeDialog(QDialog):
    def __init__(self, parent, startnode):
        QDialog.__init__(self, parent)

        layout = QVBoxLayout(self)
        
        self.treeview = QTreeView(self)
        self.tree = TreeWidget(self.treeview)
        self.tree.set_root_node(startnode)
        layout.addWidget(self.treeview)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def get_node(self):
        return self.tree.get_current_node()

    @staticmethod
    def getNode(parent, startnode):
        dialog = GetNodeDialog(parent, startnode)
        result = dialog.exec_()
        node = dialog.get_node()
        return node, result == QDialog.Accepted
