import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.uat_progress import uatProgress_proc


@st.cache_data  # Cache the plotting to avoid regeneration if data hasn't changed
def plot_data(df_selected):
    df_selected['Other'] = (df_selected['Execution'] - df_selected['Passed'] - df_selected['Failed']).clip(lower=0)
    
    fig = go.Figure()

    categories = ['Passed', 'Failed', 'Other']
    colors = ['#79B791', '#d1807d', '#AAAAAA']
    
    for category, color in zip(categories, colors):
        fig.add_trace(go.Bar(
            x=df_selected['Tanggal'],
            y=df_selected[category],
            name=category,
            marker_color=color,
            text=df_selected[category].apply(lambda x: f"{x:.2f}%"),
            textposition='inside',
            textfont=dict(size=14, color='black'),
            hoverinfo='text',
            hovertext=df_selected[category].apply(lambda x: f'{category}: {x:.2f}%')
        ))

    fig.add_trace(go.Scatter(
        x=df_selected['Tanggal'],
        y=df_selected['Execution'],
        name='Execution',
        mode='lines+markers',
        line=dict(color='#3C5D7C', width=3),
        hoverinfo='text',
        hovertext=df_selected['Execution'].apply(lambda x: f'Execution: {x:.2f}%')
    ))

    fig.add_trace(go.Scatter(
        x=df_selected['Tanggal'],
        y=df_selected['Target Execution'],
        name='Target',
        mode='lines+markers',
        line=dict(color='#555555', width=2, dash='dash'),
        hoverinfo='text',
        hovertext=df_selected['Target Execution'].apply(lambda x: f'Target: {x:.2f}%')
    ))

    fig.update_layout(
        xaxis_title='<b style="font-family:Radio Canada;">Date</b>',
        yaxis_title='<b style="font-family:Radio Canada;">Percentage (%)</b>',
        barmode='stack',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1,
            xanchor='center',
            x=0.5,
            font=dict(size=14)
        ),
        width=1000,
        height=500,
        plot_bgcolor='#F6F6F6',
        margin=dict(l=40, r=40, t=0, b=50),
        xaxis=dict(title_font=dict(size=16, color='black')),
        yaxis=dict(title_font=dict(size=16, color='black'))
    )
    
    fig.update_xaxes(
        tickmode='linear',
        tick0=df_selected['Tanggal'].min(),
        dtick="D1",
        tickformat='%d %b',
        showgrid=True,
        ticks='outside'
    )
    
    fig.update_yaxes(range=[0,110])
    fig.update_traces(selector=dict(type='bar'), textposition="inside", insidetextanchor="middle", textfont_size=12)

    return fig
@st.fragment
def uatProgress_stacked():
    options = ['Android', 'iOS']
    
    selection = st.pills('', options, selection_mode='single', default=options[0], label_visibility='hidden')

    df = uatProgress_proc(path='./data/uat_progress.xlsx')
    df_selected = df[df['OS'] == selection]

    if not df_selected.empty:
        fig = plot_data(df_selected)
        st.plotly_chart(fig, theme=None, use_container_width=True)
    else:
        st.write(f"Please choose the OS platform")

if __name__ == "__main__":
    uatProgress_stacked()