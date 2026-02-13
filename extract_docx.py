from docx import Document

def extract_text(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text.strip())
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading file: {e}"

if __name__ == "__main__":
    file_path = "MITU SKILLOGIES WEBSITE DATA.docx"
    content = extract_text(file_path)
    with open("extracted_data.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Succesfully wrote content to extracted_data.txt")
