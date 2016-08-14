from PyQt5.QtCore import pyqtSignal, Qt, QObject
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QStyledItemDelegate, QComboBox, QWidget, QVBoxLayout, QCheckBox, QDialog

from opcua import ua
from opcua import Node
from opcua.common.ua_utils import string_to_variant, variant_to_string, val_to_string

from uawidgets.get_node_dialog import GetNodeButton


class BitEditor(QDialog):
    """
    Edit bits in data
    FIXME: this should be a dialog but a Widget appearing directly in treewidget
    Patch welcome
    """

    def __init__(self, parent, attr, val):
        QDialog.__init__(self, parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.boxes = []
        self.enum = attr_to_enum(attr)
        for el in self.enum:
            box = QCheckBox(el.name, parent)
            layout.addWidget(box)
            self.boxes.append(box)
            if ua.test_bit(val, el.value):
                box.setChecked(True)
            else:
                box.setChecked(False)

    def get_byte(self):
        data = 0
        for box in self.boxes:
            if box.isChecked():
                data = ua.set_bit(data, self.enum[box.text()].value)
        return data


class AttrsWidget(QObject):

    error = pyqtSignal(str)
    modified = pyqtSignal()

    def __init__(self, view):
        QObject.__init__(self, view)
        self.view = view
        delegate = MyDelegate(self.view, self)
        self.view.setItemDelegate(delegate)
        self.model = QStandardItemModel()
        self.view.setModel(self.model)
        self.current_node = None
        self.model.itemChanged.connect(self._item_changed)
        self.view.header().setSectionResizeMode(1)

        # Context menu
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.showContextMenu)
        copyaction = QAction("&Copy Value", self.model)
        copyaction.triggered.connect(self._copy_value)
        self._contextMenu = QMenu()
        self._contextMenu.addAction(copyaction)

    def _item_changed(self, item):
        attr, dv = item.data(Qt.UserRole)
        print("Item changed", attr, dv)
        try:
            self.current_node.set_attribute(attr, dv)
        except Exception as ex:
            self.error.emit(ex)
            raise
        self.modified.emit()

    def showContextMenu(self, position):
        item = self.get_current_item()
        if item:
            self._contextMenu.exec_(self.view.viewport().mapToGlobal(position))

    def get_current_item(self, col_idx=0):
        idx = self.view.currentIndex()
        return self.model.item(idx.row(), col_idx)

    def _copy_value(self, position):
        it = self.get_current_item(1)
        if it:
            QApplication.clipboard().setText(it.text())

    def clear(self):
        self.model.clear()

    def reload(self):
        self.show_attrs(self.current_node)

    def show_attrs(self, node):
        self.current_node = node
        self.model.clear()
        if self.current_node:
            self._show_attrs()
        self.view.expandAll()

    def _show_attrs(self):
        attrs = self.get_all_attrs()
        self.model.setHorizontalHeaderLabels(['Attribute', 'Value', 'DataType'])
        for attr, dv in attrs:
            if attr == ua.AttributeIds.DataType:
                string = data_type_to_string(dv)
            elif attr in (ua.AttributeIds.AccessLevel,
                          ua.AttributeIds.UserAccessLevel,
                          ua.AttributeIds.WriteMask,
                          ua.AttributeIds.UserWriteMask,
                          ua.AttributeIds.EventNotifier):
                string = enum_to_string(attr, dv)
            else:
                string = variant_to_string(dv.Value)
            name_item = QStandardItem(attr.name)
            vitem = QStandardItem(string)
            vitem.setData((attr, dv), Qt.UserRole)
            self.model.appendRow([name_item, vitem, QStandardItem(dv.Value.VariantType.name)])

            # special case for Value, we want to show timestamps
            if attr == ua.AttributeIds.Value:
                string = val_to_string(dv.ServerTimestamp)
                name_item.appendRow([QStandardItem("Server Timestamp"), QStandardItem(string), QStandardItem(ua.VariantType.DateTime.name)])
                string = val_to_string(dv.SourceTimestamp)
                name_item.appendRow([QStandardItem("Source Timestamp"), QStandardItem(string), QStandardItem(ua.VariantType.DateTime.name)])

    def get_all_attrs(self):
        attrs = [attr for attr in ua.AttributeIds]
        try:
            dvs = self.current_node.get_attributes(attrs)
        except Exception as ex:
            self.error.emit(ex)
            raise
        res = []
        for idx, dv in enumerate(dvs):
            if dv.StatusCode.is_good():
                res.append((attrs[idx], dv))
        res.sort(key=lambda x: x[0].name)
        return res


class MyDelegate(QStyledItemDelegate):
    def __init__(self, parent, attrs_widget):
        QStyledItemDelegate.__init__(self, parent)
        self.attrs_widget = attrs_widget

    def createEditor(self, parent, option, idx):
        if idx.column() != 1:
            return None
        item = self.attrs_widget.model.itemFromIndex(idx)
        attr, dv = item.data(Qt.UserRole)
        text = item.text()
        if attr == ua.AttributeIds.NodeId:
            return None
        if dv.Value.VariantType == ua.VariantType.Boolean:
            combo = QComboBox(parent)
            combo.addItem("True")
            combo.addItem("False")
            combo.setCurrentText(text)
            return combo
        elif attr == ua.AttributeIds.NodeClass:
            combo = QComboBox(parent)
            for nclass in ua.NodeClass:
                combo.addItem(nclass.name)
            combo.setCurrentText(text)
            return combo
        elif attr == ua.AttributeIds.DataType:
            nodeid = getattr(ua.ObjectIds, text)
            node = Node(self.attrs_widget.current_node.server, nodeid)
            startnode = Node(self.attrs_widget.current_node.server, ua.ObjectIds.BaseDataType)
            button = GetNodeButton(parent, node, startnode)
            return button
        elif attr in (ua.AttributeIds.AccessLevel,
                      ua.AttributeIds.UserAccessLevel,
                      ua.AttributeIds.WriteMask,
                      ua.AttributeIds.UserWriteMask,
                      ua.AttributeIds.EventNotifier):
            return BitEditor(parent, attr, dv.Value.Value)
        else:
            return QStyledItemDelegate.createEditor(self, parent, option, idx)

    #def setEditorData(self, editor, index):
        #pass

    def setModelData(self, editor, model, idx):
        #item = self.attrs_widget.model.itemFromIndex(idx)
        attr, dv = model.data(idx, Qt.UserRole)
        if attr == ua.AttributeIds.NodeClass:
            dv.Value.Value = ua.NodeClass[editor.currentText()]
            text = editor.currentText()
        elif attr == ua.AttributeIds.DataType:
            dv.Value.Value = editor.get_node().nodeid
            text = data_type_to_string(dv)
        elif attr in (ua.AttributeIds.AccessLevel,
                      ua.AttributeIds.UserAccessLevel,
                      ua.AttributeIds.WriteMask,
                      ua.AttributeIds.UserWriteMask,
                      ua.AttributeIds.EventNotifier):
            dv.Value.Value = editor.get_byte()
            text = enum_to_string(attr, dv)
        else:
            if isinstance(editor, QComboBox):
                text = editor.currentText()
            else:
                text = editor.text()
            dv.Value = string_to_variant(text, dv.Value.VariantType)
        #model.setItemData(idx, [text, (attr, dv)], [Qt.DisplayRole, Qt.UserRole])
        model.setItemData(idx, {Qt.DisplayRole: text, Qt.UserRole: (attr, dv)})

def data_type_to_string(dv):
    # a bit too complex, we could just display browse name of node but it requires a query
    if isinstance(dv.Value.Value.Identifier, int) and dv.Value.Value.Identifier < 63:
        string = ua.DataType_to_VariantType(dv.Value.Value).name
    elif dv.Value.Value.Identifier in ua.ObjectIdNames:
        string = ua.ObjectIdNames[dv.Value.Value.Identifier]
    else:
        string = dv.Value.Value.to_string()
    return string


def attr_to_enum(attr):
    attr_name = attr.name
    if attr_name.startswith("User"):
        attr_name = attr_name[4:]
    return getattr(ua, attr_name)


def enum_to_string(attr, dv):
    attr_enum = attr_to_enum(attr)
    string = ", ".join([e.name for e in attr_enum.parse_bitfield(dv.Value.Value)])
    return string
