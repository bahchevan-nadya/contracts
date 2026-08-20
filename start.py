import sys
from PyQt6.QtWidgets import QApplication
from login import LoginWindow
from main import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    login_window = LoginWindow()

    def on_login_success(user_id):
        login_window.close()
        main_win = MainWindow(user_id=user_id)
        main_win.show()

    login_window.login_success.connect(on_login_success)

    login_window.show()
    sys.exit(app.exec())