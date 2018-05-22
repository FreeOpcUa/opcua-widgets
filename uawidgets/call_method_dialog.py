from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QPushButton, QComboBox, QLabel, QLineEdit, QHBoxLayout, QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox, QFrame

from opcua.common.ua_utils import val_to_string, string_to_variant, data_type_to_variant_type, data_type_to_string
from opcua.common.methods import call_method_full
from opcua import ua


class CallMethodDialog(QDialog):
    def __init__(self, parent, server, node):
        QDialog.__init__(self, parent)
        self.setWindowTitle("UA Method Call")
        self.server = server
        self.node = node

        self.vlayout = QVBoxLayout(self)
        self.layout = QHBoxLayout()
        self.vlayout.addLayout(self.layout)
        self.inputs = []
        self.outputs = []

        self.vlayout.addWidget(QLabel("Input Arguments:", self))
        try:
            inputs = node.get_child("0:InputArguments")
            args = inputs.get_value()
            for arg in args:
                self._add_input(arg)
        except ua.UaError as ex:
            print(ex)

        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)
        layout.addWidget(QLabel("Result:", self))
        self.result_label = QLabel("None")
        layout.addWidget(self.result_label)

        self.vlayout.addWidget(QLabel("Output Arguments:", self))
        try:
            outputs = node.get_child("0:OutputArguments")
            args = outputs.get_value()
            for arg in args:
                self._add_output(arg)
        except ua.UaError as ex:
            print(ex)

        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)
        layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        call_button = QPushButton("Call Method")
        call_button.clicked.connect(self.call)
        layout.addWidget(call_button)
    
    def call(self):
        try:
            self._call()
        except Exception as ex:
            self.result_label.setText(str(ex))

    def _call(self):
        parent = self.node.get_parent()
        args = []
        for inp in self.inputs:
            val = string_to_variant(inp.text(), data_type_to_variant_type(inp.data_type))
            args.append(val)

        result = call_method_full(parent, self.node, *args)
        self.result_label.setText(str(result.StatusCode))

        for idx, res in enumerate(result.OutputArguments):
            self.outputs[idx].setText(val_to_string(res))

    def _add_input(self, arg):
        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)
        layout.addWidget(QLabel("Name:{}".format(arg.Name), self))
        layout.addWidget(QLabel("Data type:{}".format(data_type_to_string(arg.DataType)), self))
        layout.addWidget(QLabel("Description:{}".format(arg.Description.Text), self))
        lineedit = QLineEdit(self)
        lineedit.data_type = self.server.get_node(arg.DataType)
        self.inputs.append(lineedit)
        layout.addWidget(lineedit)

    def _add_output(self, arg):
        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)
        layout.addWidget(QLabel("Data Type: {}".format(data_type_to_string(arg.DataType))))
        layout.addWidget(QLabel("Value:"))
        label = QLabel("", self)
        self.outputs.append(label)
        layout.addWidget(label)
