"""
JetBrains New UI 风格样式定义
基于 IntelliJ IDEA 2024.2+ New UI Dark Theme
"""

# 颜色定义 - 来自 expUI_dark.theme.json
class Colors:
    """JetBrains New UI Dark Theme 颜色"""

    # 灰度色阶
    GRAY1 = "#1E1F22"   # 最深背景（编辑器/面板背景）
    GRAY2 = "#2B2D30"   # 主要背景
    GRAY3 = "#393B40"   # 悬停/选中背景
    GRAY4 = "#43454A"   # 分隔线/次要边框
    GRAY5 = "#4E5157"   # 按钮边框
    GRAY6 = "#5A5D63"   # 禁用文本
    GRAY7 = "#6F737A"   # 次要文本/提示
    GRAY8 = "#868A91"
    GRAY9 = "#9DA0A8"
    GRAY10 = "#B4B8BF"
    GRAY11 = "#CED0D6"
    GRAY12 = "#DFE1E5"  # 主要文本
    GRAY13 = "#F0F1F2"
    GRAY14 = "#FFFFFF"  # 高亮/按钮文本

    # 蓝色系 - 主色调
    BLUE1 = "#25324D"
    BLUE2 = "#2E436E"   # 选中背景
    BLUE3 = "#35538F"
    BLUE4 = "#375FAD"
    BLUE5 = "#366ACE"
    BLUE6 = "#3574F0"   # 主色调（默认按钮、焦点）
    BLUE7 = "#467FF2"
    BLUE8 = "#548AF7"
    BLUE9 = "#6B9BFA"   # 链接
    BLUE10 = "#83ACFC"
    BLUE11 = "#99BBFF"

    # 绿色系 - 成功状态
    GREEN5 = "#4E8052"
    GREEN6 = "#57965C"
    GREEN7 = "#5FAD65"

    # 红色系 - 错误/危险
    RED5 = "#9C4E4E"
    RED6 = "#BD5757"
    RED7 = "#DB5C5C"

    # 黄色系 - 警告
    YELLOW5 = "#BA9752"
    YELLOW6 = "#D6AE58"
    YELLOW7 = "#F2C55C"

    # 橙色系 - 当前位置指示
    ORANGE6 = "#E08855"
    ORANGE7 = "#E5986C"
    ORANGE8 = "#F0AC81"


# 组件尺寸 - 来自 JetBrains UI Guidelines
class Sizes:
    """组件尺寸规范"""

    # 按钮
    BUTTON_MIN_WIDTH = 72
    BUTTON_HEIGHT = 28
    BUTTON_RADIUS = 8

    # 组件通用
    COMPONENT_RADIUS = 8

    # 列表
    LIST_ROW_HEIGHT = 24

    # 间距
    SPACING_SMALL = 4
    SPACING_MEDIUM = 8
    SPACING_LARGE = 12
    SPACING_XLARGE = 16


def get_stylesheet() -> str:
    """
    获取完整的 QSS 样式表
    基于 JetBrains New UI Dark Theme
    """
    return f"""
    /* ========== 全局样式 ========== */
    QWidget {{
        background-color: {Colors.GRAY2};
        color: {Colors.GRAY12};
        font-family: "Inter", -apple-system, "Segoe UI", sans-serif;
        font-size: 13px;
    }}

    QMainWindow {{
        background-color: {Colors.GRAY1};
    }}

    /* ========== 按钮 ========== */
    QPushButton {{
        background-color: {Colors.GRAY3};
        border: 1px solid {Colors.GRAY5};
        border-radius: {Sizes.BUTTON_RADIUS}px;
        padding: 4px 14px;
        min-width: {Sizes.BUTTON_MIN_WIDTH}px;
        min-height: {Sizes.BUTTON_HEIGHT}px;
        color: {Colors.GRAY12};
    }}

    QPushButton:hover {{
        background-color: {Colors.GRAY4};
        border-color: {Colors.GRAY6};
    }}

    QPushButton:pressed {{
        background-color: {Colors.GRAY5};
    }}

    QPushButton:disabled {{
        background-color: {Colors.GRAY2};
        border-color: {Colors.GRAY4};
        color: {Colors.GRAY6};
    }}

    /* 默认/主要按钮 */
    QPushButton[default="true"], QPushButton#primaryButton {{
        background-color: {Colors.BLUE6};
        border-color: {Colors.BLUE6};
        color: {Colors.GRAY14};
    }}

    QPushButton[default="true"]:hover, QPushButton#primaryButton:hover {{
        background-color: {Colors.BLUE7};
        border-color: {Colors.BLUE7};
    }}

    QPushButton[default="true"]:pressed, QPushButton#primaryButton:pressed {{
        background-color: {Colors.BLUE5};
    }}

    /* 扁平按钮 */
    QPushButton:flat {{
        background-color: transparent;
        border: none;
    }}

    QPushButton:flat:hover {{
        background-color: {Colors.GRAY3};
    }}

    /* ========== 输入框 ========== */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {Colors.GRAY1};
        border: 1px solid {Colors.GRAY5};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        padding: 4px 8px;
        min-height: 24px;
        color: {Colors.GRAY12};
        selection-background-color: {Colors.BLUE2};
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {Colors.BLUE6};
    }}

    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: {Colors.GRAY2};
        border-color: {Colors.GRAY4};
        color: {Colors.GRAY6};
    }}

    /* ========== 下拉框 ========== */
    QComboBox {{
        background-color: {Colors.GRAY3};
        border: 1px solid {Colors.GRAY5};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        padding: 4px 8px;
        min-height: 24px;
        color: {Colors.GRAY12};
    }}

    QComboBox:hover {{
        border-color: {Colors.GRAY6};
    }}

    QComboBox:focus {{
        border-color: {Colors.BLUE6};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {Colors.GRAY7};
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {Colors.GRAY2};
        border: 1px solid {Colors.GRAY4};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        selection-background-color: {Colors.BLUE2};
        outline: none;
    }}

    /* ========== 分组框 ========== */
    QGroupBox {{
        background-color: {Colors.GRAY2};
        border: 1px solid {Colors.GRAY4};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        margin-top: 8px;
        padding-top: 8px;
        font-weight: 500;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 4px;
        color: {Colors.GRAY12};
    }}

    /* ========== 标签 ========== */
    QLabel {{
        background-color: transparent;
        color: {Colors.GRAY12};
    }}

    QLabel[secondary="true"] {{
        color: {Colors.GRAY7};
    }}

    /* ========== 滚动条 ========== */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {Colors.GRAY5};
        border-radius: 5px;
        min-height: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {Colors.GRAY6};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {Colors.GRAY5};
        border-radius: 5px;
        min-width: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {Colors.GRAY6};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ========== 表格 ========== */
    QTableWidget, QTableView {{
        background-color: {Colors.GRAY1};
        alternate-background-color: {Colors.GRAY2};
        border: 1px solid {Colors.GRAY4};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        gridline-color: {Colors.GRAY3};
        selection-background-color: {Colors.BLUE2};
    }}

    QTableWidget::item, QTableView::item {{
        padding: 4px 8px;
        border: none;
    }}

    QTableWidget::item:selected, QTableView::item:selected {{
        background-color: {Colors.BLUE2};
    }}

    QHeaderView::section {{
        background-color: {Colors.GRAY2};
        color: {Colors.GRAY12};
        border: none;
        border-bottom: 1px solid {Colors.GRAY4};
        padding: 6px 8px;
        font-weight: 500;
    }}

    /* ========== 文本编辑 ========== */
    QTextEdit {{
        background-color: {Colors.GRAY1};
        border: 1px solid {Colors.GRAY4};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        color: {Colors.GRAY12};
        selection-background-color: {Colors.BLUE2};
    }}

    /* ========== 进度条 ========== */
    QProgressBar {{
        background-color: {Colors.GRAY3};
        border: none;
        border-radius: 4px;
        height: 4px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {Colors.BLUE6};
        border-radius: 4px;
    }}

    /* ========== 滑块 ========== */
    QSlider::groove:horizontal {{
        background-color: {Colors.GRAY4};
        height: 4px;
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background-color: {Colors.GRAY12};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: {Colors.GRAY14};
    }}

    QSlider::sub-page:horizontal {{
        background-color: {Colors.BLUE6};
        border-radius: 2px;
    }}

    /* ========== 菜单 ========== */
    QMenuBar {{
        background-color: {Colors.GRAY1};
        border-bottom: 1px solid {Colors.GRAY3};
        padding: 2px;
    }}

    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }}

    QMenuBar::item:selected {{
        background-color: {Colors.GRAY3};
    }}

    QMenu {{
        background-color: {Colors.GRAY2};
        border: 1px solid {Colors.GRAY4};
        border-radius: {Sizes.COMPONENT_RADIUS}px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 6px 32px 6px 12px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {Colors.BLUE2};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {Colors.GRAY4};
        margin: 4px 8px;
    }}

    /* ========== 工具提示 ========== */
    QToolTip {{
        background-color: {Colors.GRAY3};
        border: 1px solid {Colors.GRAY4};
        border-radius: 4px;
        padding: 4px 8px;
        color: {Colors.GRAY12};
    }}

    /* ========== 分割器 ========== */
    QSplitter::handle {{
        background-color: {Colors.GRAY3};
    }}

    QSplitter::handle:horizontal {{
        width: 1px;
    }}

    QSplitter::handle:vertical {{
        height: 1px;
    }}

    /* ========== 消息框 ========== */
    QMessageBox {{
        background-color: {Colors.GRAY2};
    }}

    QMessageBox QLabel {{
        color: {Colors.GRAY12};
    }}
    """


def get_primary_button_style() -> str:
    """获取主要按钮（蓝色）的内联样式"""
    return f"""
        QPushButton {{
            background-color: {Colors.BLUE6};
            border: 1px solid {Colors.BLUE6};
            border-radius: {Sizes.BUTTON_RADIUS}px;
            padding: 4px 14px;
            min-width: {Sizes.BUTTON_MIN_WIDTH}px;
            min-height: {Sizes.BUTTON_HEIGHT}px;
            color: {Colors.GRAY14};
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {Colors.BLUE7};
            border-color: {Colors.BLUE7};
        }}
        QPushButton:pressed {{
            background-color: {Colors.BLUE5};
        }}
        QPushButton:disabled {{
            background-color: {Colors.GRAY4};
            border-color: {Colors.GRAY4};
            color: {Colors.GRAY6};
        }}
    """
