
from PyQt5.QtCore import pyqtSignal, QObject, QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from opcua import ua


class RefsWidget(QObject):

    error = pyqtSignal(str)

    def __init__(self, view):
        self.view = view
        QObject.__init__(self, view)
        self.model = QStandardItemModel()
        self.view.setModel(self.model)
        self.settings = QSettings()
        self.model.setHorizontalHeaderLabels(['ReferenceType', 'NodeId', "BrowseName", "TypeDefinition"])
        self.view.horizontalHeader().setSectionResizeMode(0)
        self.view.horizontalHeader().setStretchLastSection(True)
        state = self.settings.value("refs_widget", None)
        if state is not None:
            self.view.horizontalHeader().restoreState(state)

    def clear(self):
        # remove all rows but not header!!
        self.model.removeRows(0, self.model.rowCount())

    def save_state(self):
        self.settings.setValue("refs_widget", self.view.horizontalHeader().saveState())

    def show_refs(self, node):
        self.clear()
        self._show_refs(node)

    def _show_refs(self, node):
        try:
            refs = node.get_children_descriptions(refs=ua.ObjectIds.References)
        except Exception as ex:
            self.error.emit(ex)
            raise
        for ref in refs:
            typename = ua.ObjectIdNames[ref.ReferenceTypeId.Identifier]
            if ref.NodeId.NamespaceIndex == 0 and ref.NodeId.Identifier in ua.ObjectIdNames:
                nodeid = ua.ObjectIdNames[ref.NodeId.Identifier]
            else:
                nodeid = ref.NodeId.to_string()
            if ref.TypeDefinition.Identifier in ua.ObjectIdNames:
                typedef = ua.ObjectIdNames[ref.TypeDefinition.Identifier]
            else:
                typedef = ref.TypeDefinition.to_string()
            self.model.appendRow([QStandardItem(typename),
                                  QStandardItem(nodeid),
                                  QStandardItem(ref.BrowseName.to_string()),
                                  QStandardItem(typedef)
                                 ])


