import streamlit as st
import base64

def get_base64_of_bin_file(png_file: str) -> str:
    with open(png_file, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_resource
def build_markup_for_logo(png_file: str) -> str:
    binary_string = get_base64_of_bin_file(png_file)
    return f"""
            <style>
                [data-testid="stSidebarHeader"] {{
                    background-image: url("data:image/png;base64,{binary_string}");
                    background-repeat: no-repeat;
                    background-size: contain;
                    background-position: top center;
                    height: 200px;
                }}
            </style>
            """

def get_logo(path):
    st.markdown(
        build_markup_for_logo(path),
        unsafe_allow_html=True,
    )