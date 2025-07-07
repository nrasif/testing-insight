# components/charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from streamlit_extras.stylable_container import stylable_container


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Local Imports ---
from utils.helpers import truncate_feature_name
from config import (
    SEVERITY_COLORS, TICKET_STATE_COLORS, ACTIVITY_CHART_COLORS,
    LIFECYCLE_CHART_COLORS, STATUS_CATEGORIES, PLOT_CONTAINER_STYLE
)

# --- Chart 1: Severity per Feature ---
def render_severity_per_feature_chart(df: pd.DataFrame):
    """Renders a horizontal bar chart for severity per feature."""
    with stylable_container(key="severity_chart_container", css_styles=PLOT_CONTAINER_STYLE):
        st.markdown(':material/device_thermostat: **Severity per Feature**',
                    help='Shows ticket count and severity for each feature.')

        if df.empty:
            st.info("No data to display for Severity per Feature.")
            return

        valid_status = ['Highest', 'Medium', 'Low']
        df_chart = df[df['Severity'].isin(valid_status)].copy()

        if df_chart.empty:
            st.info("No tickets with 'Highest', 'Medium', or 'Low' severity found.")
            return

        chart_data = df_chart.groupby(['Feature', 'Severity']).size().reset_index(name='Total Tickets')
        chart_data['Feature_Display'] = chart_data['Feature'].apply(truncate_feature_name)

        plot_height = max(400, len(chart_data['Feature'].unique()) * 40)

        fig = px.bar(
            chart_data,
            x='Total Tickets',
            y='Feature_Display',
            color='Severity',
            orientation='h',
            color_discrete_map=SEVERITY_COLORS,
            height=plot_height,
            labels={'Feature_Display': 'Feature'},
            custom_data=['Feature']
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            legend_title_text='Severity',
            xaxis=dict(showgrid=True),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig.update_traces(
            hovertemplate="<b>Feature: %{customdata[0]}</b><br>Severity: %{fullData.name}<br>Total Tickets: %{x}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


# --- Chart 2: Ticket Status Overview ---
def render_ticket_status_overview_chart(df: pd.DataFrame):
    """Renders a stacked bar chart showing ticket states (Open, Closed, Invalid) per feature."""
    with stylable_container(key="status_overview_container", css_styles=PLOT_CONTAINER_STYLE):
        st.markdown(':material/confirmation_number: **Ticket Status Overview**',
                    help='Composition of open, closed, and invalid tickets for each feature.')

        if df.empty:
            st.info("No data available for Ticket Status Overview.")
            return

        df_plot = df.copy()

        def categorize_ticket_state(status):
            if status in STATUS_CATEGORIES['resolved']: return 'Closed'
            if status in STATUS_CATEGORIES['invalid']: return 'Invalid'
            return 'Open'

        df_plot['Ticket_State'] = df_plot['Status'].apply(categorize_ticket_state)

        # Ensure 'Feature' column exists and is not all NaN
        if 'Feature' not in df_plot.columns or df_plot['Feature'].isnull().all():
            st.info("No 'Feature' data available to generate the status overview chart.")
            return

        feature_order = df_plot['Feature'].value_counts().index
        chart_data = df_plot.groupby(['Feature', 'Ticket_State']).size().reset_index(name='Count')
        pivot_df = chart_data.pivot(index='Feature', columns='Ticket_State', values='Count').fillna(0).reindex(feature_order)
        truncated_labels = pivot_df.index.map(lambda name: truncate_feature_name(name, max_words=2))

        fig = go.Figure()
        status_order = ['Closed', 'Invalid', 'Open']

        for status in status_order:
            if status in pivot_df.columns:
                fig.add_trace(go.Bar(
                    name=status,
                    x=truncated_labels,
                    y=pivot_df[status],
                    hovertext=pivot_df.index,
                    marker_color=TICKET_STATE_COLORS[status],
                    text=pivot_df[status].apply(lambda x: int(x) if x > 0 else ''),
                    textposition='inside',
                    textfont_color='white',
                    hovertemplate='<b>%{hovertext}</b><br>' + f'{status}: %{{y}}<extra></extra>'
                ))

        fig.update_layout(
            barmode='stack',
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, categoryorder='array', categoryarray=list(truncated_labels)),
            yaxis=dict(showgrid=True, visible=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=450,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)


# --- Chart 3: Daily Activity Chart ---
@st.cache_data
def prepare_daily_activity_data(df):
    all_events = []
    if 'Status_History_JSON' not in df.columns:
        return pd.DataFrame()
    for _, row in df.iterrows():
        history_str = row.get('Status_History_JSON')
        if not history_str or not isinstance(history_str, str): continue
        try:
            history = json.loads(history_str)
            if not isinstance(history, list): continue
            for event in history:
                ts = pd.to_datetime(event.get('timestamp'))
                s_to = event.get('status_to')
                s_from = event.get('status_from')
                if s_from is None or s_to in STATUS_CATEGORIES['reopen']:
                    all_events.append({'date': ts.date(), 'type': 'open'})
                elif s_to in STATUS_CATEGORIES['resolved']:
                    all_events.append({'date': ts.date(), 'type': 'solved'})
                elif s_to in STATUS_CATEGORIES['invalid']:
                    all_events.append({'date': ts.date(), 'type': 'invalid'})
        except (json.JSONDecodeError, TypeError):
            continue
    if not all_events: return pd.DataFrame()

    events_df = pd.DataFrame(all_events)
    daily_counts = events_df.groupby(['date', 'type']).size().unstack(fill_value=0)
    for col in ['open', 'solved', 'invalid']:
        if col not in daily_counts: daily_counts[col] = 0

    full_range = pd.date_range(start=daily_counts.index.min(), end=daily_counts.index.max(), freq='D')
    return daily_counts.reindex(full_range, fill_value=0)

def render_daily_activity_chart(df: pd.DataFrame):
    """Renders a line chart for daily ticket activity."""
    with stylable_container(key="daily_activity_container", css_styles=PLOT_CONTAINER_STYLE):
        st.markdown("**:material/show_chart: Daily Ticket Activity**",
                    help="Daily number of tickets opened/reopened vs. solved/invalidated.")

        if df.empty:
            st.info("Filter data to see daily activity.")
            return

        daily_df = prepare_daily_activity_data(df)

        if daily_df.empty:
            st.info("No valid ticket history to generate activity plot.")
            return

        fig = go.Figure()
        traces = {
            'open': {'name': 'Opened/Reopened', 'fill': 'tozeroy', 'color': ACTIVITY_CHART_COLORS['open'], 'fillcolor': 'rgba(226, 79, 79, 0.1)'},
            'solved': {'name': 'Solved', 'fill': 'tozeroy', 'color': ACTIVITY_CHART_COLORS['solved'], 'fillcolor': 'rgba(36, 178, 76, 0.2)'},
            'invalid': {'name': 'Invalid', 'fill': None, 'color': ACTIVITY_CHART_COLORS['invalid'], 'dash': 'dot'}
        }

        for key, props in traces.items():
            fig.add_trace(go.Scatter(
                x=daily_df.index, y=daily_df[key], name=props['name'], mode='lines',
                line=dict(width=3, color=props['color'], shape='spline', dash=props.get('dash')),
                fill=props.get('fill'), fillcolor=props.get('fillcolor'),
                hovertemplate=f"<b>{props['name']}: %{{y}}</b><br>Date: %{{x|%d %b %Y}}<extra></extra>"
            ))

        fig.update_layout(
            template='plotly_white', hovermode='x unified',
            xaxis=dict(rangeslider=dict(visible=True, thickness=0.1), showgrid=True),
            yaxis=dict(title='Daily Ticket Count', side='right', showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=70, b=0), height=450
        )
        st.plotly_chart(fig, use_container_width=True)


# --- Chart 4: Cumulative Lifecycle Chart ---
@st.cache_data
def prepare_ticket_lifecycle_data(df):
    opened_dates, closed_dates = [], []
    if 'Status_History_JSON' not in df.columns:
        return pd.DataFrame()
    for _, row in df.iterrows():
        history_str = row.get('Status_History_JSON')
        if not history_str or not isinstance(history_str, str): continue
        try:
            history = json.loads(history_str)
            if not isinstance(history, list) or not history: continue
            history.sort(key=lambda x: pd.to_datetime(x.get('timestamp')))
            if history[0].get('status_from') is None:
                opened_dates.append(pd.to_datetime(history[0]['timestamp']).date())
            if history[-1].get('status_to') in STATUS_CATEGORIES['final_closed']:
                closed_dates.append(pd.to_datetime(history[-1]['timestamp']).date())
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    if not opened_dates: return pd.DataFrame()

    daily_df = pd.DataFrame({
        'open': pd.Series(opened_dates).value_counts(),
        'closed': pd.Series(closed_dates).value_counts()
    }).fillna(0)

    if daily_df.empty: return pd.DataFrame()

    full_range = pd.date_range(start=daily_df.index.min(), end=daily_df.index.max(), freq='D')
    daily_df = daily_df.reindex(full_range, fill_value=0)

    return daily_df.cumsum().rename(columns={'open': 'opened_cumulative', 'closed': 'closed_cumulative'})

def render_cumulative_lifecycle_chart(df: pd.DataFrame):
    """Renders a cumulative line chart of opened vs. closed tickets."""
    with stylable_container(key="cumulative_chart_container", css_styles=PLOT_CONTAINER_STYLE):
        st.markdown("**:material/waterfall_chart: Cumulative Opened vs Closed Tickets**",
                    help="Cumulative count of unique tickets opened vs. finally closed.")

        if df.empty:
            st.info("Filter data to see ticket lifecycle.")
            return

        lifecycle_df = prepare_ticket_lifecycle_data(df)

        if lifecycle_df.empty:
            st.info("No valid ticket history for lifecycle analysis.")
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=lifecycle_df.index, y=lifecycle_df['opened_cumulative'], name='Opened (Cumulative)',
            line=dict(width=3.5, color=LIFECYCLE_CHART_COLORS['opened'], shape='spline'),
            fill='tozeroy', fillcolor='rgba(226, 79, 79, 0.1)',
            hovertemplate='<b>Total Opened: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=lifecycle_df.index, y=lifecycle_df['closed_cumulative'], name='Closed (Cumulative)',
            line=dict(width=3.5, color=LIFECYCLE_CHART_COLORS['closed'], shape='spline'),
            fill='tozeroy', fillcolor='rgba(36, 178, 76, 0.2)',
            hovertemplate='<b>Total Closed: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
        ))
        fig.update_layout(
            template='plotly_white', hovermode='x unified',
            xaxis=dict(rangeslider=dict(visible=True, thickness=0.08), showgrid=True),
            yaxis=dict(title='Cumulative Unique Tickets', side='right', showgrid=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=70, b=0), height=450
        )
        st.plotly_chart(fig, use_container_width=True)


# --- Chart 5: Ticket Distribution Bubble Chart ---
def render_ticket_distribution_bubble_chart(df: pd.DataFrame):
    """Creates and displays a bubble chart for ticket distribution."""
    bubble_chart_style = PLOT_CONTAINER_STYLE.replace("height: 500px;", "height: 1015px;")
    with stylable_container(key="bubble_chart_container_main", css_styles=bubble_chart_style):
        st.markdown(':material/bubble_chart: **Ticket Distribution by Feature, Status, and Squad**',
                    help='Visualizes ticket density by feature, status, and squad.')

        if df.empty:
            st.info("Not enough data for bubble chart. Ensure tickets have 'Feature', 'Squad', and 'Status'.")
            return

        df_chart = df.copy()
        df_chart['Squad'] = df_chart['Squad'].fillna('Unclassified')
        df_chart.dropna(subset=['Feature', 'Status'], inplace=True)

        if df_chart.empty:
            st.info("Data is missing required 'Feature' or 'Status' values for the bubble chart.")
            return

        bubble_data = df_chart.groupby(['Feature', 'Squad', 'Status']).size().reset_index(name='Total Tickets')
        bubble_data['Feature_Display'] = bubble_data['Feature'].apply(lambda name: truncate_feature_name(name, max_words=3))

        fig = px.scatter(
            bubble_data,
            x='Status',
            y='Feature_Display',
            size='Total Tickets',
            color='Squad',
            size_max=50,
            labels={"Status": "Ticket Status", "Feature_Display": "Features", "Total Tickets": "Total Tickets"},
            custom_data=['Feature', 'Squad', 'Total Tickets']
        )

        # Add annotations for totals
        status_totals = bubble_data.groupby('Status')['Total Tickets'].sum()
        for status, total in status_totals.items():
            fig.add_annotation(x=status, y=1.05, yref="paper", text=f"<b>{total}</b>", showarrow=False, font=dict(size=14))

        feature_totals = bubble_data.groupby('Feature_Display')['Total Tickets'].sum()
        for feature, total in feature_totals.items():
            fig.add_annotation(x=1.02, xref="paper", y=feature, text=f"<b>{total}</b>", showarrow=False, xanchor='left', font=dict(size=12))

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)', categoryorder='total ascending'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=60, t=70, b=20),
            height=940
        )
        fig.update_traces(
            hovertemplate="<b>Feature: %{customdata[0]}</b><br>Status: %{x}<br>Squad: %{customdata[1]}<br>Total Tickets: %{customdata[2]}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)