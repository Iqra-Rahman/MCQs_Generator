from src.generator import PDFMCQGenerator
from src.utils import save_to_json

if __name__ == "__main__":
    pdf_path = input("Enter the path to your PDF file: ").strip()
    pdf_path = pdf_path.strip('"').strip("'")
    pdf_path = pdf_path.replace("\\", "/")
    try:
        num_mcqs = int(input("How many MCQs do you want to generate? ").strip())
    except ValueError:
        print("Invalid input. Using default: 100 MCQs")
        num_mcqs = 100

    generator = PDFMCQGenerator()
    pdf_mcqs, keywords = generator.generate_questions(pdf_path, num_mcqs)
    save_to_json(pdf_mcqs, "pdf_mcqs.json")
    save_to_json(keywords, "pdf_keywords.json")