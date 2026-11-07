import os
import re
import streamlit as st

for key in ["GROQ_API_KEY", "GOOGLE_API_KEY"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

from utils.rag import analyze_resume_fit
from utils.chunking import split_resume_into_chunks
from utils.embeddings import get_embedding_model
from utils.vector_store import create_resume_vector_store, search_resume
from utils.question_generator import generate_interview_questions
from utils.answer_evaluator import evaluate_interview_answers
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from xml.sax.saxutils import escape
from utils.report_generator import generate_interview_pdf



from utils.document_processor import (
    extract_resume_text,
    validate_job_description,
)


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="AI Interview Preparation Platform",
    page_icon="🎯",
    layout="wide",
)

# ---------------- HEADER ----------------

st.title("🎯 AI Interview Preparation Platform")
st.caption("Prepare smarter. Interview better.")

st.markdown(
    """
    Welcome to your AI-powered interview preparation platform.

    Upload your resume and provide a Job Description
    to begin your interview preparation journey.
    """
)

st.divider()

# ---------------- RESUME UPLOAD ----------------

st.header("📄 Step 1: Upload Your Resume")

resume_file = st.file_uploader(
    "Upload your Resume (PDF only)",
    type=["pdf"],
    help="Upload a text-based or scanned PDF resume.",
)

if resume_file is not None:
    st.success(f"Uploaded: {resume_file.name}")

    st.caption(
        f"File size: {resume_file.size / 1024:.2f} KB"
    )

# ---------------- JOB DESCRIPTION ----------------

st.header("💼 Step 2: Job Description")

jd_text = st.text_area(
    "Paste the Job Description here",
    height=220,
    placeholder=(
        "Example:\n"
        "We are looking for a Python Developer.\n"
        "Required skills: Python, SQL, Django, REST APIs.\n"
        "Responsibilities: Develop and maintain applications."
    ),
)

# ---------------- ANALYZE BUTTON ----------------

analyze = st.button(
    "🚀 Analyze Documents",
    type="primary",
    use_container_width=True,
)

if analyze:

    # Clear old results before new processing
    st.session_state.pop("resume_text", None)
    st.session_state.pop("jd_text", None)
    st.session_state.pop("resume_filename", None)

    if resume_file is None:
        st.error("Please upload your resume PDF.")

    elif resume_file.size > 10 * 1024 * 1024:
        st.error("Resume file must be below 10 MB.")

    else:
        try:
            # Validate JD
            clean_jd = validate_job_description(jd_text)

            # Process resume
            with st.spinner(
                "Processing resume and Job Description..."
            ):
                resume_text = extract_resume_text(
                    resume_file
                )

            # Store results in session
            st.session_state["resume_text"] = resume_text
            st.session_state["jd_text"] = clean_jd
            st.session_state["resume_filename"] = (
                resume_file.name
            )

            st.success(
                "Documents processed successfully!"
            )
            
            with st.spinner("Creating resume chunks..."):
                resume_chunks = split_resume_into_chunks(resume_text)

            st.session_state["resume_chunks"] = resume_chunks

            st.info(f"Resume chunks created: {len(resume_chunks)}")

            with st.spinner("Generating embeddings and building FAISS..."):
                embedding_model = get_embedding_model()

                vector_store = create_resume_vector_store(
                    resume_chunks,
                    embedding_model
                )

            st.session_state["vector_store"] = vector_store

            st.success("FAISS vector store created successfully!")


        except ValueError as e:
            st.error(str(e))

        except Exception as e:
            # Development debugging only
            st.error(
                f"Processing error: {type(e).__name__}: {e}"
            )
            st.exception(e)

# ---------------- DISPLAY RESULTS ----------------

if (
    "resume_text" in st.session_state
    and "jd_text" in st.session_state
):
    resume_text = st.session_state["resume_text"]
    clean_jd = st.session_state["jd_text"]

    st.divider()

    st.header("✅ Document Processing Results")

    st.caption(
        f"Resume: {st.session_state.get('resume_filename', 'Uploaded PDF')}"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Resume Characters",
            f"{len(resume_text):,}",
        )

    with col2:
        st.metric(
            "JD Characters",
            f"{len(clean_jd):,}",
        )

    # Resume preview
    with st.expander(
        "📄 View Extracted Resume Text",
        expanded=True,
    ):
        st.text_area(
            "Resume Preview",
            value=resume_text[:12000],
            height=350,
            disabled=True,
        )

        if len(resume_text) > 12000:
            st.caption(
                "Preview truncated. Full extracted text "
                "is available in the current session."
            )

    # JD preview
    with st.expander("💼 View Job Description"):
        st.text_area(
            "Job Description Preview",
            value=clean_jd,
            height=250,
            disabled=True,
        )

    st.divider()

    st.success(
        "Step 2 completed! Your documents are ready."
    )

    st.info(
        "Next step: Resume chunking, embeddings, "
        "FAISS vector store and RAG retrieval."
    )

else:
    st.divider()
    st.info(
        "Upload your resume and enter a Job Description "
        "to get started."
    )

    
if "vector_store" in st.session_state:

    st.divider()
    st.header("🔎 Step 3: Resume Semantic Search")

    search_query = st.text_input(
        "Ask something about your resume",
        placeholder="Example: What Python experience does the candidate have?"
    )

    if st.button("Search Resume"):
        if search_query.strip():
            try:
                results = search_resume(
                    st.session_state["vector_store"],
                    search_query,
                    k=4
                )

                st.subheader("Retrieved Resume Chunks")

                for i, doc in enumerate(results, start=1):
                    with st.expander(f"Result {i}"):
                        st.write(doc.page_content)
                        st.caption(
                            f"Chunk ID: {doc.metadata.get('chunk_id')}"
                        )

            except Exception as e:
                st.error(f"Search failed: {type(e).__name__}: {e}")
        else:
            st.warning("Please enter a search query.")
 
# ---------------- STEP 4: INTERVIEW QUESTIONS ----------------

st.divider()
st.header("🎯 Step 4: Interview Question Generator")

if (
    "vector_store" in st.session_state
    and "jd_text" in st.session_state
):
    st.write(
        "Generate personalized interview questions "
        "using your resume and Job Description."
    )

    if st.button(
        "Generate Interview Questions",
        type="primary",
        use_container_width=True
    ):
        try:
            with st.spinner(
                "Groq AI is generating interview questions..."
            ):
                questions = generate_interview_questions(
                    st.session_state["vector_store"],
                    st.session_state["jd_text"]
                )

            st.session_state["interview_questions"] = questions
            st.success("Interview questions generated!")

        except Exception as e:
            st.error(
                f"Question generation failed: "
                f"{type(e).__name__}: {e}"
            )

    if "interview_questions" in st.session_state:
        st.subheader("📝 Your Interview Practice Questions")

        st.markdown(
            st.session_state["interview_questions"]
        )

else:
    st.info(
        "Please upload your resume and process your "
        "Job Description first."
    )

    
# ---------------- STEP 5: MOCK INTERVIEW ----------------

st.divider()
st.header("🎤 Step 5: Mock Interview")

if "interview_questions" in st.session_state:

    # Convert generated questions into a list
    raw_questions = st.session_state["interview_questions"]

    parsed_questions = re.findall(
        r"(?m)^\s*\d+\.\s+(.+?)\s*$",
        raw_questions
    )

    if len(parsed_questions) != 12:
        st.warning(
            f"Expected 12 questions, found "
            f"{len(parsed_questions)}. "
            "Please regenerate questions if needed."
        )

    # Start interview
    if st.button("🚀 Start Mock Interview"):
        if not parsed_questions:
            st.error("No questions found.")
        else:
            st.session_state["mock_questions"] = parsed_questions
            st.session_state["mock_answers"] = []
            st.session_state["mock_index"] = 0
            st.session_state["mock_completed"] = False
            st.rerun()

    # Interview in progress
    if (
        "mock_questions" in st.session_state
        and not st.session_state.get("mock_completed", False)
    ):
        questions = st.session_state["mock_questions"]
        idx = st.session_state["mock_index"]

        if idx < len(questions):

            st.progress((idx + 1) / len(questions))

            st.caption(
                f"Question {idx + 1} of {len(questions)}"
            )

            st.subheader(f"Question {idx + 1}")
            st.write(questions[idx])

            with st.form(key=f"mock_form_{idx}"):

                answer = st.text_area(
                    "Your Answer",
                    height=200,
                    placeholder=(
                        "Type your answer here..."
                    ),
                    key=f"mock_answer_{idx}"
                )

                submitted = st.form_submit_button(
                    "Submit Answer",
                    type="primary",
                    use_container_width=True
                )

            if submitted:
                if not answer.strip():
                    st.warning("Please enter your answer.")
                else:
                    st.session_state["mock_answers"].append({
                        "question": questions[idx],
                        "answer": answer.strip()
                    })

                    if idx + 1 < len(questions):
                        st.session_state["mock_index"] = idx + 1
                    else:
                        st.session_state["mock_completed"] = True

                    st.rerun()

    # Interview completed
    if st.session_state.get("mock_completed", False):

        st.success("🎉 Mock Interview Completed!")

        st.write(
            f"Questions answered: "
            f"{len(st.session_state['mock_answers'])}"
        )

        st.subheader("Your Submitted Answers")

        for i, item in enumerate(
            st.session_state["mock_answers"],
            start=1
        ):
            with st.expander(f"Question {i}"):
                st.write(item["question"])
                st.markdown("**Your Answer:**")
                st.write(item["answer"])

            
   
    import re

    st.divider()
    st.subheader("🤖 AI Answer Evaluation")

    st.write(
        "Evaluate your mock interview answers "
        "and get personalized feedback."
    )

    if st.button(
        "Generate Final Evaluation",
        key="generate_final_evaluation"
    ):
        try:
            with st.spinner("AI is evaluating your answers..."):

                evaluation = evaluate_interview_answers(
                    st.session_state["mock_answers"]
                )

                st.session_state["final_evaluation"] = evaluation

                st.session_state["final_answers"] = (
                    st.session_state["mock_answers"].copy()
                )

        except Exception as e:
            st.error(f"Evaluation failed: {e}")

    # -----------------------------------------
    # DISPLAY COMPLETE EVALUATION ONLY ONCE
    # -----------------------------------------

    if st.session_state.get("final_evaluation"):

        report = st.session_state["final_evaluation"]
        answers = st.session_state.get("final_answers", [])

        st.success("Evaluation completed successfully!")

        st.markdown("## 📋 AI Interview Evaluation")

        # Complete individual evaluation appears only here
        st.markdown(report)

        # -----------------------------------------
        # PDF DOWNLOAD
        # -----------------------------------------

        st.divider()
        st.subheader("📄 Download Your Final Report")

        try:
            pdf_bytes = generate_interview_pdf(report, answers)

            st.download_button(
                label="⬇️ Download Interview Report (PDF)",
                data=pdf_bytes,
                file_name="AI_Interview_Performance_Report.pdf",
                mime="application/pdf",
                key="download_interview_report",
            )

        except Exception as e:
            st.error(f"PDF generation failed: {e}")

        
        # -----------------------------------------
        # INTERVIEW PERFORMANCE DASHBOARD
        # -----------------------------------------

        # Extract total score
        total_match = re.search(
            r"Total Score:\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)",
            report,
            re.IGNORECASE
        )

        # Extract average score
        average_match = re.search(
            r"Average Score:\s*(\d+(?:\.\d+)?)\s*/\s*5",
            report,
            re.IGNORECASE
        )

        # Dashboard heading
        st.divider()
        st.title("📊 Interview Performance Dashboard")

        st.caption(
            "Your AI-generated mock interview performance overview."
        )

        # Dashboard metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Questions Answered",
                len(answers)
            )

        with col2:
            if total_match:
                earned = float(total_match.group(1))
                maximum = float(total_match.group(2))

                st.metric(
                    "Total Score",
                    f"{earned:g}/{maximum:g}"
                )
            else:
                st.metric("Total Score", "See Evaluation")

        with col3:
            if average_match:
                average = float(average_match.group(1))

                st.metric(
                    "Average Score",
                    f"{average:.2f}/5"
                )
            else:
                st.metric("Average Score", "See Evaluation")

        # Overall performance percentage
        if total_match:
            earned = float(total_match.group(1))
            maximum = float(total_match.group(2))

            if maximum > 0:
                percentage = (earned / maximum) * 100

                st.subheader("Overall Performance")

                st.progress(
                    max(0.0, min(1.0, percentage / 100))
                )

                st.write(
                    f"**Score Percentage:** {percentage:.2f}%"
                )

                # Performance level
                if percentage >= 90:
                    performance = "Excellent"
                elif percentage >= 80:
                    performance = "Very Good"
                elif percentage >= 70:
                    performance = "Good"
                elif percentage >= 60:
                    performance = "Average"
                else:
                    performance = "Needs Improvement"

                st.write(
                    f"**Performance Level:** {performance}"
                )

        st.divider()

        # Individual submitted answers
        st.subheader("📚 Your Interview Responses")

        for i, item in enumerate(answers, start=1):

            with st.expander(f"Question {i}"):

                st.write("**Question:**")
                st.write(item.get("question", ""))

                st.write("**Your Answer:**")
                st.write(item.get("answer", ""))

        st.info(
            "AI scores are approximate practice estimates, "
            "not official interview results."
        )


        
# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "AI Interview Preparation Platform | "
    "Interview practice and skill development"
)
