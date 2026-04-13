import sys
from PyQt5.QtWidgets import QApplication
from ui.app import DevScopeUi

app = QApplication(sys.argv)

window = DevScopeUi()
window.show()

sys.exit(app.exec_())
