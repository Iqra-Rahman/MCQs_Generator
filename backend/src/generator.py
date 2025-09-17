import math
import random
import time
import re
from typing import List, Set, Tuple
import google.generativeai as genai
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
import json

from src.config import GOOGLE_API_KEY
from src.models import MCQItem
from src.utils import should_exclude_chunk, clean_json_response, save_to_json


class PDFMCQGenerator:
    def __init__(self, model="gemini-1.5-flash", temperature=0.7):
        """Initialization"""
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(model)  # ✅ Now using Gemini correctly
        self.temperature = temperature
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50
        )
        self.retry_count = 5
        self.mcqs_per_chunk = 2
        self.successful_chunks = 0
        self.failed_chunks = 0
        self.important_keywords: Set[str] = set()

    def extract_keywords(self, document) -> Set[str]:
        """Extract important keywords from the document using Gemini"""
        print("🔑 Extracting important keywords from document...")
        full_text = " ".join([doc.page_content for doc in document])
        full_text = re.sub(r"\b\w+ et al\.,? \d{4}\b|\([A-Za-z]+, \d{4}\)", "", full_text)

        prompt = f"""
        Extract 15-20 most important technical keywords or concepts from this text.
        Focus on subject-specific terminology that represents the core concepts.
        Return ONLY a comma-separated list of these keywords, with no additional text.

        TEXT:
        {full_text[:4000]}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3}
            )
            keyword_text = response.text.strip()
            keywords = [k.strip() for k in keyword_text.split(',') if k.strip()]
            self.important_keywords = set(keywords)
            print(f"✅ Extracted {len(self.important_keywords)} keywords: {', '.join(list(self.important_keywords)[:5])}...")
            return self.important_keywords
        except Exception as e:
            print(f"⚠️ Keyword extraction failed: {str(e)[:50]}...")
            return set()

    def load_and_split_pdf(self, pdf_path: str) -> List[str]:
        """Load and process a PDF document"""
        print(f"📖 Loading PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        self.extract_keywords(documents)

        all_chunks = []
        for doc in documents:
            if should_exclude_chunk(doc.page_content):
                continue
            page_chunks = self.text_splitter.split_text(doc.page_content)
            filtered_chunks = [chunk for chunk in page_chunks if not should_exclude_chunk(chunk)]
            all_chunks.extend(filtered_chunks)

        print(f"✅ PDF split into {len(all_chunks)} chunks (after filtering)")
        if len(all_chunks) < 100:
            print("⚠️ Creating additional chunks with different parameters...")
            chunking_strategies = [
                {"chunk_size": 300, "chunk_overlap": 20},
                {"chunk_size": 200, "chunk_overlap": 10},
                {"chunk_size": 500, "chunk_overlap": 100}
            ]
            additional_chunks = []
            for strategy in chunking_strategies:
                splitter = RecursiveCharacterTextSplitter(**strategy)
                for doc in documents:
                    if should_exclude_chunk(doc.page_content):
                        continue
                    strategy_chunks = splitter.split_text(doc.page_content)
                    filtered_chunks = [chunk for chunk in strategy_chunks if not should_exclude_chunk(chunk)]
                    additional_chunks.extend(filtered_chunks)
            existing_chunks = set(all_chunks)
            for chunk in additional_chunks:
                if chunk not in existing_chunks:
                    all_chunks.append(chunk)
                    existing_chunks.add(chunk)
            print(f"✅ Enhanced PDF split into {len(all_chunks)} chunks (after filtering)")
        return all_chunks

    def generate_multiple_mcqs(self, chunk: str, difficulty_level: str = "Hard") -> List[MCQItem]:
        """Generate multiple MCQs from PDF chunk using Gemini"""
        keyword_text = ", ".join(list(self.important_keywords)[:10]) if self.important_keywords else ""
        prompt = f"""
        Create exactly {self.mcqs_per_chunk} {difficulty_level.lower()} MCQs from this text:
        {chunk}

        IMPORTANT INSTRUCTIONS:
        1. DO NOT create questions about authors, citations, publication dates, or references
        2. DO NOT ask about who wrote or published the content
        3. DO NOT create questions that refer to specific citations like [1], [2], etc.
        4. Focus on technical content, concepts, methods, and applications
        5. If possible, focus on these key topics: {keyword_text}

        For each MCQ, follow this JSON format EXACTLY:
        [
            {{
                "question": "Clear, concise question based on the technical content",
                "options": {{
                    "A": "First option",
                    "B": "Second option",
                    "C": "Third option",
                    "D": "Fourth option"
                }},
                "correct_answer": "A, B, C, or D",
                "explanation": "Brief explanation of why the answer is correct",
                "source": "PDF",
                "difficulty": "{difficulty_level}"
            }}
        ]
        Return a JSON array containing {self.mcqs_per_chunk} MCQ objects.
        """
        backoff_time = 2
        for attempt in range(self.retry_count):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": self.temperature}
                )
                content = response.text.strip()
                if not content:
                    continue
                try:
                    content = clean_json_response(content)
                    mcq_list = json.loads(content)
                    if not isinstance(mcq_list, list):
                        mcq_list = [mcq_list]

                    valid_mcqs = []
                    for mcq_data in mcq_list:
                        try:
                            question = mcq_data.get("question", "").lower()
                            author_patterns = [
                                "author", "wrote", "published", "cited", "reference",
                                "et al", "citation", "paper", "article", "researcher",
                                "study by", "according to", "et al."
                            ]
                            if any(pattern in question for pattern in author_patterns):
                                continue
                            if "source" not in mcq_data:
                                mcq_data["source"] = "PDF"
                            if "difficulty" not in mcq_data:
                                mcq_data["difficulty"] = difficulty_level
                            valid_mcqs.append(MCQItem(**mcq_data))
                        except Exception as e:
                            print(f"⚠️ Invalid MCQ format: {str(e)[:50]}...")
                            continue
                    if valid_mcqs:
                        self.successful_chunks += 1
                        return valid_mcqs
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error: {str(e)[:50]}... (Attempt {attempt+1}/{self.retry_count})")
            except Exception as e:
                print(f"❌ API Error: {str(e)[:50]}... (Attempt {attempt+1}/{self.retry_count})")
            backoff_time = min(60, backoff_time * 1.5)
            time.sleep(backoff_time + random.uniform(0, 2))
        self.failed_chunks += 1
        return []

    def generate_pdf_mcqs(self, chunks: List[str], target_count: int) -> List[MCQItem]:
        """Generate MCQs from PDF chunks"""
        pdf_mcqs = []
        random.shuffle(chunks)

        with tqdm(total=target_count, desc="🔄 Generating PDF MCQs") as pbar:
            chunk_idx = 0
            while len(pdf_mcqs) < target_count and chunk_idx < len(chunks):
                chunk = chunks[chunk_idx]
                new_mcqs = self.generate_multiple_mcqs(chunk)
                for mcq in new_mcqs:
                    if len(pdf_mcqs) < target_count:
                        pdf_mcqs.append(mcq)
                        pbar.update(1)
                    else:
                        break
                if chunk_idx > 0 and chunk_idx % 10 == 0:
                    success_rate = self.successful_chunks / max(1, (self.successful_chunks + self.failed_chunks))
                    if success_rate < 0.5:
                        self.mcqs_per_chunk = max(1, self.mcqs_per_chunk - 1)
                        print(f"⚠️ Adjusting to {self.mcqs_per_chunk} MCQs per chunk due to low success rate ({success_rate:.2f})")
                    elif success_rate > 0.8 and self.mcqs_per_chunk < 3:
                        self.mcqs_per_chunk += 1
                        print(f"✓ Increasing to {self.mcqs_per_chunk} MCQs per chunk due to high success rate ({success_rate:.2f})")
                chunk_idx += 1
                time.sleep(1)
        return pdf_mcqs

    def generate_questions(self, pdf_path: str, num_mcqs: int) -> Tuple[List[dict], List[str]]:
        """Generate MCQs and extract keywords from the provided PDF"""
        print(f"📋 Generating {num_mcqs} MCQs from PDF")
        chunks = self.load_and_split_pdf(pdf_path)
        pdf_mcqs = self.generate_pdf_mcqs(chunks, num_mcqs)
        keywords_list = list(self.important_keywords)
        print(f"✅ Generated {len(pdf_mcqs)} PDF MCQs and extracted {len(keywords_list)} keywords")
        return [mcq.model_dump() for mcq in pdf_mcqs], keywords_list
