from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QPushButton, QComboBox, QLabel, QLineEdit, QHBoxLayout, QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox, QFrame

from opcua import ua
from opcua.common.ua_utils import string_to_variant
from opcua.common.ua_utils import dtype_to_vtype

from uawidgets.get_node_dialog import GetNodeButton


class NewNodeBaseDialog(QDialog):
    def __init__(self, parent, title, server):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.settings = QSettings()
        self.server = server

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
        self.nameLabel.setMinimumWidth(120)
        self.nameLabel.setText("NoName")
        self.layout.addWidget(self.nameLabel)
        self.nodeidCheckBox = QCheckBox("Auto NodeId", self)
        self.nodeidCheckBox.stateChanged.connect(self._show_nodeid)
        self.layout.addWidget(self.nodeidCheckBox)
        self.nodeidLineEdit = QLineEdit(self)
        self.nodeidLineEdit.setMinimumWidth(80)
        self.nodeidLineEdit.setText(self.settings.value("last_nodeid_prefix", "ns={};i=20000".format(nsidx)))
        self.layout.addWidget(self.nodeidLineEdit)

        # restore check box state from settings
        if self.settings.value("last_node_widget_vis", False) == "true":
            self.nodeidCheckBox.setChecked(False)
            self.nodeidLineEdit.show()
        else:
            self.nodeidCheckBox.setChecked(True)
            self.nodeidLineEdit.hide()

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.vlayout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.accepted.connect(self._store_state)
        self.buttons.rejected.connect(self.reject)

    def _store_state(self):
        self.settings.setValue("last_namespace", self.nsComboBox.currentIndex())
        self.settings.setValue("last_node_widget_vis", not self.nodeidCheckBox.isChecked())
        ns_nt = self.nodeidLineEdit.text().split(';')
        self.settings.setValue("last_nodeid_prefix", ns_nt[0] + ';' + ns_nt[1][0:2])

    def _show_nodeid(self, val):
        if val:
            self.nodeidLineEdit.hide()
        else:
            self.nodeidLineEdit.show()
        self.adjustSize()

    def get_nodeid_and_bname(self):
        ns = self.nsComboBox.currentIndex()
        name = self.nameLabel.text()
        bname = ua.QualifiedName(name, ns)
        if self.nodeidCheckBox.isChecked():
            nodeid = ua.NodeId(namespaceidx=ns)
        else:
            nodeid = ua.NodeId.from_string(self.nodeidLineEdit.text())
        return nodeid, bname

    def get_args(self):
        nodeid, bname = self.get_nodeid_and_bname()
        return nodeid, bname

    @classmethod
    def getArgs(cls, parent, title, server, *args, **kwargs):
        dialog = cls(parent, title, server, *args, **kwargs)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.get_args(), True
        else:
            return [], False


class NewUaObjectDialog(NewNodeBaseDialog):
    def __init__(self, parent, title, server, base_node_type, current_node_type=None):
        NewNodeBaseDialog.__init__(self, parent, title, server)

        if current_node_type is None:
            current_node_type = base_node_type

        self.objectTypeButton = GetNodeButton(self, current_node_type, base_node_type)
        self.layout.addWidget(self.objectTypeButton)

    def get_args(self):
        nodeid, bname = self.get_nodeid_and_bname()
        otype = self.objectTypeButton.get_node()
        return nodeid, bname, otype


class NewUaVariableDialog(NewNodeBaseDialog):
    def __init__(self, parent, title, server, default_value):
        NewNodeBaseDialog.__init__(self, parent, title, server)

        self.valLineEdit = QLineEdit(self)
        self.valLineEdit.setText(str(default_value))
        self.layout.addWidget(self.valLineEdit)

        base_data_type = server.get_node(ua.ObjectIds.BaseDataType)
        dtype_str = self.settings.value("last_datatype", None)
        if dtype_str is None:
            current_type = server.get_node(ua.ObjectIds.Float)
        else:
            current_type = server.get_node(ua.NodeId.from_string(dtype_str))
        self.dataTypeButton = GetNodeButton(self, current_type, base_data_type)
        self.layout.addWidget(self.dataTypeButton)

    def get_args(self):
        nodeid, bname = self.get_nodeid_and_bname()
        dtype = self.dataTypeButton.get_node()
        self.settings.setValue("last_datatype", dtype.nodeid.to_string())
        vtype = dtype_to_vtype(self.server, dtype)
        var = string_to_variant(self.valLineEdit.text(), vtype)
        return nodeid, bname, var, vtype, dtype.nodeid


class NewUaMethodDialog(NewNodeBaseDialog):
    def __init__(self, parent, title, server):
        NewNodeBaseDialog.__init__(self, parent, title, server)
        # FIXME current temporary UI is fixed; should be changed to listview or treeview object

        self.widgets = []

        self.inplayout = QVBoxLayout(self)
        self.vlayout.addLayout(self.inplayout)
        self.inplayout.addLayout(self.add_header("Inputs"))
        self.inplayout.addLayout(self.add_row("input"))
        self.inplayout.addLayout(self.add_row("input"))
        self.inplayout.addLayout(self.add_row("input"))

        self.ouplayout = QVBoxLayout(self)
        self.vlayout.addLayout(self.ouplayout)
        self.ouplayout.addLayout(self.add_header("Outputs"))
        self.ouplayout.addLayout(self.add_row("output"))
        self.ouplayout.addLayout(self.add_row("output"))
        self.ouplayout.addLayout(self.add_row("output"))

    def get_args(self):
        nodeid, bname = self.get_nodeid_and_bname()

        input_args = []
        output_args = []

        for row in self.widgets:
            dtype = row[3].get_node()
            name = row[1].text()
            description = row[2].text()

            if name != "":
                # FIXME arguments need to be created from dynamaic UA
                method_arg = ua.Argument()
                method_arg.Name = name
                method_arg.DataType = dtype.nodeid
                method_arg.ValueRank = -1
                method_arg.ArrayDimensions = []
                method_arg.Description = ua.LocalizedText(description)

                if row[0] == 'input':
                    input_args.append(method_arg)
                else:
                    output_args.append(method_arg)

        # callback is None, this cannot be set from modeler
        return nodeid, bname, None, input_args, output_args

    def add_row(self, mode):
        rowlayout = QHBoxLayout(self)

        rowlayout.addWidget(QLabel("Arg Name:", self))
        argNameLabel = QLineEdit(self)
        argNameLabel.setText("")
        rowlayout.addWidget(argNameLabel)

        rowlayout.addWidget(QLabel("Description:", self))
        argDescLabel = QLineEdit(self)
        argDescLabel.setText("")
        rowlayout.addWidget(argDescLabel)

        base_data_type = self.server.get_node(ua.ObjectIds.BaseDataType)
        dtype_str = self.settings.value("last_datatype", None)
        if dtype_str is None:
            current_type = self.server.get_node(ua.ObjectIds.Float)
        else:
            current_type = self.server.get_node(ua.NodeId.from_string(dtype_str))
        dataTypeButton = GetNodeButton(self, current_type, base_data_type)
        rowlayout.addWidget(dataTypeButton)

        self.widgets.append([mode, argNameLabel, argDescLabel, dataTypeButton])
        return rowlayout

    def add_header(self, header):
        header_row = QHBoxLayout(self)
        header_row.addWidget(QLabel(header, self))
        header_row.addWidget(self.add_h_line())
        # header_row.addWidget(QLabel("+ button", self))  # FIXME this needs to be a button which triggers add_row()
        return header_row

    def add_h_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line



