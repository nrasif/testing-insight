import streamlit as st
from streamlit_extras.stylable_container import stylable_container

def display_summary_metrics(
    total_tickets,
    total_open_tickets, 
    total_solved_tickets, 
    total_invalid_ticket, 
    formatted_avg_duration,
    metric_card_style
):
    """
    Menampilkan 4 metrik utama dalam kolom dengan style kustom.

    Args:
        total_open_tickets (int): Jumlah tiket yang masih open.
        total_solved_tickets (int): Jumlah tiket yang sudah solved.
        total_invalid_ticket (int): Jumlah tiket yang invalid.
        formatted_avg_duration (str): Rata-rata waktu penyelesaian yang sudah diformat.
        metric_card_style (str): String CSS untuk styling container metrik.
    """
    
    # Membuat 4 kolom untuk menampung metrik
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        with stylable_container(
            key="total_tickets_metric",
            css_styles=metric_card_style
        ):
            st.metric(
                label="Total Tickets",
                value=f"{total_tickets}",
                help='All tickets including open, closed, and invalid tickets'
            )

    with col2:
        with stylable_container(
            key="open_tickets_metric",
            css_styles=metric_card_style  # Menggunakan style yang di-passing
        ):
            st.metric(
                label="Total Open Tickets", 
                value=f"{total_open_tickets}", 
                help='Ticket that is not solved with status include everything except "Resolve" and "Invalid"'
            )

    with col3:
        with stylable_container(
            key="solved_tickets_metric",
            css_styles=metric_card_style  # Menggunakan style yang sama
        ):
            st.metric(
                label="Solved Tickets", 
                value=f"{total_solved_tickets}", 
                help='Ticket that is solved'
            )
            
    with col4:
        with stylable_container(
            key="invalid_tickets_metric",
            css_styles=metric_card_style  # Menggunakan style yang sama
        ):
            st.metric(
                label="Invalid Ticket", 
                value=f"{total_invalid_ticket}", 
                help='Ticket that is Invalid'
            )

    with col5:
        with stylable_container(
            key="average_tickets_metric",
            css_styles=metric_card_style  # Menggunakan style yang sama
        ):
            st.metric(
                label="Average Time to Solved", 
                value=formatted_avg_duration, 
                help='Average time for ticket to solved or closed'
            )