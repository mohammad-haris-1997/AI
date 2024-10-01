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

# Set page configuration
st.set_page_config(page_title="Excel and Word File Processor")

# Title
st.title("Excel and Word File Processor")

# Function to validate file existence
def validate_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Provided path is not a file: {file_path}")

# Text input for Excel file path
file_path = st.text_input("Enter the file path for the Excel file", value="", placeholder="e.g. /path/to/your/excel.xlsx")

# Text input for sheet name
sheet_name = st.text_input("Enter the sheet name", value="")

# Text input for Word document data
word_file = st.text_input("Enter the file path for the Word document (optional)", value="", placeholder="e.g. /path/to/your/document.docx")

# Button to execute the main function
if st.button("Process Files"):
    if file_path and sheet_name:
        try:
            # Validate file paths
            validate_file(file_path)
            if word_file:
                validate_file(word_file)
            
            # Log the inputs
            logging.info(f"Processing Excel file: {file_path} and Word file: {word_file}")

            # Call the main function with the provided file path, sheet name, and word file
            result = main(file_path, sheet_name, word_file)

            # If no exception occurs, display success
            if result:
                st.success("Files processed successfully!")
                logging.info("Files processed successfully")
            else: 
                st.error("There's an error in Filename, Sheet name or in the code")
                logging.error("An error has occured")

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
        st.warning("Please provide both the file path and sheet name.")
        logging.warning("Missing file path or sheet name.")
