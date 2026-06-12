from __future__ import annotations

import asyncio
import html
import os
import tempfile
import uuid
from pathlib import Path

import streamlit as st

from cv_review_agent.agent import review_resume_text
from cv_review_agent.export import export_scores_csv, export_scores_json
from cv_review_agent.parsers import parse_resume_file
from cv_review_agent.schemas import JobTemplate
from cv_review_agent.scoring import rank_scores
from cv_review_agent.storage import (
    load_candidates,
    load_job_templates,
    load_scores,
    save_candidate,
    save_job_templates,
    save_resume_file,
    save_score,
    load_resume_file,
)


st.set_page_config(page_title="AI CV Review Agent", layout="wide")


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --surface: #ffffff;
            --surface-muted: #f6f8fb;
            --line: #d9e0ea;
            --text-muted: #5f6b7a;
            --accent: #176b87;
            --accent-strong: #0f4f66;
            --success: #1f8a5b;
            --warning: #b26a00;
            --danger: #b42318;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }
        .hero {
            background: linear-gradient(135deg, #f7fbfc 0%, #eef5f8 48%, #f8fafc 100%);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 26px 28px;
            margin-bottom: 22px;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.15rem;
            line-height: 1.15;
            letter-spacing: 0;
            color: #16212f;
        }
        .hero p {
            margin: 10px 0 0;
            color: var(--text-muted);
            font-size: 1rem;
            max-width: 780px;
        }
        .metric-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 0 0 22px;
        }
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
        }
        .metric-card span {
            display: block;
            color: var(--text-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .metric-card strong {
            display: block;
            margin-top: 5px;
            font-size: 1.45rem;
            color: #172033;
        }
        .section-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--accent-strong);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        }
        .panel-note {
            color: var(--text-muted);
            font-size: 0.92rem;
            margin: -4px 0 14px;
        }
        .result-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            background: var(--surface);
        }
        .result-card h4 {
            margin: 0 0 8px;
            color: #172033;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 3px 9px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 6px;
            border: 1px solid transparent;
        }
        .badge-strong {
            color: var(--success);
            background: #eaf7f0;
            border-color: #cbead8;
        }
        .badge-review {
            color: var(--warning);
            background: #fff6e5;
            border-color: #f4d49a;
        }
        .badge-weak {
            color: #6b7280;
            background: #f3f4f6;
            border-color: #e5e7eb;
        }
        .badge-disqualified {
            color: var(--danger);
            background: #fff0ee;
            border-color: #f5c4bf;
        }
        .score {
            font-size: 1.75rem;
            line-height: 1;
            font-weight: 800;
            color: var(--accent-strong);
        }
        .small-muted {
            color: var(--text-muted);
            font-size: 0.88rem;
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 6px;
            font-weight: 700;
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--surface);
        }
        @media (max-width: 800px) {
            .metric-row {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .hero {
                padding: 20px;
            }
            .hero h1 {
                font-size: 1.65rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="section-label">Recruiting review workspace</div>
            <h1>AI CV Review Agent</h1>
            <p>Upload resumes, maintain up to three role templates, and review ranked candidate matches with evidence and risk flags. Results are screening support only and require human confirmation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    apply_styles()
    render_header()
    if not require_login():
        return
    render_metrics()
    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        st.markdown('<div class="section-label">Setup</div>', unsafe_allow_html=True)
        st.subheader("Role templates")
        st.markdown(
            '<p class="panel-note">Create 1 to 3 roles. Use one requirement per line so the reviewer can cite evidence cleanly.</p>',
            unsafe_allow_html=True,
        )
        templates = render_templates()
        uploaded_files = render_uploads()
        if st.button("Start review", type="primary", use_container_width=True):
            run_review(uploaded_files, templates)
    with right:
        st.markdown('<div class="section-label">Output</div>', unsafe_allow_html=True)
        render_results()


def require_login() -> bool:
    configured_password = os.getenv("APP_PASSWORD", "")
    already_authenticated = bool(st.session_state.get("authenticated", False))
    if not configured_password:
        st.warning("Access password is not enabled. Set APP_PASSWORD before deploying online.")
        return True

    if already_authenticated:
        return True

    st.subheader("Private access")
    st.markdown(
        '<p class="panel-note">Enter the admin password to view candidates, upload resumes, and download reviewed files.</p>',
        unsafe_allow_html=True,
    )
    entered_password = st.text_input("Password", type="password")
    if st.button("Unlock", type="primary"):
        if is_authenticated(entered_password, configured_password, already_authenticated):
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Incorrect password.")
    return False


def is_authenticated(entered_password: str, configured_password: str, session_authenticated: bool) -> bool:
    if session_authenticated:
        return True
    if not configured_password:
        return True
    return entered_password == configured_password


def render_metrics() -> None:
    templates = load_job_templates()
    candidates = load_candidates()
    scores = load_scores()
    reviewed_jobs = len({score.job_id for score in scores})
    disqualified = len([score for score in scores if score.disqualified])
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-card"><span>Role templates</span><strong>{len(templates)}/3</strong></div>
            <div class="metric-card"><span>Candidates</span><strong>{len(candidates)}</strong></div>
            <div class="metric-card"><span>Reviewed roles</span><strong>{reviewed_jobs}</strong></div>
            <div class="metric-card"><span>Disqualified flags</span><strong>{disqualified}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_uploads():
    st.subheader("Resume intake")
    st.markdown(
        '<p class="panel-note">Upload text-based PDF or DOCX files. Scanned PDFs need OCR and are not supported in v1.</p>',
        unsafe_allow_html=True,
    )
    return st.file_uploader(
        "Candidate resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )


def render_templates() -> list[JobTemplate]:
    existing = load_job_templates()
    count = st.number_input(
        "Number of roles",
        min_value=1,
        max_value=3,
        value=max(1, len(existing)),
        help="The first version supports up to three active role templates.",
    )
    templates = []
    for index in range(int(count)):
        saved = existing[index] if index < len(existing) else None
        with st.expander(f"Role {index + 1}", expanded=True):
            title = st.text_input("Title", value=saved.title if saved else "", key=f"title-{index}")
            required = st.text_area(
                "Required conditions, one per line",
                value="\n".join(saved.required_conditions) if saved else "",
                key=f"required-{index}",
            )
            bonus = st.text_area(
                "Bonus conditions, one per line",
                value="\n".join(saved.bonus_conditions) if saved else "",
                key=f"bonus-{index}",
            )
            responsibilities = st.text_area(
                "Responsibilities, one per line",
                value="\n".join(saved.responsibilities) if saved else "",
                key=f"responsibilities-{index}",
            )
            minimum_years = st.number_input(
                "Minimum years",
                min_value=0,
                max_value=50,
                value=saved.minimum_years if saved else 0,
                key=f"years-{index}",
            )
            disqualifiers = st.text_area(
                "Disqualifiers, one per line",
                value="\n".join(saved.disqualifiers) if saved else "",
                key=f"disqualifiers-{index}",
            )
            notes = st.text_area("Notes", value=saved.notes if saved else "", key=f"notes-{index}")
            if title.strip():
                templates.append(
                    JobTemplate(
                        id=saved.id if saved else f"job-{index + 1}",
                        title=title,
                        required_conditions=_lines(required),
                        bonus_conditions=_lines(bonus),
                        responsibilities=_lines(responsibilities),
                        minimum_years=int(minimum_years),
                        disqualifiers=_lines(disqualifiers),
                        notes=notes,
                    )
                )
    if st.button("Save templates", use_container_width=True):
        if not templates:
            st.error("At least one job template is required.")
        else:
            save_job_templates(templates)
            st.success("Templates saved.")
    return templates


def run_review(uploaded_files, templates: list[JobTemplate]) -> None:
    if not templates:
        st.error("Create at least one job template before reviewing resumes.")
        return
    if not uploaded_files:
        st.error("Upload at least one resume.")
        return

    for uploaded in uploaded_files:
        uploaded_content = uploaded.getvalue()
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as handle:
            handle.write(uploaded_content)
            temp_path = Path(handle.name)
        parsed = parse_resume_file(temp_path)
        temp_path.unlink(missing_ok=True)
        if not parsed.ok:
            st.error(f"{uploaded.name}: {parsed.error}")
            continue
        try:
            review = asyncio.run(review_resume_text(parsed.text, uploaded.name, templates))
        except Exception as exc:
            st.error(f"{uploaded.name}: {exc}")
            continue
        if not review.candidate.id:
            review.candidate.id = str(uuid.uuid4())
        save_candidate(review.candidate)
        save_resume_file(
            candidate_id=review.candidate.id,
            filename=uploaded.name,
            content_type=uploaded.type or _content_type_for(uploaded.name),
            content=uploaded_content,
        )
        for score in review.scores:
            save_score(score)
        st.success(f"Reviewed {uploaded.name}")


def render_results() -> None:
    st.subheader("Rankings by role")
    candidates = {candidate.id: candidate for candidate in load_candidates()}
    jobs = {job.id: job for job in load_job_templates()}
    scores = load_scores()
    if not candidates or not jobs or not scores:
        st.info("No review results yet. Save templates, upload resumes, then start review.")
        return

    for job in jobs.values():
        st.markdown(f"### {job.title}")
        job_scores = rank_scores(score for score in scores if score.job_id == job.id)
        for score in job_scores:
            candidate = candidates.get(score.candidate_id)
            if not candidate:
                continue
            render_score_card(candidate.name, candidate.source_filename, score)

    ranked_scores = []
    for job in jobs.values():
        ranked_scores.extend(rank_scores(score for score in scores if score.job_id == job.id))
    st.divider()
    export_left, export_right = st.columns(2)
    with export_left:
        st.download_button(
            "Download CSV",
            export_scores_csv(ranked_scores, candidates, jobs),
            file_name="cv_review_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with export_right:
        st.download_button(
            "Download JSON",
            export_scores_json(ranked_scores, candidates, jobs),
            file_name="cv_review_results.json",
            mime="application/json",
            use_container_width=True,
        )


def render_score_card(candidate_name: str, source_filename: str, score) -> None:
    safe_candidate_name = html.escape(candidate_name)
    safe_source_filename = html.escape(source_filename)
    safe_recommendation = html.escape(score.recommendation)
    badge_class = f"badge-{score.recommendation}"
    if score.disqualified:
        badge_class = "badge-disqualified"
    review_flag = "Human review needed" if score.needs_human_review else "Ready for review"
    st.markdown(
        f"""
        <div class="result-card">
            <div style="display:flex;justify-content:space-between;gap:16px;align-items:flex-start;">
                <div>
                    <h4>{safe_candidate_name}</h4>
                    <span class="badge {badge_class}">{safe_recommendation}</span>
                    <span class="small-muted">{review_flag}</span>
                    <div class="small-muted" style="margin-top:6px;">{safe_source_filename}</div>
                </div>
                <div style="text-align:right;">
                    <div class="score">{score.total_score}</div>
                    <div class="small-muted">total score</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Evidence and review notes"):
        stored_resume = load_resume_file(score.candidate_id)
        if stored_resume:
            st.download_button(
                "Download original resume",
                data=stored_resume.content,
                file_name=stored_resume.filename,
                mime=stored_resume.content_type,
                key=f"download-resume-{score.candidate_id}-{score.job_id}",
                use_container_width=True,
            )
        detail_cols = st.columns(3)
        detail_cols[0].write("**Strengths**")
        detail_cols[0].write(score.strengths or ["None"])
        detail_cols[1].write("**Gaps**")
        detail_cols[1].write(score.gaps or ["None"])
        detail_cols[2].write("**Risks**")
        detail_cols[2].write(score.risks or ["None"])
        st.write("**Evidence**")
        st.write(score.evidence or ["No evidence provided"])


def _lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _content_type_for(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"


if __name__ == "__main__":
    main()
