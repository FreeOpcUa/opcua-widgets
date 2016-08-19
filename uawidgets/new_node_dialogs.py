from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QPushButton, QComboBox, QLabel, QLineEdit, QHBoxLayout, QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox

from opcua import ua

from uawidgets.get_node_dialog import GetNodeButton


class NewNodeBaseDialog(QDialog):
    def __init__(self, parent, title, server):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.settings = QSettings()

        self.vlayout = QVBoxLayout(self)
        self.layout = QHBoxLayout()
        self.vlayout.addLayout(self.layout)

        self.layout.addWidget(QLabel("ns:", self))
        
        self.nsComboBox = QComboBox(self)
        uries = server.get_namespace_array()
        for uri in uries:
            self.nsComboBox.addItem(uri)
        nsidx = int(self.settings.value("last_namespace", len(uries)-1))
        if nsidx > len(uries)-1:
            nsidx = len(uries)-1
        self.nsComboBox.setCurrentIndex(nsidx)
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
        self.nodeidLineEdit.setText("ns={};i=20000".format(nsidx))
        self.layout.addWidget(self.nodeidLineEdit)
        self.nodeidLineEdit.hide()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.vlayout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.accepted.connect(self._store_state)
        self.buttons.rejected.connect(self.reject)

    def _store_state(self):
        print("STORE")
        self.settings.setValue("last_namespace", self.nsComboBox.currentIndex())

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
    def __init__(self, parent, title, server, default_node_type, current_node_type=None):
        NewNodeBaseDialog.__init__(self, parent, title, server)

        if current_node_type is None:
            current_node_type = default_node_type

        self.objectTypeButton = GetNodeButton(self, current_node_type, default_node_type)
        self.objectTypeButton.clicked.connect(self._get_node_type)
        self.layout.addWidget(self.objectTypeButton)

    def get_args(self):
        args = self.get_ns_and_name()
        args.append(self.objectTypeButton.get_node())
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
        base_data_type = server.get_node(ua.ObjectIds.BaseDataType)
        self.dataTypeButton = GetNodeButton(self, base_data_type)
        self.layout.addWidget(self.dataTypeButton)
        self.dataTypeButton.hide()

    def _show_data_type(self, val):
        if val:
            self.dataTypeButton.hide()
        else:
            self.dataTypeButton.show()
        self.adjustSize()

    def get_args(self):
        args = self.get_ns_and_name()
        args.append(self.valLineEdit.text())
        args.append(getattr(ua.VariantType, self.vtypeComboBox.currentText()))
        if self.dtCheckBox.isChecked():
            args.append(None)
        else:
            args.append(self.dataTypeButton.get_node())
        print("NewUaVariable returns:", args)
        return args



