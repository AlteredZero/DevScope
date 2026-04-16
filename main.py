import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.app import DevScopeUi

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("assets/DevScopeIcon.png"))

window = DevScopeUi()
window.show()

sys.exit(app.exec_())