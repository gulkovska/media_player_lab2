import sys

from PyQt6.QtWidgets import QApplication

from player import MediaPlayerWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MediaPlayerWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())
