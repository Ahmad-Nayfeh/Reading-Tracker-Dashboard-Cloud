import plotly.graph_objects as go
import plotly.express as px

# Define a professional color palette to be used across all charts
CHART_COLORS = {
    "primary": "#2980B9",      # A strong, professional blue
    "secondary": "#8E44AD",    # A complementary purple
    "accent_1": "#27AE60",     # Green for growth/success
    "accent_2": "#F39C12",     # Orange for attention
    "accent_3": "#E74C3C",     # Red for emphasis
    "text_main": "#2c3e50",    # Dark, readable text
    "text_light": "#5D6D7E",   # Lighter text for labels
    "grid": "#ecf0f1",         # Very light grid lines
    "background": "rgba(0,0,0,0)" # Transparent background
}

def apply_chart_theme(fig, chart_type='default'):
    """
    Applies a consistent, modern theme to a Plotly figure.
    
    Args:
        fig (go.Figure): The figure object to style.
        chart_type (str): The type of chart to apply specific styles for 
                          ('area', 'line', 'bar', 'pie', etc.).
    
    Returns:
        go.Figure: The styled figure object.
    """
    # General layout updates for a clean and modern look
    fig.update_layout(
        font=dict(
            family="sans-serif",  # A clean, universally available font
            size=12,
            color=CHART_COLORS["text_main"]
        ),
        paper_bgcolor=CHART_COLORS["background"],
        plot_bgcolor=CHART_COLORS["background"],
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(
            gridcolor=CHART_COLORS["grid"],
            zeroline=False,
            showline=False,
            tickfont=dict(color=CHART_COLORS["text_light"])
        ),
        yaxis=dict(
            gridcolor=CHART_COLORS["grid"],
            zeroline=False,
            showline=False,
            tickfont=dict(color=CHART_COLORS["text_light"])
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )

    # --- Specific trace updates based on chart type ---

    # For area charts, apply a gradient fill and a strong line color
    if chart_type == 'area':
        fig.update_traces(
            line=dict(color=CHART_COLORS["accent_1"], width=2.5),
            fill='tozeroy',
            # Manually create a gradient-like effect with a semi-transparent fill
            fillcolor='rgba(39, 174, 96, 0.1)' 
        )
    
    # For line charts, use the primary color for the line
    elif chart_type == 'line':
        fig.update_traces(
            line=dict(color=CHART_COLORS["primary"], width=2.5)
        )
        
    # For bar charts, use a distinct color and remove the marker line
    elif chart_type == 'bar':
        fig.update_traces(
            marker_line_width=0
        )
        
    # For pie/donut charts, apply a predefined color sequence
    elif chart_type == 'pie':
        fig.update_traces(
            hoverinfo='label+percent',
            textinfo='percent',
            textfont_size=14,
            marker=dict(colors=[CHART_COLORS["primary"], CHART_COLORS["accent_2"], CHART_COLORS["secondary"]], 
                        line=dict(color='#ffffff', width=2))
        )

    return fig
