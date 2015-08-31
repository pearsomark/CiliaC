# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'set_limits.ui'
#
# Created: Tue Sep  9 10:59:28 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_DualSpin(object):
    def setupUi(self, DualSpin):
        DualSpin.setObjectName(_fromUtf8("DualSpin"))
        DualSpin.resize(214, 121)
        self.buttonBox = QtGui.QDialogButtonBox(DualSpin)
        self.buttonBox.setGeometry(QtCore.QRect(25, 76, 156, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.spinFrom = QtGui.QSpinBox(DualSpin)
        self.spinFrom.setGeometry(QtCore.QRect(35, 28, 52, 23))
        self.spinFrom.setObjectName(_fromUtf8("spinFrom"))
        self.spinTo = QtGui.QSpinBox(DualSpin)
        self.spinTo.setGeometry(QtCore.QRect(120, 28, 52, 23))
        self.spinTo.setObjectName(_fromUtf8("spinTo"))
        self.labelFrom = QtGui.QLabel(DualSpin)
        self.labelFrom.setGeometry(QtCore.QRect(40, 8, 41, 16))
        self.labelFrom.setObjectName(_fromUtf8("labelFrom"))
        self.labelTo = QtGui.QLabel(DualSpin)
        self.labelTo.setGeometry(QtCore.QRect(125, 8, 36, 16))
        self.labelTo.setObjectName(_fromUtf8("labelTo"))

        self.retranslateUi(DualSpin)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DualSpin.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DualSpin.reject)
        QtCore.QMetaObject.connectSlotsByName(DualSpin)

    def retranslateUi(self, DualSpin):
        DualSpin.setWindowTitle(_translate("DualSpin", "Dialog", None))
        self.labelFrom.setText(_translate("DualSpin", "From", None))
        self.labelTo.setText(_translate("DualSpin", "To", None))

