from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QPushButton, QComboBox, QLabel, QLineEdit, QHBoxLayout, QDialog, QDialogButtonBox, QVBoxLayout, QCheckBox, QFrame

from opcua import ua, Node
from opcua.common.ua_utils import string_to_variant
from opcua.common.ua_utils import data_type_to_variant_type

from uawidgets.get_node_dialog import GetNodeButton


class CallMethodDialog(QDialog):
    def __init__(self, parent, server, node):
        QDialog.__init__(self, parent)
        self.setWindowTitle("UA Method Call")
        self.settings = QSettings()
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
        self.vlayout.addWidget(QLabel("Output", self))
        try:
            outputs = node.get_child("0:OutputArguments")
            args = outputs.get_value()
            for arg in args:
                self._add_output(arg)
        except ua.UaError as ex:
            print(ex)

        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button)
        call_button = QPushButton("Call Method")
        call_button.clicked.connect(self._call)
        layout.addWidget(call_button)

    def _call(self):
        parent = node.get_parent()
        args = []
        for inp in self.inputs:
            pass




    def _add_input(self, arg):
        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)
        layout.addWidget(QLabel("Argument:", self))
        layout.addWidget(QLabel("Name:{}".format(arg.Name), self))
        layout.addWidget(QLabel("Data type:{}".format(arg.DataType), self))
        layout.addWidget(QLabel("Description:{}".format(arg.Description), self))
        lineedit = QLineEdit(self)
        self.inputs.append(lineedit)
        layout.addWidget(lineedit)

    def _add_output(self, arg):
        layout = QHBoxLayout()
        self.vlayout.addLayout(layout)
        layout.addWidget(QLabel("Output:", self))
        label = QLabel("", self)
        self.outputs.append(label)
        layout.addWidget(label)
