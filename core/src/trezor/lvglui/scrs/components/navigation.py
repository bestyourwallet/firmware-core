from .. import lv, theme_path_png

# from ..widgets.style import StyleWrapper


class Navigation(lv.obj):
    def __init__(
        self,
        parent,
        btn_bg_img: str | None = None,
        nav_btn_align: lv.ALIGN = lv.ALIGN.LEFT_MID,
        align: lv.ALIGN = lv.ALIGN.TOP_LEFT,
        pos: tuple[int, int] = (0, 40),
    ) -> None:
        super().__init__(parent)
        if btn_bg_img is None:
            btn_bg_img = theme_path_png("nav-back")
        self.remove_style_all()
        self.set_size(lv.pct(50), 70)
        self.align(align, pos[0], pos[1])
        # self.add_style(StyleWrapper().pad_all(12), 0)
        # self.nav_btn_align = nav_btn_align
        self.init_nav_btn(btn_bg_img, nav_btn_align, 15)
        # self.add_flag(lv.obj.FLAG.EVENT_BUBBLE)

    def init_nav_btn(self, img_path: str, align, pos_x):
        self.nav_btn = lv.imgbtn(self)
        self.nav_btn.set_size(30, 70)
        self.nav_btn.align(align, pos_x, 0)
        self.nav_btn.set_ext_click_area(200)
        self.nav_btn.add_flag(lv.obj.FLAG.EVENT_BUBBLE)
        self.set_img(img_path)

    def set_img(self, img_path):
        if not hasattr(self, "nav_btn"):
            return
        self.nav_btn.set_style_bg_img_src(img_path, 0)
