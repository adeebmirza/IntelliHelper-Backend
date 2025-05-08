from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi import APIRouter
import fitz
import tempfile
import google.generativeai as genai
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import docx



resume_router = APIRouter(tags=["profile"])


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def prompt_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text
def extract_text_from_pdf(file_bytes):
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)

def extract_text_from_docx(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp.close()
        doc = docx.Document(tmp.name)
        return "\n".join([p.text for p in doc.paragraphs])

def extract_resume_text(file: UploadFile):
    content = file.file.read()
    if file.filename.endswith(".pdf"):
        return extract_text_from_pdf(content)
    elif file.filename.endswith(".docx"):
        return extract_text_from_docx(content)
    elif file.filename.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file format")

async def process_resume(resume_file: UploadFile, job_description: str, company_name: str = None):
    resume_text = extract_resume_text(resume_file)

    # 1. Score Resume
    score_prompt = f"""
    Score this resume against the job description (0-100), give the reason in short:
    
    Resume:
    {resume_text}

    Job Description:
    {job_description}
    """
    score = prompt_gemini(score_prompt)

    # 2. Tailor Resume
    if company_name:
        tailor_prompt = f"""
        Rewrite the resume below to tailor it specifically for the job description and the company {company_name}.
    
        Resume:
        {resume_text}

        Job Description:
        {job_description}

        Company: {company_name}
        """
    else:
        tailor_prompt = f"""
        Rewrite the resume below to tailor it specifically for the job description.

        Resume:
        {resume_text}

        Job Description:
        {job_description}
        """
        
    tailored_resume = prompt_gemini(tailor_prompt)

    # 3. Career Path Suggestion (based on the company if available)
    if company_name:
        career_path_prompt = f"""
        Based on the job description and the company {company_name}, suggest a potential career path for this role.

        Job Description:
        {job_description}

        Company: {company_name}
        """
    else:
        career_path_prompt = f"""
        Based on the job description, suggest a potential career path for this role.

        Job Description:
        {job_description}
        """
        
    career_path = prompt_gemini(career_path_prompt)

    # 4. Interview Preparation (based on company and role)
    if company_name:
        interview_prep_prompt = f"""
        Based on the job description and the company {company_name}, provide interview preparation tips including potential interview questions, key skills to focus on, and company-specific interview insights.
        
        Job Description:
        {job_description}

        Company: {company_name}
        """
    else:
        interview_prep_prompt = f"""
        Based on the job description, provide interview preparation tips including potential interview questions and key skills to focus on.

        Job Description:
        {job_description}
        """
        
    interview_preparation = prompt_gemini(interview_prep_prompt)

    return {
        "score": score,
        "tailored_resume": tailored_resume,
        "career_path": career_path,
        "interview_preparation": interview_preparation
    }


@resume_router.post("/analyze/")
async def analyze_resume(
    resume: UploadFile,
    job_description: str = Form(...),
    company_name: Optional[str] = Form(None)  # Optional company name field
):
    result = await process_resume(resume, job_description, company_name)
    return result