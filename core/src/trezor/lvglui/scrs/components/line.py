from .. import lv, lv_theme


class Line(lv.line):
    def __init__(self, parent, width, height=1, line_color=None) -> None:
        super().__init__(parent)
        if line_color is None:
            line_color = lv_theme.CONT_ITEM_BLINE
        line_points = [{"x": 0, "y": 0}, {"x": width, "y": 0}]
        style_line = lv.style_t()
        style_line.init()
        style_line.set_line_color(line_color)
        style_line.set_line_width(height)
        self.remove_style_all()
        self.set_points(line_points, 2)
        self.add_style(style_line, 0)
