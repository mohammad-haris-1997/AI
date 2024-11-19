import streamlit as st
from prod_llm_excel_main_local_upload import main 
import io
import logging
import base64

logging.basicConfig(
    filename="excel_processor.log", 
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %e(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)

st.set_page_config(page_title="Excel and Word File Processor", page_icon="📑", layout="centered")

# Custom CSS for styling
st.markdown("""
    <style>
    /* Background gradient */
    body {
        background: linear-gradient(to right, #141E30, #243B55);
        background-image: url('https://media.licdn.com/dms/image/v2/D4E1BAQEcKmVEMwmrcQ/company-background_10000/company-background_10000/0/1658118962304/c2_technologies_cover?e=2147483647&v=beta&t=XyScLHoWP3X_Wp2u6l2dOkSL9I1AC6cZbrF269A9nxk');
        color: #FF0000;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;    
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
        background-color: #333
        color: #fff;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #ddd;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    /* Button style */
    .stButton>button {
        background-color: #6c63ff;
        color: #fff;
        cursor: pointer;
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
        margin-top: 20px;
        margin-left: 100px;
        width: 90%;
        max-width: 500px;
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

   .left-links {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .left-links a {
        text-decoration: none;
        font-size: 16px;
        font-weight: bold;
        color: #007BFF;
        margin-bottom: 10px;
    }
    .left-links a:hover {
        color: #0056b3;
        text-decoration: underline;
    }
   
    @media (max-width: 768px) {
    .card {
        width: 95%;  /* Increase width on smaller screens for better use of space */
        padding: 15px;  /* Slightly reduce padding to accommodate smaller screen sizes */
        margin-top: 10px;  /* Reduce margin-top to save space */
    }
}
    </style>
""", unsafe_allow_html=True)

st.title("AI -Driven Requirement Insights Engine")


word_file_path = "/Users/mohammadharis/Downloads/Guidelines_for_the_Excel_Sheet_Setup.docx"
excel_file_path = "/Users/mohammadharis/Downloads/ACTSII_CapsMatrix_CompanyName_Blank.xlsx"

def create_download_link(file_path, file_label):
    with open(file_path, "rb") as file:
        file_data = file.read()
        b64 = base64.b64encode(file_data).decode()
        file_extension = file_path.split(".")[-1]
        return f'<a href="data:application/{file_extension};base64,{b64}" download="{file_path}">{file_label}</a>'


st.markdown(
f"""
    <div class="left-links">
        {create_download_link(word_file_path, "📄File Format Requirements")}
        {create_download_link(excel_file_path, "📊 Click Here to Download Sample Excel Workbook")}
    </div>
    """,
    unsafe_allow_html=True
)

with st.container():
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    sheet_name = st.text_input("Enter the sheet name to process")
    uploaded_word_doc = st.file_uploader("Upload a Word document (optional)", type=["docx"])

if st.button("🚀 Process File"):
    if uploaded_file and sheet_name:
        excel_data = io.BytesIO(uploaded_file.read())
        word_data = io.BytesIO(uploaded_word_doc.read()) if uploaded_word_doc else None
        
        with st.spinner("Please wait while the files are being processed..."):
                    processed_data = main(excel_data, sheet_name, word_data)
        if processed_data:
            st.download_button(
                label="Download Updated Excel File",
                data=processed_data,
                file_name="updated_excel.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Processing failed. Please check the file and sheet name.")
    else:
        st.error("Please upload an Excel file and provide the sheet name.")
