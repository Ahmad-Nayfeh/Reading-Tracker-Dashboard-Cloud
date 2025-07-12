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

# --- CONSTANTS & STYLING ---
FONT_NAME = "Amiri-Regular.ttf"
COVER_IMAGE = "cover_page.png"
A4_WIDTH = 210
A4_HEIGHT = 297

# --- AESTHETIC IMPROVEMENT ---
ACCENT_COLOR = (41, 128, 185) # A professional blue color (e.g., #2980B9)
LINE_COLOR = (224, 224, 224) # A light gray for separator lines
TITLE_COLOR = (44, 62, 80) # A dark slate color for titles (e.g., #2C3E50)
KPI_TEXT_COLOR = (93, 109, 126) # A gray for KPI labels (e.g., #5D6D7E)
CARD_BACKGROUND_COLOR = (248, 249, 250) # Very light gray for card backgrounds
HERO_ACCENT_COLOR = (231, 76, 60) # An accent red for hero titles (e.g., #E74C3C)

# Plotly colors (RGB string format)
PLOTLY_TITLE_COLOR = f"rgb{TITLE_COLOR}"
PLOTLY_TEXT_COLOR = "rgb(0,0,0)"

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
            # Lower opacity for a more subtle effect
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

    def add_page_with_background(self, use_background=True):
        """Adds a new page and applies the background if it exists and is requested."""
        super().add_page()
        if self.processed_background and use_background:
            try:
                self.image(self.processed_background, 0, 0, w=A4_WIDTH, h=A4_HEIGHT)
            except Exception as e:
                st.warning(f"Could not apply background image: {e}")

    def _process_text(self, text):
        if not self.font_loaded: return str(text)
        if text is None: return ""
        try:
            reshaped_text = arabic_reshaper.reshape(str(text))
            return get_display(reshaped_text)
        except Exception as e:
            st.warning(f"Text processing error: {e}")
            return str(text)

    def set_font(self, family, style="", size=0):
        # Simplified font setting for custom fonts
        if self.font_loaded and isinstance(family, str) and family.lower() == "amiri":
            # The 'B' style for custom fonts often requires a separate bold font file.
            # Sticking to '' (regular) prevents errors if a bold version isn't added.
            super().set_font(family, '', size)
        else:
            super().set_font(family, style, size)

    def footer(self):
        # No footer on the cover page (page 1)
        if not self.font_loaded or self.page_no() == 1: return
        try:
            self.set_y(-15)
            self.set_font("Amiri", "", 10)
            self.set_text_color(128, 128, 128)
            # Page number in the center
            self.cell(0, 10, f"{self.page_no()}", align="C")
            # Report title on the right
            self.set_y(-15)
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.cell(0, 10, self._process_text(f"تقرير ماراثون القراءة - {today_str}"), align="R")
        except Exception as e:
            st.warning(f"Footer error: {e}")

    def _get_drawable_width(self):
        return self.w - self.l_margin - self.r_margin

    def _style_figure_for_arabic(self, fig: go.Figure):
        # This function remains largely the same, it's already well-styled.
        if not self.font_loaded: return fig
        try:
            fig.update_layout(
                font=dict(family="Arial", size=12, color=PLOTLY_TEXT_COLOR),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(250,250,250,0.8)',
                title=dict(font=dict(family="Arial", size=18, color=PLOTLY_TITLE_COLOR), x=0.5, pad=dict(b=15)),
                xaxis=dict(title=dict(font=dict(family="Arial", size=14)), tickfont=dict(family="Arial", size=12), showgrid=True, gridcolor="lightgray"),
                yaxis=dict(title=dict(font=dict(family="Arial", size=14)), tickfont=dict(family="Arial", size=12), showgrid=True, gridcolor="lightgray"),
                margin=dict(l=60, r=60, t=80, b=60)
            )
            return fig
        except Exception as e:
            st.warning(f"Figure styling error: {e}")
            return fig

    def add_plot(self, fig: go.Figure, width_percent=90):
        if not self.font_loaded or not fig: return
        try:
            styled_fig = self._style_figure_for_arabic(fig)
            try:
                pio.kaleido.scope.chromium_args = ["--no-sandbox", "--disable-dev-shm-usage"]
            except Exception:
                pass # Ignore if Kaleido scope is not configurable
            
            img_bytes = styled_fig.to_image(format="png", scale=2, width=800, height=450)
            img_file = io.BytesIO(img_bytes)
            pil_img = Image.open(img_file)
            
            aspect_ratio = pil_img.height / pil_img.width
            page_width = self._get_drawable_width()
            img_width_mm = page_width * (width_percent / 100)
            img_height_mm = img_width_mm * aspect_ratio
            
            # Auto page break if plot doesn't fit
            if self.get_y() + img_height_mm > (self.h - self.b_margin):
                self.add_page_with_background(use_background=False)
                
            x_pos = (self.w - img_width_mm) / 2
            img_file.seek(0)
            self.image(img_file, x=x_pos, y=self.get_y(), w=img_width_mm)
            self.set_y(self.get_y() + img_height_mm)
        except Exception as e:
            st.error(f"Error adding plot: {e}")

    def add_section_title(self, title):
        # Auto page break for section titles
        if self.get_y() > (self.h - self.b_margin - 30):
            self.add_page_with_background(use_background=False)
            
        self.ln(10)
        self.set_font("Amiri", "", 22)
        self.set_text_color(*TITLE_COLOR)
        self.cell(0, 12, self._process_text(title), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Decorative line below the title
        self.set_draw_color(*ACCENT_COLOR)
        self.line(self.w - self.r_margin - 60, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(8)


    def add_kpi_grid(self, kpis: dict):
        if not kpis:
            return
        
        drawable_width = self._get_drawable_width()
        num_cols = 3
        gap = 5  # The space between cards
        col_width = (drawable_width - (num_cols - 1) * gap) / num_cols
        card_height = 30
        icon_size = 18
        
        kpi_list = list(kpis.items())
        for i in range(0, len(kpi_list), num_cols):
            # --- START OF FIX ---
            # 1. Save the Y position at the START of the row
            y0 = self.get_y()
            # Reset X position to the left margin for the row
            self.set_x(self.l_margin)
            # --- END OF FIX ---

            row_items = kpi_list[i : i + num_cols]
            
            for j, (label, (value, icon)) in enumerate(row_items):
                # Calculate the X position for each card manually
                x0 = self.l_margin + j * (col_width + gap)
                
                # Draw the card background
                self.set_fill_color(248, 249, 250) # CARD_BACKGROUND_COLOR
                # 2. Use the saved y0 for the card's vertical position
                # self.rect(x0, y0, col_width, card_height, 'F')
                self.set_draw_color(224, 224, 224) # LINE_COLOR
                self.rect(x0, y0, col_width, card_height, 'DF')
                
                # Draw the accent line on the right
                self.set_draw_color(41, 128, 185) # ACCENT_COLOR
                self.line(x0 + col_width, y0, x0 + col_width, y0 + card_height)

                # Icon
                self.set_font("Amiri", "", icon_size)
                self.set_text_color(41, 128, 185) # ACCENT_COLOR
                # 3. Use y0 for all positioning calculations
                self.set_xy(x0 + col_width - icon_size - 5, y0 + (card_height - icon_size) / 2)
                self.cell(icon_size, icon_size, self._process_text(icon))

                # KPI Value (Large Font)
                self.set_font("Amiri", "", 16)
                self.set_text_color(44, 62, 80) # TITLE_COLOR
                self.set_xy(x0 + 5, y0 + 5)
                self.cell(col_width - icon_size - 15, 10, self._process_text(str(value)), align="R")

                # KPI Label (Smaller Font)
                self.set_font("Amiri", "", 11)
                self.set_text_color(93, 109, 126) # KPI_TEXT_COLOR
                self.set_xy(x0 + 5, y0 + 15)
                self.cell(col_width - icon_size - 15, 10, self._process_text(label), align="R")
                
            # 4. Move the cursor down based on the original y0
            self.set_y(y0 + card_height + gap)


    def add_hall_of_fame_grid(self, heroes: dict):
        if not heroes: return

        drawable_width = self._get_drawable_width()
        num_cols = 4
        gap = 4 # The space between cards
        col_width = (drawable_width - (num_cols - 1) * gap) / num_cols
        card_height = 35
        
        heroes_list = list(heroes.items())
        for i in range(0, len(heroes_list), num_cols):
            # --- START OF FIX ---
            # 1. Save the Y position at the START of the row
            y0 = self.get_y()
            # --- END OF FIX ---

            row_items = heroes_list[i : i + num_cols]
            
            for j, (title, (name, value)) in enumerate(row_items):
                # Calculate X for each card
                x0 = self.l_margin + j * (col_width + gap)

                # Card background and border
                self.set_fill_color(248, 249, 250) # CARD_BACKGROUND_COLOR
                self.set_draw_color(224, 224, 224) # LINE_COLOR
                # 2. Use the saved y0 for card's vertical position
                self.rect(x0, y0, col_width, card_height, 'DF')
                
                # 3. Use y0 for all positioning calculations
                # Hero Title
                self.set_font("Amiri", "", 12)
                self.set_text_color(41, 128, 185) # ACCENT_COLOR
                self.set_xy(x0 + 2, y0 + 3)
                self.multi_cell(col_width - 4, 7, self._process_text(title), align="C")

                # Hero Name
                self.set_font("Amiri", "", 14)
                self.set_text_color(44, 62, 80) # TITLE_COLOR
                self.set_xy(x0 + 2, y0 + 15)
                self.multi_cell(col_width - 4, 6, self._process_text(name), align="C")

                # Hero Value
                self.set_font("Amiri", "", 10)
                self.set_text_color(93, 109, 126) # KPI_TEXT_COLOR
                self.set_xy(x0 + 2, y0 + 26)
                self.multi_cell(col_width - 4, 5, self._process_text(value), align="C")
                
            # 4. Move cursor down based on original y0
            self.set_y(y0 + card_height + gap)

    def add_dual_chart_pages(self, charts: dict):
        """Adds pages with two charts each, ensuring a structured layout."""
        if not charts:
            return

        chart_list = [(title, fig) for title, fig in charts.items() if fig is not None]
        
        for i in range(0, len(chart_list), 2):
            # A new page for every pair of charts
            self.add_page_with_background(use_background=False)
            
            # --- First Chart (Top) ---
            title1, fig1 = chart_list[i]
            self.add_section_title(title1)
            self.add_plot(fig1)
            self.ln(10) # Spacing

            # --- Second Chart (Bottom), if it exists ---
            if i + 1 < len(chart_list):
                title2, fig2 = chart_list[i+1]
                self.add_section_title(title2)
                self.add_plot(fig2)

    def add_dashboard_report(self, data: dict):
        """Generates a full dashboard report with the new structured and professional layout."""
        if not self.font_loaded:
            st.error("Font not loaded, cannot generate PDF report.")
            return
        
        # --- PAGE 1: COVER PAGE ---
        self.add_page_with_background(use_background=True)
        self.set_y(A4_HEIGHT / 2 - 40) # Start near the middle
        self.set_font("Amiri", "", 40)
        self.set_text_color(*TITLE_COLOR)
        self.cell(0, 25, self._process_text("تقرير ماراثون القراءة"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Amiri", "", 24)
        self.set_text_color(*ACCENT_COLOR)
        self.cell(0, 15, self._process_text("لوحة التحكم العامة"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(10)
        self.set_font("Amiri", "", 14)
        self.set_text_color(*KPI_TEXT_COLOR)
        today_str = self._process_text(f"تاريخ الإصدار: {date.today().strftime('%Y-%m-%d')}")
        self.cell(0, 10, today_str, align="C")

        # --- PAGE 2: SUMMARY (KPIs & Hall of Fame) ---
        self.add_page_with_background(use_background=False) # Use a clean white page
        
        # KPIs Section
        self.add_section_title("📊 مؤشرات الأداء الرئيسية")
        self.add_kpi_grid(data.get('kpis', {}))
        
        self.ln(15) # Add extra space between sections

        # Hall of Fame Section
        self.add_section_title("🌟 لوحة شرف الأبطال")
        self.add_hall_of_fame_grid(data.get('heroes', {}))

        # --- SUBSEQUENT PAGES: CHARTS (Two per page) ---
        self.add_dual_chart_pages(data.get('charts', {}))

    # --- Other report functions remain unchanged ---
    def add_challenge_report(self, data: dict):
        if not self.font_loaded: return
        try:
            self.add_challenge_title_page(
                title=data.get('title', ''), author=data.get('author', ''),
                period=data.get('period', ''), duration=data.get('duration', 0)
            )
            self.add_participants_page(
                all_participants=data.get('all_participants', []),
                finishers=data.get('finishers', []), attendees=data.get('attendees', [])
            )
        except Exception as e:
            st.error(f"Error generating challenge report: {e}")

    def add_challenge_title_page(self, title, author, period, duration):
        # ... (This function remains as is)
        if not self.font_loaded: return
        try:
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
        except Exception as e:
            st.warning(f"Challenge title page error: {e}")


    def add_participants_page(self, all_participants, finishers, attendees):
        if not self.font_loaded:
            return
        try:
            self.add_page_with_background(use_background=False)
            self.add_section_title("المشاركون في التحدي")
            page_w = self._get_drawable_width()
            col_w = page_w / 3
            header_h, line_h = 10, 8

            # Table Header
            self.set_font("Amiri", "", 14)
            self.set_fill_color(68, 84, 106) # لون رأس أغمق
            self.set_text_color(255, 255, 255) # نص أبيض
            self.cell(col_w, header_h, self._process_text("من حضروا النقاش"), border=0, align="C", fill=True)
            self.cell(col_w, header_h, self._process_text("من أنهوا الكتاب"), border=0, align="C", fill=True)
            self.cell(col_w, header_h, self._process_text("جميع المشاركين"), border=0, align="C", fill=True)
            self.ln(header_h)

            # Table Body
            self.set_font("Amiri", "", 11)
            self.set_text_color(50,50,50)
            max_len = max(len(all_participants), len(finishers), len(attendees))
            
            for i in range(max_len):
                # --- START OF AESTHETIC CHANGE ---
                # Alternating row colors for better readability
                if i % 2 == 0:
                    self.set_fill_color(248, 249, 250) # Light Gray
                else:
                    self.set_fill_color(255, 255, 255) # White
                # --- END OF AESTHETIC CHANGE ---

                p_name = all_participants[i] if i < len(all_participants) else ""
                f_name = finishers[i] if i < len(finishers) else ""
                a_name = attendees[i] if i < len(attendees) else ""
                
                # Draw cells for the row, ensuring fill is True
                self.cell(col_w, line_h, self._process_text(a_name), align="C", fill=True, border='LR')
                self.cell(col_w, line_h, self._process_text(f_name), align="C", fill=True, border='LR')
                self.cell(col_w, line_h, self._process_text(p_name), align="C", fill=True, border='LR')
                self.ln(line_h)
                
            # Add a bottom line to close the table
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())

        except Exception as e:
            st.warning(f"Participants page error: {e}")


    def header(self):
        # لا تقم بإضافة رأس لصفحة الغلاف (صفحة رقم 1)
        if self.page_no() == 1:
            return
        
        # إضافة شعار إذا كان موجودًا (اختياري)
        # if os.path.exists("logo.png"):
        #     self.image("logo.png", x=10, y=8, w=30)
            
        # إضافة خط فاصل أنيق في الأعلى
        self.set_draw_color(224, 224, 224) # LINE_COLOR
        self.line(self.l_margin, 20, self.w - self.r_margin, 20)
        
        # اترك مسافة كافية بعد الرأس قبل بدء المحتوى
        self.set_y(25)