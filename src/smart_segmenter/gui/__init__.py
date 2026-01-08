"""
GUI 模块入口
使用 PyQtDarkTheme 主题
"""

import sys


def main():
    """GUI 入口函数"""
    from PySide6.QtWidgets import QApplication
    import qdarktheme

    from .main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Smart Video Segmenter")

    # 应用扁平深色主题（JetBrains 风格）
    qdarktheme.setup_theme(
        theme="dark",
        custom_colors={"primary": "#3574F0"},  # JetBrains 蓝
    )

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
