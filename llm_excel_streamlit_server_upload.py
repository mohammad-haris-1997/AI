import streamlit as st
from prod_llm_excel_main import main
import logging
import os

# Configure logging
logging.basicConfig(
    filename="excel_processor.log", 
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Set page configuration with custom favicon and layout
st.set_page_config(page_title="Excel and Word File Processor", page_icon="📑", layout="centered")

# Custom CSS for styling
st.markdown("""
    <style>
    /* Background gradient */
    body {
        background: linear-gradient(to right, #141E30, #243B55);
        color: #FF0000;
    }
    /* Center the main container */
    .stApp {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    /* Title style */
    h1 {
        font-family: Arial, sans-serif;
        font-size: 2.1em;
        color: #f9f9f9;
        text-shadow: 1px 1px 2px #000;
    }
    /* Input box styles */
    .stTextInput, .stButton {
        background: #2F2F2F;
        color: #333;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    /* Button style */
    .stButton>button {
        background-color: #6c63ff;
        color: #fff;
        font-weight: bold;
        border: None;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #5548c8;
    }
    /* Card style */
    .card {
        background-color: #243B55;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.5);
    }
    /* Increase font size for input labels */
    .large-text {
        font-size: 1.2em; /* Adjust this size as needed */
        color: #f0f0f5; /* Change color for contrast */
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📑 AI-Driven Requirement Insights Engine")

# Function to validate file existence
def validate_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Provided path is not a file: {file_path}")

# File input form in a card layout
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Larger font text labels
    st.markdown('<p class="large-text">🔍 Enter the file path for the Excel file</p>', unsafe_allow_html=True)
    st.text_input("", value="", placeholder="e.g. /path/to/your/excel.xlsx", key="excel_path")

    st.markdown('<p class="large-text">📄 Enter the sheet name</p>', unsafe_allow_html=True)
    st.text_input("", value="",placeholder="e.g. Sheet1", key="sheet_name")

    st.markdown('<p class="large-text">📃 Enter the file path for the Word document</p>', unsafe_allow_html=True)
    st.text_input("", value="", placeholder="e.g. /path/to/your/document.docx", key="word_file")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Button to execute the main function
if st.button("🚀 Process Files"):
    file_path = st.session_state.get("excel_path", "")
    sheet_name = st.session_state.get("sheet_name", "")
    word_file = st.session_state.get("word_file", "")
    
    if file_path and sheet_name:
        try:
            # Validate file paths
            validate_file(file_path)
            if word_file:
                validate_file(word_file)
            
            # Log the inputs
            logging.info(f"Processing Excel file: {file_path} and Word file: {word_file}")

            # Call the main function with the provided file path, sheet name, and word file
            main(file_path, sheet_name, word_file)

            # Display success message
            st.success("✅ Files processed successfully!")
            logging.info("Files processed successfully")

        except FileNotFoundError as fnf_error:
            st.error(f"File not found: {fnf_error}")
            logging.error(f"File not found: {fnf_error}")

        except ValueError as ve_error:
            st.error(f"Validation error: {ve_error}")
            logging.error(f"Validation error: {ve_error}")

        except Exception as e:
            # Log the full stack trace in the log and show a user-friendly message on the front end
            logging.exception(f"Error processing files: {str(e)}")
            st.error(f"Error processing file: {str(e)}")

    else:
        st.warning("⚠️ Please provide both the file path and sheet name.")
        logging.warning("Missing file path or sheet name.")
