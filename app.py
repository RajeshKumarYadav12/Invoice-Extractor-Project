# Import necessary libraries
from dotenv import load_dotenv  # Import function to load environment variables from .env file
import streamlit as st  # Import Streamlit for building interactive web applications
import os  # Import os module for operating system functionalities
from PIL import Image  # Import Image class from Python Imaging Library (PIL)
import requests  # Import requests module for making HTTP requests
import fitz  # Import PyMuPDF for working with PDF files
import io  # Import io module for handling input/output operations
import google.generativeai as genai  # Import Google's Generative AI module

# Load environment variables from .env file
load_dotenv()

# Configure Google Generative AI with API key fetched from environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get response from Generative AI
def get_generative_ai_response(prompt):
    response = genai.generate_text(
        model="models/text-bison-001",  # Ensure the correct model name is used
        prompt=prompt
    )
    return response.result.strip()  # Strip any leading/trailing whitespace

# Function to extract text from images using OCR.space API
def extract_text_from_images(images):
    text = ""
    ocr_api_key = os.getenv("OCR_API_KEY")
    ocr_api_url = "https://api.ocr.space/parse/image"
    
    for image in images:
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        
        response = requests.post(
            ocr_api_url,
            files={"filename": ("image.png", image_bytes)},
            data={"apikey": ocr_api_key}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ParsedResults"):
                text += result["ParsedResults"][0]["ParsedText"] + "\n"
            else:
                text += "Error: Could not parse image.\n"
        else:
            text += f"Error: API request failed with status code {response.status_code}.\n"
    return text

# Function to extract images from PDF
def extract_images_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")  # Open PDF file using PyMuPDF
    images = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))  # Open image from byte stream
            images.append(image)
    return images

# Initialize Streamlit app
st.set_page_config(page_title="Invoice Data Extraction")  # Set Streamlit page title

# Display header for the application
st.header("Invoice Data Extraction Application")

# Input prompt for the user
input_text = st.text_input("Input Prompt: ", key="input")

# File uploader for uploading PDF invoices
uploaded_file = st.file_uploader("Choose an invoice PDF...", type=["pdf"])

# List to store extracted images from PDF
images = []

# If a PDF file is uploaded, attempt to extract images
if uploaded_file is not None:
    try:
        images = extract_images_from_pdf(uploaded_file)  # Extract images from PDF
        for img in images:
            st.image(img, caption="Extracted Image", use_column_width=True)  # Display extracted images
    except Exception as e:
        st.error(f"An error occurred while extracting images from PDF: {e}")  # Display error if extraction fails

# Button to trigger information extraction
submit = st.button("Extract Information")

# Prompt text for the user
input_prompt = """
               You are an expert in understanding invoices.
               You will receive input images as invoices & you will have to answer questions based on the input image.
               Please provide the invoice number and total cost.
               """

# When the "Extract Information" button is clicked
if submit:
    try:
        if not images:
            raise FileNotFoundError("No images extracted from the uploaded PDF")  # Raise error if no images are extracted
        
        # Extract text from images
        extracted_text = extract_text_from_images(images)
        
        # Combine prompt with extracted text and user input
        combined_prompt = input_prompt + "\n\nExtracted Text:\n" + extracted_text + "\n\n" + input_text
        
        # Get response from Generative AI
        response = get_generative_ai_response(combined_prompt)
        
        # Display extracted information header and response
        st.subheader("Extracted Information")
        st.write(response)
    
    except Exception as e:
        st.error(f"An error occurred: {e}")  # Display error message if any exception occurs
