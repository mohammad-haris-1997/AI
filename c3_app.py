import streamlit as st
from testt1 import main

st.set_page_config(page_title="Excel File Processor")

st.title("Excel File Processor")

# Text input for Excel file path
file_path = st.text_input("Enter the file path for the Excel file")

# Text input for sheet name
sheet_name = st.text_input("Enter the sheet name")

word_file = st.text_input("Enter the word document data")

# Button to execute the main function
if st.button("Process File"):
    if file_path and sheet_name:
        try:
            # Call the main function with the provided file path and sheet name
            main(file_path, sheet_name, word_file)
            st.success("File processed successfully!")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    else:
        st.warning("Please provide both the file path and sheet name.")
