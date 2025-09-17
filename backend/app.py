import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from .src.generator import PDFMCQGenerator
from .src.utils import save_to_json  # optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF MCQ Generator API", version="1.0")

origins = ["http://localhost:5173", "http://localhost:3000", "https://your-render-app-name.onrender.com"
]  

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate")
async def generate_questions(
    file: UploadFile = File(...), 
    num_mcqs: int = Form(...)
):
    """
    Upload a PDF file and generate MCQs.
    """
    generator = PDFMCQGenerator()

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        pdf_path = tmp.name

    try:
        pdf_mcqs, keywords = generator.generate_questions(pdf_path, num_mcqs)
        
        # save_to_json(pdf_mcqs, "pdf_mcqs.json")
        return {"mcqs": pdf_mcqs, "keywords": keywords}
    finally:
        os.unlink(pdf_path)  # Clean up temp file


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
