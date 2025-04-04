# Create your views here.
# views.py
import os
from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
from .serializers import PDFAnalysisResultSerializer

load_dotenv()

genai.configure(api_key="AIzaSyDUyZrgqqH086Q82o3n0lHacKCDdrrBi8M")
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

@api_view(['POST'])
@parser_classes([MultiPartParser])
def analyze_pdf(request):
    try:
        if 'pdfFile' not in request.FILES:
            return JsonResponse({'message': 'No file part'}, status=400)

        pdf_file = request.FILES['pdfFile']
        if pdf_file.name == '':
            return JsonResponse({'message': 'No selected file'}, status=400)

        if pdf_file and allowed_file(pdf_file.name):
            pdf_text = extract_text_from_pdf(pdf_file)
            prompt = f"""
            Analyze the following PDF text for financial risks, loopholes, and clauses that are not in favor of the customer.
            Identify specific issues and provide a concise description for each.
            
            Text from PDF:
            {pdf_text}

            Specifically, look for:
            - Hidden fees or charges
            - Unclear or ambiguous clauses
            - Conditions that heavily favor the service provider over the customer
            - Loopholes that the company might exploit
            - Terms that could lead to unexpected financial burdens for the customer.

            Format your response as a list of issues, each with a description.
            If no significant risks are found, explicitly state "No significant risks found".
            """
            gemini_response = model.generate_content(prompt)
            response_text = gemini_response.text
            print("Raw Gemini Response Text:\n", response_text)
            analysis_results = parse_gemini_response(response_text)
            return JsonResponse({'results': response_text})
        else:
            return JsonResponse({'message': 'Invalid file type'}, status=400)
    except Exception as e:
        print(f"Error processing PDF or Gemini API: {e}")
        return JsonResponse({'message': 'Error analyzing PDF', 'error': str(e)}, status=500)


def allowed_file(filename):
    return filename.lower().endswith('.pdf')


def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return "Error extracting text from PDF."
    return text


def parse_gemini_response(response_text):
    analysis_results = []
    if response_text and "No significant risks found" in response_text:
        return []

    if response_text:
        issues_lines = response_text.strip().split('\n')
        current_issue = None
        current_description = ""

        for line in issues_lines:
            line = line.strip()
            if not line:
                continue

            if "issue:" in line.lower():
                if current_issue:
                    analysis_results.append({'issue': current_issue.strip(), 'description': current_description.strip()})
                issue_start_index = line.lower().find("issue:") + len("issue:")
                current_issue = line[issue_start_index:].strip().lstrip('**').rstrip('**').strip()
                current_description = ""
            elif current_issue:
                current_description += line + " "

        if current_issue:
            analysis_results.append({'issue': current_issue.strip(), 'description': current_description.strip()})

        if not analysis_results:
            analysis_results.append({'issue': "Analysis Incomplete", 'description': "Could not parse specific issues from the AI response. Review the raw AI response for details."})
    else:
        analysis_results.append({'issue': "No Analysis Response", 'description': "Gemini API did not return a valid response."})

    return analysis_results
