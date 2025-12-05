import streamlit as st
import PyPDF2
import docx
# from google import genai
import google.generativeai as genai
import json
import re

# ===========================
# CONFIGURATION
# ===========================
# 🔑 Directly use your API key here (for local testing only)
API_KEY = "AIzaSyBgthsd6RZujiJobfhVPd3Ordodysrhz_o"

# Choose model (you can change to gemini-1.5-pro if needed)
MODEL = "gemini-2.0-flash"

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)


# ===========================
# HELPER FUNCTIONS
# ===========================





def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


def extract_text_from_docx(file):
    """Extract text from DOCX file"""
    doc = docx.Document(file)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_resume(uploaded_file):
    """Read and extract text from uploaded resume"""
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        st.error("❌ Unsupported file format. Please upload PDF or DOCX.")
        return ""


def get_ats_analysis(resume_text, jd_text):
    """Use Gemini API to compare resume and job description"""
    prompt = f"""
You are an expert ATS evaluator and career coach.

Evaluate the following resume against the given job description.

Provide output in JSON format with the following fields:
- score: integer between 0 and 100
- strengths: list of top strengths
- missing_skills: list of missing or weak skills
- verdict: Shortlist / Consider / Not a Match
- recommendations: list of 2–3 suggestions
- create a list where mention the only missing skills from the job description

=== JOB DESCRIPTION ===
{jd_text}

=== RESUME ===
{resume_text}
"""

    response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
)

    text = response.text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)

    try:
        result = json.loads(text)
    except Exception:
        result = {
            "score": 0,
            "strengths": [],
            "missing_skills": [],
            "verdict": "Parsing Error",
            "recommendations": [response.text],
        }

    return result


# ===========================
# STREAMLIT UI
# ===========================

st.set_page_config(page_title="ATS Resume Score Checker", page_icon="📄", layout="centered")

st.title("📄 ATS Resume Score Checker")
st.caption("Powered by Google Gemini API — built by Akshat Anand 💡")

st.markdown("""
Upload your resume and paste a job description below.  
The app will calculate an **ATS match score (0–100)** and provide improvement suggestions.
""")

uploaded_resume = st.file_uploader("📎 Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("🧾 Paste Job Description", height=200)

if uploaded_resume and job_description:
    if st.button("🔍 Analyze Resume"):
        with st.spinner("Analyzing your resume with Gemini AI... ⏳"):
            resume_text = read_resume(uploaded_resume)
            if not resume_text:
                st.error("❌ Unable to extract text from resume.")
            else:
                result = get_ats_analysis(resume_text, job_description)

                st.subheader("📊 ATS Match Score")
                st.progress(result.get("score", 0) / 100)
                st.metric("Match Score", f"{result.get('score', 0)} / 100")

                st.subheader("💪 Strengths")
                if result.get("strengths"):
                    for s in result["strengths"]:
                        st.write(f"- {s}")
                else:
                    st.write("No strengths identified.")

                st.subheader("⚠️ Missing or Weak Skills")
                if result.get("missing_skills"):
                    for m in result["missing_skills"]:
                        st.write(f"- {m}")
                else:
                    st.write("No missing skills identified.")

                st.subheader("🧾 Verdict")
                st.write(f"**{result.get('verdict', 'N/A')}**")

                st.subheader("📈 Recommendations")
                for r in result.get("recommendations", []):
                    st.write(f"- {r}")

else:
    st.info("⬆️ Upload a resume and paste a job description to begin.")

st.markdown("---")
st.caption("Made with ❤️ using Streamlit + Gemini API")
