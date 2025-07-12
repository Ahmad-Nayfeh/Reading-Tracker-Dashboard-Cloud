import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import apply_chart_theme
from datetime import date

def create_growth_chart(logs_df, full_date_range_df):
    """
    Generates the cumulative reading growth area chart.
    Args:
        logs_df (pd.DataFrame): DataFrame containing reading logs.
        full_date_range_df (pd.DataFrame): DataFrame with a complete date range.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    if logs_df.empty or full_date_range_df.empty:
        return None
    
    daily_minutes_growth = logs_df.groupby(logs_df['submission_date_dt'])['total_minutes'].sum().reset_index(name='minutes')
    merged_growth = pd.merge(full_date_range_df, daily_minutes_growth, on='submission_date_dt', how='left').fillna(0)
    merged_growth['cumulative_hours'] = merged_growth['minutes'].cumsum() / 60
    
    fig = px.area(merged_growth, x='submission_date_dt', y='cumulative_hours', 
                  labels={'submission_date_dt': 'التاريخ', 'cumulative_hours': 'مجموع الساعات التراكمي'})
    fig = apply_chart_theme(fig, 'area')
    fig.update_layout(yaxis={'side': 'right'}, xaxis_autorange='reversed')
    return fig

def create_weekly_activity_chart(logs_df):
    """
    Generates the weekly activity vertical bar chart.
    Args:
        logs_df (pd.DataFrame): DataFrame containing reading logs.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    if logs_df.empty:
        return None

    df = logs_df.copy()
    df['weekday'] = df['submission_date_dt'].dt.dayofweek
    weekday_map_ar = {
        0: 'الاثنين', 1: 'الثلاثاء', 2: 'الأربعاء', 3: 'الخميس', 
        4: 'الجمعة', 5: 'السبت', 6: 'الأحد'
    }
    df['weekday_ar'] = df['weekday'].map(weekday_map_ar)
    
    weekly_activity = df.groupby('weekday_ar')['total_minutes'].sum().reset_index()
    total_minutes_all = weekly_activity['total_minutes'].sum()
    
    if total_minutes_all == 0:
        return None
        
    weekly_activity['percentage'] = (weekly_activity['total_minutes'] / total_minutes_all) * 100
    
    weekday_order_ar = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']
    weekly_activity['weekday_ar'] = pd.Categorical(weekly_activity['weekday_ar'], categories=weekday_order_ar, ordered=True)
    weekly_activity = weekly_activity.sort_values('weekday_ar')

    fig = px.bar(
        weekly_activity,
        x='weekday_ar',
        y='percentage',
        text=weekly_activity['percentage'].apply(lambda x: f'{x:.1f}%'),
        labels={'weekday_ar': 'يوم الأسبوع', 'percentage': 'نسبة النشاط (%)'},
        color_discrete_sequence=['#27AE60']
    )
    fig = apply_chart_theme(fig, 'bar')
    fig.update_traces(textposition='outside')
    fig.update_layout(
        yaxis_title="النسبة المئوية للنشاط",
        yaxis={'side': 'right'}
    )
    return fig

def create_rhythm_chart(logs_df, full_date_range_df):
    """
    Generates the daily reading rhythm line chart.
    Args:
        logs_df (pd.DataFrame): DataFrame containing reading logs.
        full_date_range_df (pd.DataFrame): DataFrame with a complete date range.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    if logs_df.empty or full_date_range_df.empty:
        return None

    daily_team_minutes = logs_df.groupby(logs_df['submission_date_dt'])['total_minutes'].sum().reset_index()
    merged_team_minutes = pd.merge(full_date_range_df, daily_team_minutes, on='submission_date_dt', how='left').fillna(0)
    merged_team_minutes.rename(columns={'submission_date_dt': 'التاريخ', 'total_minutes': 'مجموع الدقائق'}, inplace=True)
    merged_team_minutes['مجموع الساعات'] = merged_team_minutes['مجموع الدقائق'] / 60
    
    fig = px.line(merged_team_minutes, x='التاريخ', y='مجموع الساعات',
                  labels={'التاريخ': 'التاريخ', 'مجموع الساعات': 'مجموع الساعات المقروءة'},
                  markers=True)
    fig = apply_chart_theme(fig, 'line')
    fig.update_layout(yaxis={'side': 'right'}, xaxis_autorange='reversed')
    return fig

def create_points_leaderboard(member_stats_df):
    """
    Generates the points leaderboard horizontal bar chart.
    Args:
        member_stats_df (pd.DataFrame): DataFrame with aggregated stats per member.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    if member_stats_df.empty or 'name' not in member_stats_df.columns:
        return None
        
    points_leaderboard_df = member_stats_df.sort_values('total_points', ascending=False).head(10)[['name', 'total_points']].rename(columns={'name': 'الاسم', 'total_points': 'النقاط'})
    fig = px.bar(points_leaderboard_df, x='النقاط', y='الاسم', orientation='h', 
                 text='النقاط', color_discrete_sequence=['#8E44AD'])
    fig = apply_chart_theme(fig, 'bar')
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis={'side': 'right', 'autorange': 'reversed'}, xaxis_autorange='reversed')
    return fig

def create_hours_leaderboard(member_stats_df):
    """
    Generates the hours leaderboard horizontal bar chart.
    Args:
        member_stats_df (pd.DataFrame): DataFrame with aggregated stats per member.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    if member_stats_df.empty or 'name' not in member_stats_df.columns:
        return None

    df = member_stats_df.copy()
    df['total_hours'] = (df['total_reading_minutes_common'] + df['total_reading_minutes_other']) / 60
    hours_leaderboard_df = df.sort_values('total_hours', ascending=False).head(10)[['name', 'total_hours']].rename(columns={'name': 'الاسم', 'total_hours': 'الساعات'})
    hours_leaderboard_df['الساعات'] = hours_leaderboard_df['الساعات'].round(1)
    
    fig = px.bar(hours_leaderboard_df, x='الساعات', y='الاسم', orientation='h', 
                   text='الساعات', color_discrete_sequence=['#F39C12'])
    fig = apply_chart_theme(fig, 'bar')
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(yaxis={'side': 'right', 'autorange': 'reversed'}, xaxis_autorange='reversed')
    return fig

def create_focus_donut(stats_df, common_col='total_reading_minutes_common', other_col='total_reading_minutes_other'):
    """
    Generates the reading focus donut chart.
    Args:
        stats_df (pd.DataFrame): DataFrame with aggregated stats. Can be for one or more members.
        common_col (str): The name of the column for common book minutes.
        other_col (str): The name of the column for other book minutes.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    if stats_df.empty:
        return None

    total_common_minutes = stats_df[common_col].sum()
    total_other_minutes = stats_df[other_col].sum()
    
    if total_common_minutes == 0 and total_other_minutes == 0:
        return None
        
    donut_labels = ['الكتاب المشترك', 'الكتب الأخرى']
    donut_values = [total_common_minutes, total_other_minutes]
    
    fig = go.Figure(data=[go.Pie(labels=donut_labels, values=donut_values, hole=.6)])
    fig = apply_chart_theme(fig, 'pie')
    fig.update_layout(
        showlegend=True, 
        legend=dict(x=0.5, y=-0.1, xanchor='center', yanchor='bottom', orientation='h'), 
        margin=dict(t=20, b=20, l=20, r=20), 
        annotations=[dict(text='التوزيع', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    return fig

def create_points_source_donut(points_source_data):
    """
    Generates the points source donut chart for an individual reader.
    Args:
        points_source_data (dict): A dictionary with point sources as keys and point values as values.
    Returns:
        go.Figure or None: The generated Plotly figure, or None if data is insufficient.
    """
    points_source_filtered = {k: v for k, v in points_source_data.items() if v > 0}
    if not points_source_filtered:
        return None

    color_map = {
        'قراءة الكتاب المشترك': '#2980B9', 'قراءة كتب أخرى': '#F39C12',
        'اقتباسات (الكتاب المشترك)': '#27AE60', 'اقتباسات (كتب أخرى)': '#f39c12',
        'إنهاء الكتاب المشترك': '#8E44AD', 'حضور النقاش': '#E74C3C',
        'إنهاء كتب أخرى': '#16a085'
    }
    chart_labels = list(points_source_filtered.keys())
    chart_colors = [color_map.get(label, '#bdc3c7') for label in chart_labels]

    fig = go.Figure(data=[go.Pie(
        labels=chart_labels, values=list(points_source_filtered.values()), 
        hole=.6, textinfo='percent+label', insidetextorientation='radial',
        marker_colors=chart_colors
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    return fig
