import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import PDFPasswordRemover

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("移除PDF密码工具")
    app.setOrganizationName("PDF Tools")
    
    window = PDFPasswordRemover()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()