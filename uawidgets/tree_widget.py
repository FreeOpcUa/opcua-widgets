from PyQt5.QtCore import pyqtSignal, QMimeData, QObject, Qt, QSettings
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QApplication, QAbstractItemView, QAction

from opcua import ua
from opcua import Node
from opcua.ua import UaError


class TreeWidget(QObject):

    error = pyqtSignal(Exception)

    def __init__(self, view):
        QObject.__init__(self, view)
        self.view = view
        self.model = TreeViewModel()
        self.model.clear()  # FIXME: do we need this?
        self.model.error.connect(self.error)
        self.view.setModel(self.model)

        #self.view.setUniformRowHeights(True)
        self.model.setHorizontalHeaderLabels(['DisplayName', "BrowseName", 'NodeId'])
        self.view.header().setSectionResizeMode(0)
        self.view.header().setStretchLastSection(True)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.settings = QSettings()
        state = self.settings.value("tree_widget_state", None)
        if state is not None:
            self.view.header().restoreState(state)

        self.actionReload = QAction("Reload", self)
        self.actionReload.triggered.connect(self.reload_current)

    def save_state(self):
        self.settings.setValue("tree_widget_state", self.view.header().saveState())

    def clear(self):
        self.model.clear()

    def set_root_node(self, node):
        self.model.clear()
        self.model.set_root_node(node)
        self.view.expandToDepth(0)

    def copy_path(self):
        path = self.get_current_path()
        path_str = ",".join(path)
        QApplication.clipboard().setText(path_str)

    def expand_current_node(self, expand=True):
        idx = self.view.currentIndex()
        self.view.setExpanded(idx, expand)

    def expand_to_node(self, node):
        """
        Expand tree until given node and select it
        """
        if isinstance(node, str):
            idxlist = self.model.match(self.model.index(0, 0), Qt.DisplayRole, node, 1, Qt.MatchExactly|Qt.MatchRecursive)
            if not idxlist:
                raise ValueError(f"Node {node} not found in tree")
            node = self.model.data(idxlist[0], Qt.UserRole)
        path = node.get_path()
        for node in path:
            # FIXME: this would be the correct way if it would work
            #idxlist = self.model.match(self.model.index(0, 0), Qt.UserRole, node.node, 2, Qt.MatchExactly|Qt.MatchRecursive)
            try:
                text = node.get_display_name().Text
            except UaError as ex:
                return
            idxlist = self.model.match(self.model.index(0, 0), Qt.DisplayRole, text, 1, Qt.MatchExactly|Qt.MatchRecursive)
            if idxlist:
                idx = idxlist[0]
                self.view.setExpanded(idx, True)
                self.view.setCurrentIndex(idx)
                self.view.activated.emit(idx)
            else:
                print(f"While expanding tree, Could not find node {node} in tree view, this might be OK")

    def copy_nodeid(self):
        node = self.get_current_node()
        text = node.nodeid.to_string()
        QApplication.clipboard().setText(text)

    def get_current_path(self):
        idx = self.view.currentIndex()
        idx = idx.sibling(idx.row(), 0)
        it = self.model.itemFromIndex(idx)
        path = []
        while it and it.data(Qt.UserRole):
            node = it.data(Qt.UserRole)
            name = node.get_browse_name().to_string()
            path.insert(0, name)
            it = it.parent()
        return path

    def update_browse_name_current_item(self, bname):
        idx = self.view.currentIndex()
        idx = idx.sibling(idx.row(), 1)
        it = self.model.itemFromIndex(idx)
        it.setText(bname.to_string())

    def update_display_name_current_item(self, dname):
        idx = self.view.currentIndex()
        idx = idx.sibling(idx.row(), 0)
        it = self.model.itemFromIndex(idx)
        it.setText(dname.Text)

    def reload_current(self):
        idx = self.view.currentIndex()
        idx = idx.sibling(idx.row(), 0)
        it = self.model.itemFromIndex(idx)
        if not it:
            return None
        self.reload(it)

    def reload(self, item=None):
        if item is None:
            item = self.model.item(0, 0)
        for _ in range(item.rowCount()):
            child_it = item.child(0, 0)
            node = child_it.data(Qt.UserRole)
            if node:
                self.model.reset_cache(node)
            item.takeRow(0)
        node = item.data(Qt.UserRole)
        if node:
            self.model.reset_cache(node)
            idx = self.model.indexFromItem(item)
            #if self.view.isExpanded(idx):
            #self.view.setExpanded(idx, True)

    def remove_current_item(self):
        idx = self.view.currentIndex()
        self.model.removeRow(idx.row(), idx.parent())

    def get_current_node(self, idx=None):
        if idx is None:
            idx = self.view.currentIndex()
        idx = idx.sibling(idx.row(), 0)
        it = self.model.itemFromIndex(idx)
        if not it:
            return None
        node = it.data(Qt.UserRole)
        if not node:
            ex = RuntimeError("Item does not contain node data, report!")
            self.error.emit(ex)
            raise ex
        return node


class TreeViewModel(QStandardItemModel):

    error = pyqtSignal(Exception)

    def __init__(self):
        super(TreeViewModel, self).__init__()
        self._fetched = []

    def clear(self):
        # remove all rows but not header!!
        self.removeRows(0, self.rowCount())
        self._fetched = []

    def set_root_node(self, node):
        desc = self._get_node_desc(node)
        self.add_item(desc, node=node)

    def _get_node_desc(self, node):
        attrs = node.get_attributes([ua.AttributeIds.DisplayName, ua.AttributeIds.BrowseName, ua.AttributeIds.NodeId, ua.AttributeIds.NodeClass])
        desc = ua.ReferenceDescription()
        desc.DisplayName = attrs[0].Value.Value
        desc.BrowseName = attrs[1].Value.Value
        desc.NodeId = attrs[2].Value.Value
        desc.NodeClass = attrs[3].Value.Value
        desc.TypeDefinition = ua.TwoByteNodeId(ua.ObjectIds.FolderType)
        return desc

    def add_item(self, desc, parent=None, node=None):
        dname = bname = nodeid = "No Value"
        if desc.DisplayName:
            dname = desc.DisplayName.to_string()
        if desc.BrowseName:
            bname = desc.BrowseName.to_string()
        nodeid = desc.NodeId.to_string()
        item = [QStandardItem(dname), QStandardItem(bname), QStandardItem(nodeid)]
        if desc.NodeClass == ua.NodeClass.Object:
            if desc.TypeDefinition == ua.TwoByteNodeId(ua.ObjectIds.FolderType):
                item[0].setIcon(QIcon(":/folder.svg"))
            else:
                item[0].setIcon(QIcon(":/object.svg"))
        elif desc.NodeClass == ua.NodeClass.Variable:
            if desc.TypeDefinition == ua.TwoByteNodeId(ua.ObjectIds.PropertyType):
                item[0].setIcon(QIcon(":/property.svg"))
            else:
                item[0].setIcon(QIcon(":/variable.svg"))
        elif desc.NodeClass == ua.NodeClass.Method:
            item[0].setIcon(QIcon(":/method.svg"))
        elif desc.NodeClass == ua.NodeClass.ObjectType:
            item[0].setIcon(QIcon(":/object_type.svg"))
        elif desc.NodeClass == ua.NodeClass.VariableType:
            item[0].setIcon(QIcon(":/variable_type.svg"))
        elif desc.NodeClass == ua.NodeClass.DataType:
            item[0].setIcon(QIcon(":/data_type.svg"))
        elif desc.NodeClass == ua.NodeClass.ReferenceType:
            item[0].setIcon(QIcon(":/reference_type.svg"))
        if node:
            item[0].setData(node, Qt.UserRole)
        else:
            parent_node = parent.data(Qt.UserRole)
            item[0].setData(Node(parent_node.server, desc.NodeId), Qt.UserRole)
        if parent:
            return parent.appendRow(item)
        else:
            return self.appendRow(item)

    def reset_cache(self, node):
        if node in self._fetched:
            self._fetched.remove(node)

    def canFetchMore(self, idx):
        item = self.itemFromIndex(idx)
        if not item:
            return False
        node = item.data(Qt.UserRole)
        if node not in self._fetched:
            self._fetched.append(node)
            return True
        return False

    def hasChildren(self, idx):
        item = self.itemFromIndex(idx)
        if not item:
            return True
        node = item.data(Qt.UserRole)
        if node in self._fetched:
            return QStandardItemModel.hasChildren(self, idx)
        return True

    def fetchMore(self, idx):
        parent = self.itemFromIndex(idx)
        if parent:
            self._fetchMore(parent)

    def _fetchMore(self, parent):
        try:
            node = parent.data(Qt.UserRole)
            descs = node.get_children_descriptions()
            descs.sort(key=lambda x: x.BrowseName)
            added = []
            for desc in descs:
                if not desc.NodeId in added:
                    self.add_item(desc, parent)
                    added.append(desc.NodeId)
        except Exception as ex:
            self.error.emit(ex)
            raise

    def mimeData(self, idxs):
        mdata = QMimeData()
        nodes = []
        for idx in idxs:
            item = self.itemFromIndex(idx)
            if item:
                node = item.data(Qt.UserRole)
                if node:
                    nodes.append(node.nodeid.to_string())
        mdata.setText(", ".join(nodes))
        return mdata


