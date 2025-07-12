import streamlit as st
from fpdf import FPDF, XPos, YPos
from datetime import datetime, date
import pandas as pd
import plotly.graph_objects as go
import io
import os
from PIL import Image
import arabic_reshaper
from bidi.algorithm import get_display
import plotly.io as pio

# --- Constants ---
FONT_NAME = "Amiri-Regular.ttf"
COVER_IMAGE = "cover_page.png"
A4_WIDTH = 210
A4_HEIGHT = 297
# --- AESTHETIC IMPROVEMENT ---
ACCENT_COLOR = (41, 128, 185) # A professional blue color
LINE_COLOR = (224, 224, 224) # A light gray for separator lines
TITLE_COLOR = (44, 62, 80) # A dark slate color for titles
KPI_TEXT_COLOR = (93, 109, 126) # A gray for KPI labels

class PDFReporter(FPDF):
    """
    A class to generate professional, multi-page PDF reports with full Arabic support,
    custom backgrounds, headers, and footers, using a local font file.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_path = FONT_NAME
        self.font_loaded = False
        self._setup_fonts()
        self.processed_background = None
        if os.path.exists(COVER_IMAGE):
            self._prepare_background_image()

    def _setup_fonts(self):
        if not os.path.exists(self.font_path):
            st.error(f"Font file not found! Please make sure '{self.font_path}' is in the root folder of the project.")
            self.font_loaded = False
            return
        try:
            self.add_font("Amiri", "", self.font_path, uni=True)
            self.font_loaded = True
        except Exception as e:
            st.error(f"FPDF error when adding font '{self.font_path}': {e}")
            self.font_loaded = False

    def _prepare_background_image(self):
        try:
            img = Image.open(COVER_IMAGE).convert("RGBA")
            background = Image.new("RGBA", img.size, (255, 255, 255))
            alpha = img.getchannel('A').point(lambda i: i * 0.5)
            img.putalpha(alpha)
            background.paste(img, (0, 0), img)
            buffer = io.BytesIO()
            background.convert("RGB").save(buffer, format="PNG")
            buffer.seek(0)
            self.processed_background = buffer
        except Exception as e:
            st.error(f"Could not process background image: {e}")
            self.processed_background = None

    def add_page_with_background(self):
        """Adds a new page and applies the background if it exists."""
        super().add_page()
        if self.processed_background and self.page_no() == 1:
            self.image(self.processed_background, 0, 0, w=A4_WIDTH, h=A4_HEIGHT)

    def _process_text(self, text):
        if not self.font_loaded: return str(text)
        if text is None: return ""
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)

    def set_font(self, family, style="", size=0):
        if self.font_loaded and family.lower() == "amiri":
            super().set_font(family, style, size)
        else:
            super().set_font("helvetica", style, size)

    def footer(self):
        if not self.font_loaded: return
        self.set_y(-15)
        self.set_font("Amiri", "", 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"{self.page_no()}", align="C")
        self.set_y(-15)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.cell(0, 10, self._process_text(f"تقرير ماراثون القراءة - {today_str}"), align="R")

    def _get_drawable_width(self):
        return self.w - self.l_margin - self.r_margin

    def _style_figure_for_arabic(self, fig: go.Figure):
        if not self.font_loaded: return fig
        fig.update_layout(
            font=dict(family="Amiri", size=12, color="black"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(250,250,250,0.8)',
            title=dict(font=dict(family="Amiri", size=18, color=TITLE_COLOR), x=0.5, pad=dict(b=15)),
            xaxis=dict(title=dict(font=dict(family="Amiri", size=14)), tickfont=dict(family="Amiri", size=12), showgrid=True, gridcolor="lightgray", gridwidth=0.5),
            yaxis=dict(title=dict(font=dict(family="Amiri", size=14)), tickfont=dict(family="Amiri", size=12), showgrid=True, gridcolor="lightgray", gridwidth=0.5),
            margin=dict(l=60, r=60, t=80, b=60)
        )
        return fig

    def add_plot(self, fig: go.Figure, width_percent=90):
        if not self.font_loaded or not fig: return None, 0
        styled_fig = self._style_figure_for_arabic(fig)
        pio.kaleido.chromium_args = "--no-sandbox"
        img_bytes = styled_fig.to_image(format="png", scale=2, width=800, height=500)

        img_file = io.BytesIO(img_bytes)
        pil_img = Image.open(img_file)
        aspect_ratio = pil_img.height / pil_img.width
        page_width = self._get_drawable_width()
        img_width_mm = page_width * (width_percent / 100)
        img_height_mm = img_width_mm * aspect_ratio
        
        if self.get_y() + img_height_mm > (self.h - self.b_margin):
            self.add_page_with_background()
            
        x_pos = (self.w - img_width_mm) / 2
        img_file.seek(0)
        self.image(img_file, x=x_pos, y=self.get_y(), w=img_width_mm)
        self.set_y(self.get_y() + img_height_mm)
        return img_height_mm

    def add_section_title(self, title):
        """Adds a styled title for a new section."""
        self.ln(10)
        self.set_font("Amiri", "", 22)
        self.set_text_color(*TITLE_COLOR)
        self.cell(0, 12, self._process_text(title), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT_COLOR)
        self.line(self.w - self.r_margin - 60, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(8)

    def add_kpi_grid(self, kpis: dict):
        """Adds a 3x2 grid of Key Performance Indicators."""
        if not kpis: return
        
        col_width = self._get_drawable_width() / 3
        cell_height = 30
        icon_size = 18
        
        kpi_list = list(kpis.items())
        
        for i in range(0, len(kpi_list), 3):
            self.set_x(self.l_margin)
            for j in range(3):
                if i + j < len(kpi_list):
                    label, (value, icon) = kpi_list[i+j]
                    x = self.get_x()
                    y = self.get_y()
                    
                    self.rect(x, y, col_width - 5, cell_height, 'F')
                    
                    # Icon
                    # --- FIX: Use the Amiri font for icons (emojis) ---
                    self.set_font("Amiri", "", icon_size)
                    self.set_xy(x + 5, y + (cell_height / 2) - (icon_size/2) + 2)
                    self.cell(icon_size, icon_size, self._process_text(icon))

                    # Text
                    self.set_font("Amiri", "", 16)
                    self.set_text_color(*TITLE_COLOR)
                    self.set_xy(x + icon_size + 10, y + 5)
                    self.cell(col_width - icon_size - 20, 10, self._process_text(str(value)), align="R")

                    self.set_font("Amiri", "", 11)
                    self.set_text_color(*KPI_TEXT_COLOR)
                    self.set_xy(x + icon_size + 10, y + 15)
                    self.cell(col_width - icon_size - 20, 10, self._process_text(label), align="R")

                    self.set_x(x + col_width)
            self.ln(cell_height + 5)

    def add_hall_of_fame_grid(self, heroes: dict):
        """Adds a 4x2 grid for the Hall of Fame."""
        if not heroes: return
        
        col_width = self._get_drawable_width() / 4
        cell_height = 35
        
        heroes_list = list(heroes.items())

        for i in range(0, len(heroes_list), 4):
            self.set_x(self.l_margin)
            for j in range(4):
                if i + j < len(heroes_list):
                    title, (name, value) = heroes_list[i+j]
                    x = self.get_x()
                    y = self.get_y()
                    
                    self.rect(x, y, col_width - 4, cell_height, 'F')

                    # Title
                    self.set_font("Amiri", "", 12)
                    self.set_text_color(*ACCENT_COLOR)
                    self.set_xy(x + 2, y + 4)
                    self.multi_cell(col_width - 8, 8, self._process_text(title), align="C")

                    # Name
                    self.set_font("Amiri", "B", 14)
                    self.set_text_color(*TITLE_COLOR)
                    self.set_xy(x + 2, y + 15)
                    self.multi_cell(col_width - 8, 8, self._process_text(name), align="C")

                    # Value
                    self.set_font("Amiri", "", 10)
                    self.set_text_color(*KPI_TEXT_COLOR)
                    self.set_xy(x + 2, y + 25)
                    self.multi_cell(col_width - 8, 8, self._process_text(value), align="C")
                    
                    self.set_x(x + col_width)
            self.ln(cell_height + 5)

    def add_charts_page(self, charts: dict):
        """Adds a page for each chart provided."""
        for title, fig in charts.items():
            if fig is not None:
                self.add_page_with_background()
                self.add_section_title(title)
                self.add_plot(fig)

    def add_dashboard_report(self, data: dict):
        """Generates a full dashboard report that mirrors the web page."""
        if not self.font_loaded: return
        
        # Page 1: Title and KPIs
        self.add_page_with_background()
        self.set_font("Amiri", "", 32)
        self.set_text_color(*TITLE_COLOR)
        self.cell(0, 25, self._process_text("تقرير لوحة التحكم العامة"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

        self.add_section_title("📊 مؤشرات الأداء الرئيسية")
        self.set_fill_color(245, 245, 245)
        self.add_kpi_grid(data.get('kpis', {}))

        # Page 2: Hall of Fame
        self.add_page_with_background()
        self.add_section_title("🌟 لوحة شرف الأبطال")
        self.set_fill_color(248, 249, 250)
        self.add_hall_of_fame_grid(data.get('heroes', {}))
        
        # Subsequent Pages: Charts
        self.add_charts_page(data.get('charts', {}))

    def add_challenge_report(self, data: dict):
        if not self.font_loaded: return
        self.add_challenge_title_page(
            title=data.get('title', ''), author=data.get('author', ''),
            period=data.get('period', ''), duration=data.get('duration', 0)
        )
        self.add_participants_page(
            all_participants=data.get('all_participants', []),
            finishers=data.get('finishers', []), attendees=data.get('attendees', [])
        )

    def add_challenge_title_page(self, title, author, period, duration):
        if not self.font_loaded: return
        self.add_page_with_background()
        drawable_width = self._get_drawable_width()
        content_height = (15 * 2) + 15 + (10 * 3)
        self.set_y((A4_HEIGHT - content_height) / 2)
        self.set_font("Amiri", "", 28)
        self.set_text_color(*ACCENT_COLOR)
        self.multi_cell(drawable_width, 15, self._process_text(f"تقرير تحدي:\n{title}"), align="C")
        self.ln(15)
        self.set_font("Amiri", "", 16)
        self.set_text_color(80, 80, 80)
        self.multi_cell(drawable_width, 10, self._process_text(f"تأليف: {author}"), align="C")
        self.multi_cell(drawable_width, 10, self._process_text(f"الفترة: {period}"), align="C")
        self.multi_cell(drawable_width, 10, self._process_text(f"مدة التحدي: {duration} يوم"), align="C")

    def add_participants_page(self, all_participants, finishers, attendees):
        if not self.font_loaded: return
        self.add_page_with_background()
        self.add_section_title("المشاركون في التحدي")
        page_w = self._get_drawable_width()
        col_w = page_w / 3
        header_h, line_h = 10, 8
        self.set_font("Amiri", "", 14)
        self.set_fill_color(240, 240, 240)
        self.cell(col_w, header_h, self._process_text("من حضروا النقاش"), border='B', align="C", fill=True)
        self.cell(col_w, header_h, self._process_text("من أنهوا الكتاب"), border='B', align="C", fill=True)
        self.cell(col_w, header_h, self._process_text("جميع المشاركين"), border='B', align="C", fill=True)
        self.ln(header_h)
        self.set_font("Amiri", "", 11)
        self.set_text_color(50,50,50)
        max_len = max(len(all_participants), len(finishers), len(attendees))
        for i in range(max_len):
            p_name = all_participants[i] if i < len(all_participants) else ""
            f_name = finishers[i] if i < len(finishers) else ""
            a_name = attendees[i] if i < len(attendees) else ""
            self.cell(col_w, line_h, self._process_text(a_name), align="C")
            self.cell(col_w, line_h, self._process_text(f_name), align="C")
            self.cell(col_w, line_h, self._process_text(p_name), align="C")
            self.ln()
