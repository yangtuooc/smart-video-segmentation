"""
GUI 模块入口
使用 JetBrains New UI 风格
"""

import sys


def main():
    """GUI 入口函数"""
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from .main_window import MainWindow
    from .styles import get_stylesheet

    app = QApplication(sys.argv)
    app.setApplicationName("Smart Video Segmenter")

    # 设置默认字体
    font = QFont()
    font.setFamily("Inter")
    font.setPointSize(13)
    app.setFont(font)

    # 应用 JetBrains New UI 风格样式表
    app.setStyleSheet(get_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
