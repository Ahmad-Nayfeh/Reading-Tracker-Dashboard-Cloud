import streamlit as st
from fpdf import FPDF, XPos, YPos
from datetime import datetime
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
ACCENT_COLOR = (41, 128, 185) # A professional blue color
LINE_COLOR = (200, 200, 200) # A light gray for separator lines

class PDF(FPDF):
    """
    A base class to generate professional, multi-page PDF reports with full Arabic support,
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
            st.error(f"Font file not found! Please make sure '{self.font_path}' is in the root folder.")
            return
        try:
            self.add_font("Amiri", "", self.font_path, uni=True)
            self.font_loaded = True
        except Exception as e:
            st.error(f"FPDF error when adding font '{self.font_path}': {e}")

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

    def add_page(self, orientation="", format="", same=False):
        super().add_page(orientation, format, same)
        if self.processed_background:
            self.image(self.processed_background, 0, 0, w=A4_WIDTH, h=A4_HEIGHT)

    def _process_text(self, text):
        if not self.font_loaded or text is None: return str(text or "")
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)

    def set_font(self, family, style="", size=0):
        if self.font_loaded and family.lower() == "amiri":
            super().set_font(family, style, size)
        else:
            super().set_font("helvetica", style, size)

    def footer(self):
        if not self.font_loaded or self.page_no() <= 1: return
        self.set_y(-15)
        self.set_font("Amiri", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, f"{self.page_no()}", align="L")
        self.set_y(-15)
        self.cell(0, 10, self._process_text("تقرير ماراثون القراءة"), align="R")

    def _style_figure_for_arabic(self, fig: go.Figure):
        if not self.font_loaded: return fig
        fig.update_layout(
            font=dict(family="Amiri", size=12, color="black"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            title=dict(font=dict(family="Amiri", size=18, color="black"), x=0.5, pad=dict(b=15)),
            xaxis=dict(title=dict(font=dict(family="Amiri", size=14, color="black")), tickfont=dict(family="Amiri", size=12, color="black"), showgrid=True, gridcolor="lightgray", gridwidth=0.5),
            yaxis=dict(title=dict(font=dict(family="Amiri", size=14, color="black")), tickfont=dict(family="Amiri", size=12, color="black"), showgrid=True, gridcolor="lightgray", gridwidth=0.5),
            margin=dict(l=60, r=60, t=80, b=60)
        )
        return fig

    def add_plot(self, fig: go.Figure, width_percent=90):
        if not self.font_loaded or not fig: return 0
        styled_fig = self._style_figure_for_arabic(fig)
        pio.kaleido.chromium_args = "--no-sandbox"
        try:
            img_bytes = styled_fig.to_image(format="png", scale=2, width=800, height=500)
        except Exception as e:
            st.error(f"Failed to convert Plotly figure to image: {e}")
            return 0

        img_file = io.BytesIO(img_bytes)
        pil_img = Image.open(img_file)
        aspect_ratio = pil_img.height / pil_img.width
        page_width = self.w - self.l_margin - self.r_margin
        img_width_mm = page_width * (width_percent / 100)
        img_height_mm = img_width_mm * aspect_ratio
        x_pos = (self.w - img_width_mm) / 2
        img_file.seek(0)
        self.image(img_file, x=x_pos, w=img_width_mm)
        return img_height_mm
    
    def add_cover_page(self, title, subtitle):
        if not self.font_loaded: return
        self.add_page()
        self.set_y(A4_HEIGHT / 4)
        self.set_font("Amiri", "", 36)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 15, self._process_text(title), align="C")
        self.set_font("Amiri", "", 24)
        self.set_text_color(*ACCENT_COLOR)
        self.multi_cell(0, 20, self._process_text(subtitle), align="C")
        self.set_y(A4_HEIGHT / 1.5)
        self.set_font("Amiri", "", 16)
        self.set_text_color(0, 0, 0)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.multi_cell(0, 10, self._process_text(f"تاريخ التصدير: {today_str}"), align="C")

    def add_kpi_section(self, kpis: dict, title: str):
        if not self.font_loaded or not kpis: return
        self.add_page()
        self.set_y(A4_HEIGHT / 4)
        self.set_font("Amiri", "", 24)
        self.set_text_color(*ACCENT_COLOR)
        self.cell(0, 15, self._process_text(title), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.line(self.l_margin, self.get_y() + 2, self.w - self.r_margin, self.get_y() + 2)
        self.ln(15)

        col_width = (self.w - self.l_margin - self.r_margin) / len(kpis)
        self.set_font("Amiri", "", 12)
        self.set_text_color(50, 50, 50)
        for label, _ in kpis.items():
            self.cell(col_width, 10, self._process_text(label), align="C")
        self.ln(10)
        self.set_font("Amiri", "", 20)
        self.set_text_color(0, 0, 0)
        for _, value in kpis.items():
            self.cell(col_width, 10, self._process_text(str(value)), align="C")
        self.ln(15)

    def add_chart_page(self, fig, title):
        if not fig: return
        self.add_page()
        self.set_y(A4_HEIGHT / 4)
        self.set_font("Amiri", "", 24)
        self.set_text_color(*ACCENT_COLOR)
        self.cell(0, 10, self._process_text(title), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(10)
        self.add_plot(fig, width_percent=85)

# --- Generator Functions ---

def generate_overall_dashboard_pdf(data: dict):
    pdf = PDF()
    pdf.add_cover_page("تقرير ماراثون القراءة", "لوحة التحكم العامة")
    
    # KPIs
    pdf.add_kpi_section(data.get('kpis_main', {}), "المؤشرات الرئيسية")
    pdf.add_kpi_section(data.get('kpis_secondary', {}), "المؤشرات الثانوية")
    
    # Charts
    pdf.add_chart_page(data.get('fig_growth'), "نمو القراءة التراكمي")
    pdf.add_chart_page(data.get('fig_weekly_activity'), "نشاط القراءة الأسبوعي")
    pdf.add_chart_page(data.get('fig_rhythm'), "إيقاع القراءة اليومي للفريق")
    pdf.add_chart_page(data.get('fig_points_leaderboard'), "المتصدرون بالنقاط")
    pdf.add_chart_page(data.get('fig_hours_leaderboard'), "المتصدرون بالساعات")
    pdf.add_chart_page(data.get('fig_donut'), "تركيز القراءة")

    return bytes(pdf.output())

def generate_challenge_summary_pdf(data: dict):
    pdf = PDF()
    pdf.add_cover_page(f"تقرير تحدي: {data.get('title', '')}", f"من {data.get('start_date', '')} إلى {data.get('end_date', '')}")

    # KPIs
    pdf.add_kpi_section(data.get('kpis', {}), "ملخص أداء التحدي")
    
    # Charts
    pdf.add_chart_page(data.get('fig_growth'), "نمو القراءة التراكمي للتحدي")
    pdf.add_chart_page(data.get('fig_weekly_activity'), "نشاط القراءة الأسبوعي للتحدي")
    pdf.add_chart_page(data.get('fig_rhythm'), "إيقاع القراءة اليومي للتحدي")
    pdf.add_chart_page(data.get('fig_points_leaderboard'), "المتصدرون بالنقاط في التحدي")
    pdf.add_chart_page(data.get('fig_hours_leaderboard'), "المتصدرون بالساعات في التحدي")
    pdf.add_chart_page(data.get('fig_donut'), "تركيز القراءة في التحدي")

    return bytes(pdf.output())

def generate_reader_card_pdf(data: dict):
    pdf = PDF()
    pdf.add_cover_page(f"بطاقة القارئ: {data.get('name', '')}", "ملخص الأداء التاريخي")

    # KPIs
    pdf.add_kpi_section(data.get('kpis', {}), "إحصائيات القارئ")

    # Badges and Points Source
    pdf.add_page()
    pdf.set_y(A4_HEIGHT / 5)
    pdf.set_font("Amiri", "", 24)
    pdf.set_text_color(*ACCENT_COLOR)
    pdf.cell(0, 15, pdf._process_text("الأوسمة ومصادر النقاط"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)
    
    # Badges
    pdf.set_font("Amiri", "", 18)
    pdf.cell(0, 10, pdf._process_text("🏅 الأوسمة والشارات"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Amiri", "", 12)
    pdf.set_text_color(0,0,0)
    if data.get('badges'):
        for badge in data['badges']:
            pdf.multi_cell(0, 8, pdf._process_text(f"• {badge[0]} {badge[1]}"), align="R")
    else:
        pdf.multi_cell(0, 8, pdf._process_text("لا توجد أوسمة بعد."), align="R")
    pdf.ln(10)

    # Points source chart
    pdf.add_plot(data.get('fig_points_source'), width_percent=60)
    
    # Charts
    pdf.add_chart_page(data.get('fig_growth'), "نمو القراءة التراكمي")
    pdf.add_chart_page(data.get('fig_weekly_activity'), "نشاط القراءة الأسبوعي")
    pdf.add_chart_page(data.get('fig_rhythm'), "إيقاع القراءة اليومي")
    pdf.add_chart_page(data.get('fig_heatmap'), "خريطة الالتزام الحرارية")

    return bytes(pdf.output())
