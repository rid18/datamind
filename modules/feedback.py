"""
feedback.py
-----------
Powers BOTH the "Feedback" tab and the "About" tab for DataMind.
Author/Maintainer: Ridham Bansal
"""

import os
import pandas as pd
from datetime import datetime

FEEDBACK_COLUMNS = [
    "Timestamp",
    "Rating",
    "AI_Helpful",
    "Visualizations_Useful",
    "Would_Recommend",
    "Suggestions",
]

def _get_feedback_file_path() -> str:
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(modules_dir)
    return os.path.join(project_root, "feedback.csv")

def submit_feedback(rating, ai_helpful, viz_useful, would_recommend, suggestions) -> str:
    if rating is None:
        return "  Please select an Overall Rating before submitting."
    if not ai_helpful:
        return "  Please answer 'Was AI Helpful?' before submitting."
    if not viz_useful:
        return "  Please answer 'Were Visualizations Useful?' before submitting."
    if not would_recommend:
        return "  Please answer 'Would you Recommend this App?' before submitting."

    file_path = _get_feedback_file_path()
    new_entry = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Rating": int(rating),
        "AI_Helpful": ai_helpful,
        "Visualizations_Useful": viz_useful,
        "Would_Recommend": would_recommend,
        "Suggestions": suggestions.strip() if suggestions else "",
    }], columns=FEEDBACK_COLUMNS)

    try:
        file_exists = os.path.isfile(file_path)
        new_entry.to_csv(file_path, mode="a", header=not file_exists, index=False)
        return "  Thank you! Your feedback has been recorded."
    except Exception as e:
        return f" Could not save feedback: {str(e)}"

def _load_feedback_dataframe() -> pd.DataFrame:
    file_path = _get_feedback_file_path()
    if not os.path.isfile(file_path):
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception:
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)

def get_feedback_stats():
    df = _load_feedback_dataframe()
    if df.empty:
        stats = {
            "total_users": 0,
            "average_rating": 0,
            "pct_ai_helpful": 0,
            "pct_viz_useful": 0,
            "pct_recommend": 0,
        }
        return stats, pd.DataFrame(columns=FEEDBACK_COLUMNS)

    total_users = len(df)
    average_rating = round(df["Rating"].mean(), 2)
    pct_ai_helpful = round((df["AI_Helpful"] == "Yes").mean() * 100, 1)
    pct_viz_useful = round((df["Visualizations_Useful"] == "Yes").mean() * 100, 1)
    pct_recommend = round((df["Would_Recommend"] == "Yes").mean() * 100, 1)

    stats = {
        "total_users": total_users,
        "average_rating": average_rating,
        "pct_ai_helpful": pct_ai_helpful,
        "pct_viz_useful": pct_viz_useful,
        "pct_recommend": pct_recommend,
    }

    latest_entries = df.tail(5).iloc[::-1].reset_index(drop=True)
    return stats, latest_entries

def format_about_markdown(stats: dict) -> str:
    if not stats or stats.get("total_users", 0) == 0:
        return (
            "###   About This App\n\n"
            "**DataMind** helps you explore, understand, and visualize "
            "your datasets in minutes   no code required.\n\n"
            "No feedback has been submitted yet. Be the first!"
        )

    md = "###   About This App\n\n"
    md += (
        "**DataMind** helps you explore, understand, and visualize "
        "your datasets in minutes   no code required.\n\n"
    )
    md += "###   Community Feedback Summary\n\n"
    md += "| Metric | Value |\n"
    md += "|---|---|\n"
    md += f"| **Total Users** | {stats['total_users']} |\n"
    md += f"| **Average Rating** | {stats['average_rating']} / 5 |\n"
    md += f"| **AI Found Helpful** | {stats['pct_ai_helpful']}% |\n"
    md += f"| **Satisfied with Visualizations** | {stats['pct_viz_useful']}% |\n"
    md += f"| **Would Recommend the App** | {stats['pct_recommend']}% |\n"
    return md

def format_about_intro_markdown() -> str:
    return (
        "###   About This App\n\n"
        "**DataMind** helps you explore, understand, and visualize "
        "your datasets in minutes   no code required. Developed by Ridham Bansal."
    )

def format_about_kpi_cards(stats: dict) -> str:
    if not stats or stats.get("total_users", 0) == 0:
        return (
            "<div class='kpi-empty'>"
            "No feedback has been submitted yet. Be the first!"
            "</div>"
        )

    kpi_definitions = [
        (" ", "Total Users", stats["total_users"]),
        (" ", "Average Rating", f"{stats['average_rating']} / 5"),
        (" ", "Found AI Helpful", f"{stats['pct_ai_helpful']}%"),
        (" ", "Satisfied with Visualizations", f"{stats['pct_viz_useful']}%"),
        (" ", "Would Recommend", f"{stats['pct_recommend']}%"),
    ]

    cards_html = ""
    for icon, label, value in kpi_definitions:
        cards_html += f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """
    return f'<div class="kpi-grid">{cards_html}</div>'