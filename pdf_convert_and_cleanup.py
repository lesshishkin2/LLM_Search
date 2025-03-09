from pathlib import Path
import re
import os
import time
import requests
from dotenv import load_dotenv
from config import MD_FILES_PATH, PDF_FILES_PATH
from concurrent.futures import ThreadPoolExecutor


def convert_pdf_to_markdown(pdf_file, source_folder, target_folder, api_key):
    url = "https://www.datalab.to/api/v1/marker"
    headers = {"X-Api-Key": api_key}
    pdf_path = os.path.join(source_folder, pdf_file)
    pdf_name = os.path.basename(pdf_path)
    markdown_file_path = os.path.join(
        target_folder, pdf_file.replace('.pdf', '.md'))

    if os.path.exists(markdown_file_path):
        print(
            f"Markdown file {markdown_file_path} already exists. Skipping conversion for {pdf_file}.")
        return

    with open(pdf_path, 'rb') as f:
        form_data = {
            'file': (pdf_name, f, 'application/pdf'),
            'langs': (None, "en"),
            "force_ocr": (None, False),
            "paginate": (None, True),
            'output_format': (None, 'markdown'),
            "use_llm": (None, False),
            "strip_existing_ocr": (None, False),
            "disable_image_extraction": (None, True)
        }

        try:
            response = requests.post(url, files=form_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    request_check_url = data["request_check_url"]
                    print(
                        f"Conversion started for {pdf_file}. Checking status...")

                    # Poll the request check URL to get the result
                    markdown_content = poll_conversion_status(
                        request_check_url, headers)

                    if markdown_content:
                        # Save the Markdown content to a file
                        with open(markdown_file_path, 'w') as markdown_file:
                            markdown_file.write(markdown_content)
                        print(
                            f"Conversion successful! Saved to {markdown_file_path}")
                    else:
                        print(f"Conversion failed for {pdf_file}.")
                else:
                    print(
                        f"Error during conversion of {pdf_file}: {data.get('error', 'Unknown error')}")
            else:
                print(
                    f"Failed to send request for {pdf_file}. HTTP Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the request for {pdf_file}: {e}")


def poll_conversion_status(check_url, headers, max_polls=300, interval=40):
    for i in range(max_polls):
        time.sleep(interval)
        try:
            response = requests.get(check_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "complete":
                    return data["markdown"]
            else:
                print(
                    f"Failed to check conversion status. HTTP Status: {response.status_code}")
                break
        except requests.exceptions.RequestException as e:
            print(
                f"An error occurred while polling for conversion status: {e}")
            break

    print("Conversion did not complete in time.")
    return None


def clean_md_file(path):
    """
    Opens the markdown file at the given path, removes all occurrences of 
    the pattern <span id="{anything}"></span> using a regular expression, 
    and saves the cleaned content back to the same file.
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove any HTML span tags with an id attribute, where the id can be any string.
    cleaned_content = re.sub(r'<span id="[^"]*"></span>', '', content)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    print(f"Cleaned file: {path}")


if __name__ == "__main__":
    load_dotenv()

    api_key = os.getenv("MARKER_API_KEY")
    source_folder = PDF_FILES_PATH
    target_folder = MD_FILES_PATH

    pdf_files = [file for file in os.listdir(
        source_folder) if file.endswith('.pdf')]

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(convert_pdf_to_markdown, file,
                                   source_folder, target_folder, api_key) for file in pdf_files]
        for future in futures:
            future.result()

    # remove <span id=...></span>
    for filename in os.listdir(target_folder):
        if filename.endswith('.md'):
            full_path = os.path.join(target_folder, filename)
            clean_md_file(full_path)
