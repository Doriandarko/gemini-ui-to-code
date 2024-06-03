import streamlit as st
import pathlib
from PIL import Image
import google.generativeai as genai

# Configure the API key directly in the script
API_KEY = 'YOUR GEMINI KEY'
genai.configure(api_key=API_KEY)

# Generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Create the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction="Describe this UI in accurate details. When you reference a UI element put its name and bounding box in the format: [object name (y_min, x_min, y_max, x_max)]. Also Describe the color of the elements.",
)

# Function to refine the description with image
def refine_description_with_image(description, image_path):
    model_refine_description = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction="Compare the described UI elements with the provided image and identify any missing elements or inaccuracies. Also Describe the color of the elements. Provide a refined and accurate description of the UI elements based on this comparison.",
    )
    chat_session_refine_description = model_refine_description.start_chat(history=[])
    image_input = {
        'mime_type': 'image/jpeg',
        'data': pathlib.Path(image_path).read_bytes()
    }
    response_refine_description = chat_session_refine_description.send_message([description, image_input])
    return response_refine_description.text

# Function to generate HTML from description
def generate_html(description):
    model_html = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction="Create an HTML file based on the following UI description, using the UI elements described in the previous response. Include inline CSS within the HTML file to style the elements. Make sure the colors used are the same as the original UI. The UI needs to be responsive and mobile-first, matching the original UI as closely as possible. Do not include any explanations or comments. ONLY return the HTML code with inline CSS.",
    )
    chat_session_html = model_html.start_chat(history=[])
    response_html = chat_session_html.send_message("Generate an HTML file with inline CSS for the described UI: " + description)
    return response_html.text

# Function to refine HTML
def refine_html(description, initial_html):
    model_refine = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction="Validate the following HTML code based on the UI description and provide a refined version of the HTML code with inline CSS that improves accuracy, responsiveness, and adherence to the original design. ONLY return the refined HTML code with inline CSS.",
    )
    chat_session_refine = model_refine.start_chat(history=[])
    response_refine = chat_session_refine.send_message("Refine the HTML code based on the description and the initial HTML code: " + initial_html)
    return response_refine.text

# Streamlit app
def main():
    st.title("Gemini 1.5 Pro, UI to Code 👨‍💻 ")
    st.subheader('Made with ❤️ by [Skirano](https://cursor.sh/)')

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            # Load and display the image
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Image.', use_column_width=True)

            # Convert image to RGB mode if it has an alpha channel
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # Save the uploaded image temporarily
            temp_image_path = pathlib.Path("temp_image.jpg")
            image.save(temp_image_path, format="JPEG")

            # Generate UI description
            if st.button("Describe UI"):
                st.write("🧑‍💻 Looking at your UI...")
                prompt = "Analyze this image and describe the UI elements in detail."
                image_input = {
                    'mime_type': 'image/jpeg',
                    'data': temp_image_path.read_bytes()
                }
                response = model.start_chat(history=[]).send_message([prompt, image_input])
                description = response.text
                st.write(description)

                # Refine the description
                st.write("🔍 Refining description with visual comparison...")
                refined_description = refine_description_with_image(description, temp_image_path)
                st.write(refined_description)

                # Generate HTML
                st.write("🛠️ Generating website...")
                initial_html = generate_html(refined_description)
                st.code(initial_html, language='html')

                # Refine HTML
                st.write("🔧 Refining website...")
                refined_html = refine_html(refined_description, initial_html)
                st.code(refined_html, language='html')

                # Save the refined HTML to a file
                with open("index.html", "w") as file:
                    file.write(refined_html)
                st.success("HTML file 'index.html' has been created.")

                # Provide download link for HTML
                st.download_button(label="Download HTML", data=refined_html, file_name="index.html", mime="text/html")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
