import streamlit as st
from streamlit_extras.stylable_container import stylable_container

import streamlit as st

# Define card style
card_style = """
    {
        border: 1px groove #52546a;
        border-radius: 10px;
        padding-left: 25px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
"""

def card_testing(cards, num_columns):
    """
    Render a list of cards in a multi-column layout.

    Args:
        cards (list of dict): Each dict contains keys: 'text', 'value', 'delta', and 'help_text'.
        num_columns (int): Number of columns in the layout.
    """
    columns = st.columns(num_columns)

    for index, card in enumerate(cards):
        column = columns[index % num_columns]  # Select the correct column in a round-robin manner
        with column:
            with stylable_container(f"Card-{index}", css_styles=card_style):
                st.metric(card["text"], card["value"], card["delta"], help=card["help_text"])

