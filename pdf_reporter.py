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
# --- ENHANCED AESTHETIC CONSTANTS ---
ACCENT_COLOR = (52, 152, 219)  # Modern blue
SECONDARY_COLOR = (46, 204, 113)  # Success green
WARNING_COLOR = (241, 196, 15)  # Warning yellow
DANGER_COLOR = (231, 76, 60)  # Danger red
LINE_COLOR = (236, 240, 241)  # Light separator
TITLE_COLOR = (44, 62, 80)  # Dark slate
SUBTITLE_COLOR = (108, 117, 125)  # Medium gray
KPI_TEXT_COLOR = (108, 117, 125)  # Medium gray
BACKGROUND_COLOR = (248, 249, 250)  # Light background
CARD_BACKGROUND = (255, 255, 255)  # White cards

# Plotly colors
PLOTLY_TITLE_COLOR = f"rgb{TITLE_COLOR}"
PLOTLY_TEXT_COLOR = "rgb(52, 73, 94)"
PLOTLY_GRID_COLOR = "rgba(189, 195, 199, 0.3)"

class PDFReporter(FPDF):
    """
    Enhanced PDF Reporter with improved formatting and Arabic support
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
            alpha = img.getchannel('A').point(lambda i: i * 0.3)  # More subtle background
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
        # Add subtle page background
        if not use_background:
            self.set_fill_color(*BACKGROUND_COLOR)
            self.rect(0, 0, A4_WIDTH, A4_HEIGHT, 'F')
        
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
        is_amiri = isinstance(family, str) and family.lower() == "amiri"
        is_bold_style = isinstance(style, str) and style.upper() == 'B'

        if self.font_loaded and is_amiri:
            if is_bold_style:
                style = ''
            super().set_font(family, style, size)
        else:
            super().set_font(family, style, size)

    def footer(self):
        if not self.font_loaded or self.page_no() == 1: return
        try:
            # Enhanced footer with better styling
            self.set_y(-20)
            self.set_fill_color(*CARD_BACKGROUND)
            self.rect(0, A4_HEIGHT - 20, A4_WIDTH, 20, 'F')
            
            self.set_draw_color(*LINE_COLOR)
            self.line(10, A4_HEIGHT - 20, A4_WIDTH - 10, A4_HEIGHT - 20)
            
            self.set_y(-15)
            self.set_font("Amiri", "", 9)
            self.set_text_color(*SUBTITLE_COLOR)
            
            # Page number
            self.set_x(A4_WIDTH / 2 - 10)
            self.cell(20, 10, f"صفحة {self.page_no()}", align="C")
            
            # Date
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.set_x(A4_WIDTH - 80)
            self.cell(70, 10, self._process_text(f"تقرير ماراثون القراءة - {today_str}"), align="R")
            
        except Exception as e:
            st.warning(f"Footer error: {e}")

    def _get_drawable_width(self):
        return self.w - self.l_margin - self.r_margin

    def _style_figure_for_arabic(self, fig: go.Figure):
        if not self.font_loaded: return fig
        try:
            fig.update_layout(
                font=dict(family="Arial", size=11, color=PLOTLY_TEXT_COLOR),
                paper_bgcolor='rgba(255,255,255,0.9)',
                plot_bgcolor='rgba(248,249,250,0.5)',
                title=dict(
                    font=dict(family="Arial", size=16, color=PLOTLY_TITLE_COLOR), 
                    x=0.5, 
                    y=0.95,
                    pad=dict(b=20)
                ),
                xaxis=dict(
                    title=dict(font=dict(family="Arial", size=12, color=PLOTLY_TEXT_COLOR)), 
                    tickfont=dict(family="Arial", size=10, color=PLOTLY_TEXT_COLOR), 
                    showgrid=True, 
                    gridcolor=PLOTLY_GRID_COLOR, 
                    gridwidth=1,
                    linecolor="rgba(189, 195, 199, 0.8)",
                    linewidth=1
                ),
                yaxis=dict(
                    title=dict(font=dict(family="Arial", size=12, color=PLOTLY_TEXT_COLOR)), 
                    tickfont=dict(family="Arial", size=10, color=PLOTLY_TEXT_COLOR), 
                    showgrid=True, 
                    gridcolor=PLOTLY_GRID_COLOR, 
                    gridwidth=1,
                    linecolor="rgba(189, 195, 199, 0.8)",
                    linewidth=1
                ),
                margin=dict(l=50, r=50, t=60, b=50),
                showlegend=True,
                legend=dict(
                    font=dict(size=10, color=PLOTLY_TEXT_COLOR),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(189, 195, 199, 0.5)",
                    borderwidth=1
                )
            )
            return fig
        except Exception as e:
            st.warning(f"Figure styling error: {e}")
            return fig

    def add_plot(self, fig: go.Figure, width_percent=88):
        if not self.font_loaded or not fig: return None, 0
        try:
            styled_fig = self._style_figure_for_arabic(fig)
            try:
                pio.kaleido.scope.chromium_args = ["--no-sandbox", "--disable-dev-shm-usage"]
            except:
                pass
            
            # Enhanced plot rendering
            img_bytes = styled_fig.to_image(format="png", scale=2.5, width=900, height=500)
            img_file = io.BytesIO(img_bytes)
            pil_img = Image.open(img_file)
            aspect_ratio = pil_img.height / pil_img.width
            page_width = self._get_drawable_width()
            img_width_mm = page_width * (width_percent / 100)
            img_height_mm = img_width_mm * aspect_ratio
            
            # Check if we need a new page
            if self.get_y() + img_height_mm > (self.h - self.b_margin - 10):
                self.add_page_with_background(use_background=False)
                
            # Add subtle shadow/border effect
            x_pos = (self.w - img_width_mm) / 2
            self.set_fill_color(240, 240, 240)
            self.rect(x_pos - 1, self.get_y() - 1, img_width_mm + 2, img_height_mm + 2, 'F')
            
            img_file.seek(0)
            self.image(img_file, x=x_pos, y=self.get_y(), w=img_width_mm)
            self.set_y(self.get_y() + img_height_mm + 5)
            return img_height_mm
        except Exception as e:
            st.error(f"Error adding plot: {e}")
            return None, 0

    def add_section_title(self, title, subtitle=None):
        try:
            # Check if there is enough space
            if self.get_y() > (self.h - self.b_margin - 40): 
                self.add_page_with_background(use_background=False)
            
            self.ln(15)
            
            # Main title
            self.set_font("Amiri", "", 20)
            self.set_text_color(*TITLE_COLOR)
            self.cell(0, 10, self._process_text(title), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Decorative line
            self.set_draw_color(*ACCENT_COLOR)
            self.set_line_width(2)
            line_start = self.w - self.r_margin - 80
            line_end = self.w - self.r_margin
            self.line(line_start, self.get_y(), line_end, self.get_y())
            
            # Subtitle if provided
            if subtitle:
                self.ln(5)
                self.set_font("Amiri", "", 12)
                self.set_text_color(*SUBTITLE_COLOR)
                self.cell(0, 8, self._process_text(subtitle), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.ln(12)
            
        except Exception as e:
            st.warning(f"Section title error: {e}")

    def add_enhanced_kpi_grid(self, kpis: dict):
        if not kpis: return
        try:
            # Enhanced KPI cards with better spacing and styling
            cols = 2  # Use 2 columns for better readability
            col_width = (self._get_drawable_width() - 10) / cols
            cell_height = 40
            
            kpi_list = list(kpis.items())
            
            for i in range(0, len(kpi_list), cols):
                if self.get_y() + cell_height > (self.h - self.b_margin - 20):
                    self.add_page_with_background(use_background=False)
                
                self.set_x(self.l_margin)
                
                for j in range(cols):
                    if i + j < len(kpi_list):
                        label, (value, icon) = kpi_list[i+j]
                        x = self.get_x()
                        y = self.get_y()
                        
                        # Card background with subtle shadow
                        self.set_fill_color(245, 245, 245)
                        self.rect(x + 1, y + 1, col_width - 8, cell_height, 'F')
                        self.set_fill_color(*CARD_BACKGROUND)
                        self.rect(x, y, col_width - 8, cell_height, 'F')
                        
                        # Card border
                        self.set_draw_color(*LINE_COLOR)
                        self.set_line_width(0.5)
                        self.rect(x, y, col_width - 8, cell_height, 'D')
                        
                        # Icon
                        self.set_font("Amiri", "", 24)
                        self.set_text_color(*ACCENT_COLOR)
                        self.set_xy(x + 8, y + 8)
                        self.cell(30, 12, self._process_text(icon), align="C")
                        
                        # Value
                        self.set_font("Amiri", "", 18)
                        self.set_text_color(*TITLE_COLOR)
                        self.set_xy(x + col_width - 80, y + 8)
                        self.cell(65, 12, self._process_text(str(value)), align="R")
                        
                        # Label
                        self.set_font("Amiri", "", 11)
                        self.set_text_color(*SUBTITLE_COLOR)
                        self.set_xy(x + 8, y + 24)
                        self.cell(col_width - 20, 12, self._process_text(label), align="R")
                        
                        self.set_x(x + col_width + 2)
                
                self.ln(cell_height + 8)
                
        except Exception as e:
            st.warning(f"Enhanced KPI grid error: {e}")

    def add_enhanced_hall_of_fame(self, heroes: dict):
        if not heroes: return
        try:
            # Create a more elegant hall of fame layout
            cols = 2
            col_width = (self._get_drawable_width() - 10) / cols
            cell_height = 50
            
            heroes_list = list(heroes.items())
            
            for i in range(0, len(heroes_list), cols):
                if self.get_y() + cell_height > (self.h - self.b_margin - 20):
                    self.add_page_with_background(use_background=False)
                
                self.set_x(self.l_margin)
                
                for j in range(cols):
                    if i + j < len(heroes_list):
                        title, (name, value) = heroes_list[i+j]
                        x = self.get_x()
                        y = self.get_y()
                        
                        # Gradient-like effect with multiple rectangles
                        self.set_fill_color(240, 240, 240)
                        self.rect(x + 2, y + 2, col_width - 8, cell_height, 'F')
                        
                        # Main card
                        self.set_fill_color(*CARD_BACKGROUND)
                        self.rect(x, y, col_width - 8, cell_height, 'F')
                        
                        # Colored top border
                        colors = [ACCENT_COLOR, SECONDARY_COLOR, WARNING_COLOR, DANGER_COLOR]
                        color = colors[j % len(colors)]
                        self.set_fill_color(*color)
                        self.rect(x, y, col_width - 8, 4, 'F')
                        
                        # Title
                        self.set_font("Amiri", "", 11)
                        self.set_text_color(*color)
                        self.set_xy(x + 8, y + 8)
                        self.cell(col_width - 20, 8, self._process_text(title), align="C")
                        
                        # Name
                        self.set_font("Amiri", "", 14)
                        self.set_text_color(*TITLE_COLOR)
                        self.set_xy(x + 8, y + 20)
                        self.cell(col_width - 20, 10, self._process_text(name), align="C")
                        
                        # Value
                        self.set_font("Amiri", "", 10)
                        self.set_text_color(*SUBTITLE_COLOR)
                        self.set_xy(x + 8, y + 32)
                        self.cell(col_width - 20, 8, self._process_text(str(value)), align="C")
                        
                        # Border
                        self.set_draw_color(*LINE_COLOR)
                        self.set_line_width(0.5)
                        self.rect(x, y, col_width - 8, cell_height, 'D')
                        
                        self.set_x(x + col_width + 2)
                
                self.ln(cell_height + 10)
                
        except Exception as e:
            st.warning(f"Enhanced hall of fame error: {e}")

    def add_enhanced_dual_chart_pages(self, charts: dict):
        """Enhanced dual chart layout with better spacing"""
        if not charts:
            return

        chart_list = [(title, fig) for title, fig in charts.items() if fig is not None]
        
        for i in range(0, len(chart_list), 2):
            # Start new page
            self.add_page_with_background(use_background=False)
            
            # First chart
            title1, fig1 = chart_list[i]
            self.add_section_title(title1)
            self.add_plot(fig1, width_percent=85)
            
            # Add separator space
            self.ln(15)
            
            # Second chart if exists
            if i + 1 < len(chart_list):
                title2, fig2 = chart_list[i+1]
                self.add_section_title(title2)
                self.add_plot(fig2, width_percent=85)

    def add_enhanced_dashboard_report(self, data: dict):
        """Enhanced dashboard report with improved layout"""
        if not self.font_loaded: return
        
        try:
            # --- Page 1: Cover ---
            self.add_page_with_background(use_background=True)
            
            # Enhanced cover page
            self.set_y(A4_HEIGHT / 2 - 50)
            
            # Main title with gradient effect
            self.set_font("Amiri", "", 36)
            self.set_text_color(*TITLE_COLOR)
            self.cell(0, 20, self._process_text("تقرير ماراثون القراءة"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Decorative line
            self.set_draw_color(*ACCENT_COLOR)
            self.set_line_width(3)
            line_width = 80
            line_start = (A4_WIDTH - line_width) / 2
            self.line(line_start, self.get_y(), line_start + line_width, self.get_y())
            
            self.ln(15)
            
            # Subtitle
            self.set_font("Amiri", "", 22)
            self.set_text_color(*ACCENT_COLOR)
            self.cell(0, 12, self._process_text("لوحة التحكم العامة"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.ln(25)
            
            # Date with better formatting
            self.set_font("Amiri", "", 13)
            self.set_text_color(*SUBTITLE_COLOR)
            today_str = self._process_text(f"تاريخ الإصدار: {date.today().strftime('%Y-%m-%d')}")
            
            # Add a box around the date
            date_width = 60
            date_x = (A4_WIDTH - date_width) / 2
            self.set_fill_color(*CARD_BACKGROUND)
            self.set_draw_color(*LINE_COLOR)
            self.rect(date_x, self.get_y() - 2, date_width, 12, 'FD')
            
            self.cell(0, 8, today_str, align="C")

            # --- Page 2: Summary ---
            self.add_page_with_background(use_background=False)
            
            # KPI Section
            self.add_section_title("📊 مؤشرات الأداء الرئيسية", "نظرة عامة على الإحصائيات الهامة")
            self.add_enhanced_kpi_grid(data.get('kpis', {}))
            
            self.ln(20)

            # Hall of Fame Section
            self.add_section_title("🌟 لوحة شرف الأبطال", "أبرز المتميزين في ماراثون القراءة")
            self.add_enhanced_hall_of_fame(data.get('heroes', {}))

            # --- Chart Pages ---
            self.add_enhanced_dual_chart_pages(data.get('charts', {}))

        except Exception as e:
            st.error(f"Error generating enhanced dashboard report: {e}")

    # Keep existing methods for backward compatibility
    def add_kpi_grid(self, kpis: dict):
        return self.add_enhanced_kpi_grid(kpis)
    
    def add_hall_of_fame_grid(self, heroes: dict):
        return self.add_enhanced_hall_of_fame(heroes)
    
    def add_dual_chart_pages(self, charts: dict):
        return self.add_enhanced_dual_chart_pages(charts)
    
    def add_dashboard_report(self, data: dict):
        return self.add_enhanced_dashboard_report(data)

    # --- Keep existing challenge report methods unchanged ---
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
        if not self.font_loaded: return
        try:
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
        except Exception as e:
            st.warning(f"Participants page error: {e}")