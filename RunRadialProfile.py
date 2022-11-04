import sys
import RadialProfileWindow as rpw

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

def main():
    rpApplication = QApplication(sys.argv) # Create Instance

    mainWindow = rpw.MainWindow()
    widget=QtWidgets.QStackedWidget()
    widget.addWidget(mainWindow)
    widget.setFixedWidth(530)
    widget.setFixedHeight(450)
    widget.show()

    sys.exit(rpApplication.exec())
if __name__=="__main__":
    main()