from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QPushButton, QComboBox, QLabel, QLineEdit, QHBoxLayout, QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox

from opcua import ua

from uawidgets.get_node_dialog import GetNodeDialog


class NewNodeBaseDialog(QDialog):
    def __init__(self, parent, title, server):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)

        self.vlayout = QVBoxLayout(self)
        self.layout = QHBoxLayout()
        self.vlayout.addLayout(self.layout)

        self.layout.addWidget(QLabel("ns:", self))
        
        self.nsComboBox = QComboBox(self)
        uries = server.get_namespace_array()
        for uri in uries:
            self.nsComboBox.addItem(uri)
        self.nsComboBox.setCurrentIndex(len(uries)-1)
        self.layout.addWidget(self.nsComboBox)

        self.layout.addWidget(QLabel("Name:", self))
        self.nameLabel = QLineEdit(self)
        self.nameLabel.setText("NoName")
        self.layout.addWidget(self.nameLabel)

        self.nodeidCheckBox = QCheckBox("Auto NodeId", self)
        self.nodeidCheckBox.setChecked(True)
        self.nodeidCheckBox.stateChanged.connect(self._show_nodeid)
        self.layout.addWidget(self.nodeidCheckBox)
        self.nodeidLineEdit = QLineEdit(self)
        self.nodeidLineEdit.setText("ns=3;i=20000")
        self.layout.addWidget(self.nodeidLineEdit)
        self.nodeidLineEdit.hide()


        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.vlayout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _show_nodeid(self, val):
        if val:
            self.nodeidLineEdit.hide()
        else:
            self.nodeidLineEdit.show()
        self.adjustSize()

    def get_ns_and_name(self):
        args = []
        ns = self.nsComboBox.currentIndex()
        name = self.nameLabel.text()
        if self.nodeidCheckBox.isChecked():
            args.append(ns)
            args.append(name)
        else:
            nodeid = ua.NodeId.from_string(self.nodeidLineEdit.text())
            args.append(nodeid)
            args.append(ua.QualifiedName(name, ns))
        return args

    def get_args(self):
        args = self.get_ns_and_name()
        print("NewNodeBaseDialog returns:", args)
        return args 

    @classmethod
    def getArgs(cls, parent, title, server, *args, **kwargs):
        dialog = cls(parent, title, server, *args, **kwargs)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.get_args(), True
        else:
            return [], False


class NewUaObjectDialog(NewNodeBaseDialog):
    def __init__(self, parent, title, server, node_type):
        NewNodeBaseDialog.__init__(self, parent, title, server)

        self.start_node_type = node_type
        self.node_type = node_type

        name = self.node_type.get_browse_name().to_string()
        self.objectTypeButton = QPushButton(name, self)
        self.objectTypeButton.clicked.connect(self._get_node_type)
        self.layout.addWidget(self.objectTypeButton)
        
    def _get_node_type(self):
        node, ok = GetNodeDialog.getNode(self, self.start_node_type)
        if ok:
            self.node_type = node
            self.objectTypeButton.setText(node.get_browse_name().to_string())

    def get_args(self):
        args = self.get_ns_and_name()
        args.append(self.node_type)
        print("NewUaObject:", args)
        return args


class NewUaVariableDialog(NewNodeBaseDialog):
    def __init__(self, parent, title, server, default_value):
        NewNodeBaseDialog.__init__(self, parent, title, server)

        self.valLineEdit = QLineEdit(self)
        self.valLineEdit.setText(str(default_value))
        self.layout.addWidget(self.valLineEdit)

        self.vtypeComboBox = QComboBox(self)
        vtypes = [vt.name for vt in ua.VariantType]
        for vtype in vtypes:
            self.vtypeComboBox.addItem(vtype)
        self.vtypeComboBox.setCurrentText("Float")
        self.layout.addWidget(self.vtypeComboBox)

        self.dtCheckBox = QCheckBox("Auto data type", self)
        self.dtCheckBox.setChecked(True)
        self.dtCheckBox.stateChanged.connect(self._show_data_type)
        self.layout.addWidget(self.dtCheckBox)
        self.original_data_type = server.get_node(ua.ObjectIds.BaseDataType)
        self.data_type = self.original_data_type
        name = self.data_type.get_browse_name().to_string()
        self.dataTypeButton = QPushButton(name, self)
        self.dataTypeButton.clicked.connect(self._get_data_type)
        self.layout.addWidget(self.dataTypeButton)
        self.dataTypeButton.hide()

    def _show_data_type(self, val):
        if val:
            self.dataTypeButton.hide()
        else:
            self.dataTypeButton.show()
        self.adjustSize()

    def _get_data_type(self):
        node, ok = GetNodeDialog.getNode(self, self.original_data_type)
        print("GET NODE", node, ok)
        if ok:
            self.data_type = node
            self.dataTypeButton.setText(node.get_browse_name().to_string())

    def get_args(self):
        args = self.get_ns_and_name()
        args.append(self.valLineEdit.text())
        args.append(getattr(ua.VariantType, self.vtypeComboBox.currentText()))
        if self.dtCheckBox.isChecked():
            args.append(None)
        else:
            args.append(self.data_type.nodeid)
        print("NewUaVariable returns:", args)
        return args



