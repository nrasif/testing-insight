import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def allRegression_proc(path):
    df = pd.read_excel(path)
    df.ffill(inplace=True)
    df[['Target Execution', 'Execution', 'Passed', 'Failed']] = df[['Target Execution', 'Execution', 'Passed', 'Failed']].applymap(lambda x: x*100).astype(float)
    df["Tanggal"] = pd.to_datetime(df["Tanggal"], format="%m/%d/%Y")
    
    df_android = df[df['OS'] == 'Android']
    df_ios = df[df['OS'] == 'iOS']
    
    return df_android, df_ios

def allProgress_stacked():
    options = ['Android', 'iOS']
    selection = st.pills('', options, selection_mode='single', default=options[0], label_visibility='hidden')

    df_android, df_ios = allRegression_proc(path='./data/data_allregresion.xlsx')

    if selection and selection[0] == 'Android':
        df_selected = df_android
    else:
        df_selected = df_ios

    # Ensure 'Other' is non-negative
    df_selected['Other'] = (df_selected['Execution'] - df_selected['Passed'] - df_selected['Failed']).clip(lower=0)

    # Create figure
    fig = go.Figure()

    # Stacked Bar: Passed
    fig.add_trace(go.Bar(
        x=df_selected['Tanggal'],
        y=df_selected['Passed'],
        name='Passed',
        marker_color='#79B791',
        text=df_selected['Passed'].apply(lambda x: f"{x:.2f}%"),
        textposition='inside',
        textfont=dict(size=14, color='black'),
        hoverinfo='text',
        hovertext=df_selected['Passed'].apply(lambda x: f'Passed: {x:.2f}%')
    ))

    # Stacked Bar: Failed
    fig.add_trace(go.Bar(
        x=df_selected['Tanggal'],
        y=df_selected['Failed'],
        name='Failed',
        marker_color='#d1807d',
        text=df_selected['Failed'].apply(lambda x: f"{x:.2f}%"),
        textposition='inside',
        textfont=dict(size=14, color='black'),
        hoverinfo='text',
        hovertext=df_selected['Failed'].apply(lambda x: f'Failed: {x:.2f}%')
    ))

    # Stacked Bar: Other
    fig.add_trace(go.Bar(
        x=df_selected['Tanggal'],
        y=df_selected['Other'],
        name='Other',
        marker_color='#AAAAAA',
        text=df_selected['Other'].apply(lambda x: f"{x:.2f}%"),
        textposition='inside',
        textfont=dict(size=14, color='black'),
        hoverinfo='text',
        hovertext=df_selected['Other'].apply(lambda x: f'Other: {x:.2f}%')
    ))

    # Execution Line
    fig.add_trace(go.Scatter(
        x=df_selected['Tanggal'],
        y=df_selected['Execution'],
        name='Execution',
        mode='lines+markers',
        line=dict(color='#3C5D7C', width=3),
        hoverinfo='text',
        hovertext=df_selected['Execution'].apply(lambda x: f'Execution: {x:.2f}%')
    ))

    # Target Execution Line
    fig.add_trace(go.Scatter(
        x=df_selected['Tanggal'],
        y=df_selected['Target Execution'],
        name='Target',
        mode='lines+markers',
        line=dict(color='#555555', width=2, dash='dash'),
        hoverinfo='text',
        hovertext=df_selected['Target Execution'].apply(lambda x: f'Target: {x:.2f}%')
    ))

    # Layout Customization
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
        dtick="D1",  # Daily ticks if you want all dates visible
        tickformat='%d %b',
        showgrid=True,
        ticks='outside'
    )
    
    fig.update_yaxes(range=[0,110])

    # Update text for better readability and ensure text is centered only for bar traces
    fig.update_traces(selector=dict(type='bar'), textposition="inside", insidetextanchor="middle", textfont_size=12)

    return st.plotly_chart(fig, theme=None, use_container_width=True)

if __name__ == "__main__":
    allProgress_stacked()