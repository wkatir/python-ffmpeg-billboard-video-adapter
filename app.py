import streamlit as st
import pandas as pd

st.set_page_config(page_title="My App", page_icon="📊", layout="centered")

st.write(
    """
    # My first app
    Hello *world!*
    """
)

# Example data
_df = pd.DataFrame({
    "category": list("ABCDEFGH"),
    "sales": [10, 20, 35, 50, 40, 60, 80, 55],
})

# Widgets
number = st.slider("Pick a number", 0, 100, 25)
color = st.color_picker("Pick a color", "#4CAF50")
date = st.date_input("Pick a date")
file = st.file_uploader("Pick a file")
pet = st.radio("Pick a pet", ["Dog", "Cat", "Bird"]) 

st.write("You picked:", number, color, date, pet)

st.bar_chart(_df, x="category", y="sales")
