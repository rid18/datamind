"""
app.py
------
Main entry point for DataMind (formerly "DataNest" / "AI Data Analyst Agent" / "Prism Analytics").

PART 1: Project setup + File upload (CSV / Excel) + Dashboard tab
PART 2: Dataset Metadata tab (column name, dtype, missing, unique values)
PART 3: AI Readiness tab (0-100 quality score + status label)
PART 4: Visualization Studio (interactive chart builder)
PART 5: Feedback tab + About tab (feedback.csv storage + aggregated stats)
PART 6: Feedback tab UI redesign (card layout) + Persistent Upload History
PART 7: Dashboard KPI cards + Bar Chart X/Y fix + AI Dataset Chat tab
PART 8: Data Cleaning tab (missing values, duplicates, outliers) + Export
PART 9: Full visual redesign - premium SaaS look, rebrand, no logic changes

Maintainer / Developer: Ridham Bansal

Run with:
    python app.py
"""

import os
import textwrap
import functools
import gradio as gr

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from modules.data_handler import load_dataset
from modules.dashboard import get_dashboard_stats, format_stats_as_markdown, format_stats_as_kpi_cards, get_preview
from modules.metadata import (
    get_metadata,
    render_metadata_dashboard,
    render_metadata_top_html,
    render_metadata_bottom_html,
    get_business_metric_columns,
    get_default_business_metrics,
    get_bi_kpis,
    format_bi_kpis_html,
    generate_column_visual_summary_html,
)
from modules.visualization import (
    CHART_TYPES,
    get_feature_dropdown_updates,
    get_feature_availability_warning,
    get_numeric_feature_choices,
    generate_visualization,
    PIVOT_AGGREGATIONS,
    get_pivot_dropdown_updates,
    get_pivot_filter_value_choices,
    generate_pivot_table,
)
from modules.feedback import (
    submit_feedback,
    get_feedback_stats,
    format_about_markdown,
    format_about_intro_markdown,
    format_about_kpi_cards,
)
from modules.upload_history import log_upload, get_upload_history
from modules.ai_chat import answer_question, is_openai_available, get_example_questions_markdown
from modules.data_cleaning import (
    MISSING_VALUE_STRATEGIES,
    OUTLIER_STRATEGIES,
    get_missing_summary,
    get_missing_value_stats,
    format_missing_value_stats_html,
    search_missing_summary,
    detect_outliers_iqr,
    clean_dataset,
    export_dataset,
    preview_cleaning_plan,
)

# ----------------------------------------------------------------------
# CALLBACK FUNCTIONS
# ----------------------------------------------------------------------

def handle_file_upload(file):
    file_path = file.name if file is not None else None
    df, message = load_dataset(file_path)
    default_chart_type = "Histogram"
    
    if df is None:
        empty_dashboard_html = format_stats_as_kpi_cards({})
        empty_metadata_top = render_metadata_top_html(None)
        empty_metric_dropdown = gr.update(choices=[], value=None)
        empty_bi_kpis = format_bi_kpis_html({})
        empty_metadata_bottom = render_metadata_bottom_html(None)
        feature1_update, feature2_update = get_feature_dropdown_updates(default_chart_type, None)
        history_df = get_upload_history()
        empty_missing_summary = get_missing_summary(None)
        empty_visual_summary_dropdown = gr.update(choices=[], value=None)
        empty_visual_summary_html = generate_column_visual_summary_html(None, None)
        empty_cleaning_plan = preview_cleaning_plan(None, "Do Nothing", "Do Nothing", None)
        empty_missing_stats_html = format_missing_value_stats_html(get_missing_value_stats(None))
        (
            empty_pivot_rows, empty_pivot_columns, empty_pivot_values,
            empty_pivot_filter_column, empty_pivot_filter_value,
        ) = get_pivot_dropdown_updates(None)
        return (
            message, None, empty_dashboard_html, None,
            empty_metadata_top, empty_metric_dropdown, empty_bi_kpis, empty_metadata_bottom,
            gr.update(value=default_chart_type), feature1_update, feature2_update, None, "",
            history_df, [], [],
            empty_missing_summary, gr.update(choices=[], value=None), None, "",
            None, gr.update(value=None, visible=False),
            "", gr.update(visible=True),
            empty_visual_summary_dropdown, empty_visual_summary_html, empty_cleaning_plan,
            empty_pivot_rows, empty_pivot_columns, empty_pivot_values,
            empty_pivot_filter_column, empty_pivot_filter_value, None, "",
            empty_missing_stats_html, "", gr.update(visible=False),
        )

    stats = get_dashboard_stats(df)
    dashboard_html = format_stats_as_kpi_cards(stats)
    preview_df = get_preview(df, n_rows=10)

    metadata_top_html = render_metadata_top_html(df)
    business_metric_choices = get_business_metric_columns(df)
    default_metrics = get_default_business_metrics(df, top_n=1)
    default_metric = default_metrics[0] if default_metrics else None
    metric_dropdown_update = gr.update(choices=business_metric_choices, value=default_metric)
    bi_kpis_html = format_bi_kpis_html(get_bi_kpis(df, columns=default_metrics if default_metrics else None))
    metadata_bottom_html = render_metadata_bottom_html(df)
    feature1_update, feature2_update = get_feature_dropdown_updates(default_chart_type, df)
    viz_warning = get_feature_availability_warning(default_chart_type, df)

    original_filename = os.path.basename(file_path) if file_path else "unknown_file"
    total_rows, total_columns = df.shape
    log_upload(filename=original_filename, rows=total_rows, columns=total_columns)
    history_df = get_upload_history()

    missing_summary_df = get_missing_summary(df)
    missing_stats_html = format_missing_value_stats_html(get_missing_value_stats(df))
    outlier_column_update = gr.update(choices=get_numeric_feature_choices(df), value=None)
    cleaning_plan_html = preview_cleaning_plan(df, "Do Nothing", "Do Nothing", None)

    all_columns = df.columns.tolist()
    default_visual_column = all_columns[0] if all_columns else None
    visual_summary_dropdown_update = gr.update(choices=all_columns, value=default_visual_column)
    visual_summary_html = generate_column_visual_summary_html(df, default_visual_column)

    (
        pivot_rows_update, pivot_columns_update, pivot_values_update,
        pivot_filter_column_update, pivot_filter_value_update,
    ) = get_pivot_dropdown_updates(df)

    return (
        message, df, dashboard_html, preview_df,
        metadata_top_html, metric_dropdown_update, bi_kpis_html, metadata_bottom_html,
        gr.update(value=default_chart_type), feature1_update, feature2_update, None, "",
        history_df, [], [],
        missing_summary_df, outlier_column_update, None, "",
        None, gr.update(value=None, visible=False),
        viz_warning, gr.update(visible=True),
        visual_summary_dropdown_update, visual_summary_html, cleaning_plan_html,
        pivot_rows_update, pivot_columns_update, pivot_values_update,
        pivot_filter_column_update, pivot_filter_value_update, None, "",
        missing_stats_html, "", gr.update(visible=False),
    )

def handle_feedback_submit(rating, ai_helpful, viz_useful, would_recommend, suggestions):
    status_message = submit_feedback(rating, ai_helpful, viz_useful, would_recommend, suggestions)
    stats, latest_entries = get_feedback_stats()
    about_html = format_about_kpi_cards(stats)
    return (
        status_message, about_html, latest_entries,
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=""),
    )

def handle_about_refresh():
    stats, latest_entries = get_feedback_stats()
    about_html = format_about_kpi_cards(stats)
    return about_html, latest_entries

def handle_chat_message(question, chat_history, df):
    answer = answer_question(question, df)
    chat_history = chat_history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    return chat_history, chat_history, "", gr.update(visible=False)

def handle_chat_clear():
    return [], [], "", gr.update(visible=True)

def handle_metric_change(selected_metric, df):
    return format_bi_kpis_html(get_bi_kpis(df, columns=selected_metric))

def handle_visual_summary_change(selected_column, df):
    return generate_column_visual_summary_html(df, selected_column)

def handle_chart_type_change(chart_type, df):
    feature1_update, feature2_update = get_feature_dropdown_updates(chart_type, df)
    warning_message = get_feature_availability_warning(chart_type, df)
    return feature1_update, feature2_update, warning_message

def handle_pivot_filter_column_change(df, filter_column):
    choices = get_pivot_filter_value_choices(df, filter_column)
    return gr.update(choices=choices, value=[])

def handle_generate_pivot(df, rows, columns, values, aggregation, filter_column, filter_values):
    pivot_df, status_message = generate_pivot_table(
        df, rows, columns, values, aggregation, filter_column, filter_values
    )
    return pivot_df, status_message

def handle_detect_outliers(df, column):
    _, _, _, message = detect_outliers_iqr(df, column)
    return message

def handle_cleaning_plan_preview(df, missing_strategy, outlier_strategy, outlier_column):
    return preview_cleaning_plan(df, missing_strategy, outlier_strategy, outlier_column)

def handle_missing_search(df, search_term):
    return search_missing_summary(df, search_term)

def handle_apply_cleaning(df, missing_strategy, outlier_strategy, outlier_column):
    cleaned_df, summary_md, missing_df = clean_dataset(
        df, missing_strategy, outlier_strategy, outlier_column
    )
    hide_banner = gr.update(visible=False)
    hide_file = gr.update(value=None, visible=False)
    if cleaned_df is None:
        empty_stats_html = format_missing_value_stats_html(get_missing_value_stats(None))
        return None, summary_md, None, get_missing_summary(None), empty_stats_html, hide_banner, hide_file
    preview_df = cleaned_df.head(10)
    stats_html = format_missing_value_stats_html(get_missing_value_stats(cleaned_df))
    return cleaned_df, summary_md, preview_df, missing_df, stats_html, hide_banner, hide_file

def handle_export_csv(cleaned_df):
    if cleaned_df is None:
        gr.Warning("Please click 'Apply Cleaning' first - there's no cleaned dataset to export yet.")
        return gr.update(visible=False), gr.update(value=None, visible=False)
    file_path = export_dataset(cleaned_df, "CSV (.csv)")
    banner_html = (
        "<div class='export-success-banner-inner'>"
        "<span class='export-success-icon'> </span>"
        "<span>Your cleaned dataset is ready   CSV format.</span>"
        "</div>"
    )
    return gr.update(value=banner_html, visible=True), gr.update(value=file_path, visible=True)

def handle_export_excel(cleaned_df):
    if cleaned_df is None:
        gr.Warning("Please click 'Apply Cleaning' first - there's no cleaned dataset to export yet.")
        return gr.update(visible=False), gr.update(value=None, visible=False)
    file_path = export_dataset(cleaned_df, "Excel (.xlsx)")
    banner_html = (
        "<div class='export-success-banner-inner'>"
        "<span class='export-success-icon'> </span>"
        "<span>Your cleaned dataset is ready   Excel format.</span>"
        "</div>"
    )
    return gr.update(value=banner_html, visible=True), gr.update(value=file_path, visible=True)

# ----------------------------------------------------------------------
# CUSTOM CSS
# ----------------------------------------------------------------------
CUSTOM_CSS = """
:root {
    --pa-indigo: #6366f1;
    --pa-purple: #8b5cf6;
    --pa-cyan: #22d3ee;
    --pa-blue-accent: #3b82f6;
    --pa-charcoal: #1e1b2e;
    --pa-slate: #64748b;
    --pa-success: #22c55e;
    --pa-danger: #f43f5e;
    --pa-warning: #f59e0b;
    --pa-tooltip-bg: #12131c;
    --pa-tooltip-text: #f1f5f9;
    --pa-radius-lg: 18px;
    --pa-radius-md: 14px;
    --pa-radius-sm: 10px;

    --pa-bg: #0a0a12;
    --pa-bg-elevated: #131320;
    --pa-card-bg: rgba(255, 255, 255, 0.045);
    --pa-card-bg-solid: #211f36;
    --pa-card-bg-secondary: rgba(255, 255, 255, 0.03);
    --pa-subtle-fill: rgba(255, 255, 255, 0.035);
    --pa-border: rgba(255, 255, 255, 0.09);
    --pa-border-strong: rgba(255, 255, 255, 0.18);
    --pa-text-primary: #f1f5f9;
    --pa-text-secondary: rgba(241, 245, 249, 0.7);
    --pa-text-muted: rgba(241, 245, 249, 0.5);
    --pa-text-disabled: rgba(241, 245, 249, 0.3);
    --readiness-track-color: rgba(148, 163, 184, 0.22);
    --pa-shadow-resting: 0 1px 2px rgba(0, 0, 0, 0.2), 0 2px 10px rgba(0, 0, 0, 0.16);
    --pa-shadow-soft: 0 4px 20px rgba(0, 0, 0, 0.18);
    --pa-shadow-hover: 0 10px 30px rgba(99, 102, 241, 0.22);
    --pa-table-header-bg: rgba(255, 255, 255, 0.05);
    --pa-table-row-alt-bg: rgba(255, 255, 255, 0.02);
    --pa-table-row-hover-bg: rgba(99, 102, 241, 0.12);
    --pa-table-border: var(--pa-border);
    --pa-table-selected-bg: rgba(99, 102, 241, 0.18);
    --pa-btn-primary-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    --pa-btn-secondary-bg: rgba(255, 255, 255, 0.05);
    --pa-btn-secondary-border: var(--pa-border);
    --pa-btn-disabled-bg: rgba(255, 255, 255, 0.03);
    --pa-btn-disabled-text: rgba(241, 245, 249, 0.28);
    --pa-scrollbar-thumb: rgba(99, 102, 241, 0.3);
    --pa-scrollbar-thumb-hover: rgba(99, 102, 241, 0.5);
    --pa-scrollbar-track: transparent;
    --pa-upload-border: rgba(255, 255, 255, 0.18);
    --pa-upload-bg: rgba(255, 255, 255, 0.02);
    --pa-upload-bg-hover: rgba(99, 102, 241, 0.07);
    --pa-upload-icon-bg: rgba(99, 102, 241, 0.16);

    --body-background-fill: var(--pa-bg);
    --background-fill-primary: var(--pa-bg-elevated);
    --background-fill-secondary: var(--pa-card-bg-solid);
    --border-color-primary: var(--pa-border);
    --border-color-accent: var(--pa-border);
    --body-text-color: var(--pa-text-primary);
    --body-text-color-subdued: var(--pa-text-muted);
    --block-background-fill: var(--pa-card-bg-solid);
    --block-border-color: var(--pa-border);
    --input-background-fill: var(--pa-bg-elevated);
    --table-even-background-fill: var(--pa-bg-elevated);
    --table-odd-background-fill: var(--pa-card-bg-solid);
    --table-border: var(--pa-border);
}

body.light-mode, .gradio-container.light-mode {
    --pa-bg: #f7f8fc;
    --pa-bg-elevated: #ffffff;
    --pa-card-bg: #ffffff;
    --pa-card-bg-solid: #ffffff;
    --pa-card-bg-secondary: #f1f2f8;
    --pa-subtle-fill: #f1f2f8;
    --pa-border: #e4e6f0;
    --pa-border-strong: #d5d8e5;
    --pa-text-primary: #14151f;
    --pa-text-secondary: #565973;
    --pa-text-muted: #85889f;
    --pa-text-disabled: #b7b9c6;
    --readiness-track-color: #e4e6f0;
    --pa-shadow-resting: 0 1px 2px rgba(15, 23, 42, 0.045), 0 2px 8px rgba(15, 23, 42, 0.05);
    --pa-shadow-soft: 0 1px 3px rgba(15, 23, 42, 0.05), 0 8px 22px rgba(15, 23, 42, 0.07);
    --pa-shadow-hover: 0 12px 28px rgba(99, 102, 241, 0.14), 0 2px 8px rgba(15, 23, 42, 0.06);
    --pa-table-header-bg: #f1f2f8;
    --pa-table-row-alt-bg: #fafbfd;
    --pa-table-row-hover-bg: #eef0fc;
    --pa-table-border: #e4e6f0;
    --pa-table-selected-bg: rgba(99, 102, 241, 0.09);
    --pa-btn-primary-shadow: 0 4px 14px rgba(99, 102, 241, 0.22);
    --pa-btn-secondary-bg: #ffffff;
    --pa-btn-secondary-border: #d5d8e5;
    --pa-btn-disabled-bg: #f1f2f8;
    --pa-btn-disabled-text: #b7b9c6;
    --pa-scrollbar-thumb: rgba(99, 102, 241, 0.25);
    --pa-scrollbar-thumb-hover: rgba(99, 102, 241, 0.45);
    --pa-scrollbar-track: #f1f2f8;
    --pa-upload-border: #d5d8e5;
    --pa-upload-bg: #fafbfd;
    --pa-upload-bg-hover: #f1f2fc;
    --pa-upload-icon-bg: rgba(99, 102, 241, 0.1);
    --body-background-fill: var(--pa-bg);
    --background-fill-primary: var(--pa-bg-elevated);
    --background-fill-secondary: #f1f2f8;
    --border-color-primary: var(--pa-border);
    --border-color-accent: var(--pa-border);
    --body-text-color: var(--pa-text-primary);
    --body-text-color-subdued: var(--pa-text-muted);
    --block-background-fill: var(--pa-bg-elevated);
    --block-border-color: var(--pa-border);
    --input-background-fill: #ffffff;
    --table-even-background-fill: #ffffff;
    --table-odd-background-fill: var(--pa-table-row-alt-bg);
    --table-border: var(--pa-border);
}

html, body, .gradio-container {
    background: var(--pa-bg) !important;
}

.kpi-card, .card, .rec-card, .cleaning-tool-card, .export-option-card, .mini-stat, .chart-card, .insight-card {
    box-shadow: var(--pa-shadow-resting);
}

.info-tooltip::after, .info-tooltip::before {
    box-shadow: var(--pa-shadow-soft);
}

body.light-mode .block, .gradio-container.light-mode .block, body.light-mode .form, .gradio-container.light-mode .form {
    background: var(--pa-bg-elevated) !important;
    border-color: var(--pa-border) !important;
    color: var(--pa-text-primary) !important;
}

body.light-mode .card .block, .gradio-container.light-mode .card .block, body.light-mode .card .form, .gradio-container.light-mode .card .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.upload-zone .wrap, .upload-zone [data-testid="file-upload"], .upload-zone .file-preview, .upload-zone .empty.wrap, .upload-zone .empty {
    background: var(--pa-upload-bg) !important;
    border: 1.5px dashed var(--pa-upload-border) !important;
    border-radius: var(--pa-radius-md) !important;
    color: var(--pa-text-secondary) !important;
    transition: background 0.2s ease, border-color 0.2s ease;
}

.upload-zone .wrap *, .upload-zone [data-testid="file-upload"] * {
    color: var(--pa-text-secondary) !important;
}

.upload-zone .wrap:hover, .upload-zone [data-testid="file-upload"]:hover {
    background: var(--pa-upload-bg-hover) !important;
    border-color: var(--pa-indigo) !important;
}

.upload-zone .icon-wrap {
    background: var(--pa-upload-icon-bg) !important;
    border-radius: 999px !important;
    color: var(--pa-indigo) !important;
    padding: 10px !important;
}

.upload-zone .icon-wrap svg {
    fill: var(--pa-indigo) !important;
    stroke: var(--pa-indigo) !important;
}

.accordion, .label-wrap, .accordion > .label-wrap, .accordion-header {
    background: var(--pa-bg-elevated) !important;
    color: var(--pa-text-primary) !important;
    border: 1px solid var(--pa-border) !important;
    border-radius: var(--pa-radius-md) !important;
}

.label-wrap:hover {
    color: var(--pa-indigo) !important;
}

table, .table-wrap, .cell-wrap {
    background: var(--pa-bg-elevated) !important;
    color: var(--pa-text-primary) !important;
    border-color: var(--pa-table-border) !important;
}

thead, thead th, .thead {
    background: var(--pa-table-header-bg) !important;
    color: var(--pa-text-primary) !important;
    font-weight: 700 !important;
    border-bottom: 1.5px solid var(--pa-table-border) !important;
}

tbody tr, tbody tr td {
    background: var(--pa-bg-elevated) !important;
    border-color: var(--pa-table-border) !important;
    transition: background 0.12s ease;
}

tbody tr:nth-child(even) td {
    background: var(--pa-table-row-alt-bg) !important;
}

tbody tr:hover td {
    background: var(--pa-table-row-hover-bg) !important;
}

td[aria-selected="true"], .cell-selected, td.selected {
    background: var(--pa-table-selected-bg) !important;
    outline: 1.5px solid var(--pa-indigo) !important;
    outline-offset: -1.5px;
}

.table-wrap {
    border: 1px solid var(--pa-table-border) !important;
    border-radius: var(--pa-radius-md) !important;
    overflow: hidden;
}

.theme-toggle-btn {
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    border: 1px solid var(--pa-border) !important;
    background: var(--pa-card-bg) !important;
    color: var(--pa-text-secondary) !important;
    box-shadow: none !important;
    white-space: nowrap;
}

.theme-toggle-btn:hover {
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: var(--pa-text-primary) !important;
    transform: translateY(-1px);
    transition: background-color 0.2s ease, border-color 0.2s ease,
                box-shadow 0.25s ease, transform 0.2s ease, opacity 0.2s ease;
}

.app-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 6px 4px 18px 4px;
}

.app-header-icon {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--pa-indigo), var(--pa-purple));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    color: white;
    box-shadow: var(--pa-shadow-hover);
}

.app-header-text h1 {
    margin: 0 !important;
    font-size: 27px !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, var(--pa-indigo), var(--pa-purple) 70%, var(--pa-blue-accent));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: var(--pa-text-primary);
}

.app-header-text p {
    margin: 4px 0 0 0;
    font-size: 14px;
    color: var(--pa-text-secondary);
}

.card {
    background: var(--pa-card-bg) !important;
    border: 1px solid var(--pa-border) !important;
    border-radius: var(--pa-radius-lg);
    padding: 22px !important;
    margin-bottom: 20px !important;
    box-shadow: var(--pa-shadow-soft);
    color: var(--pa-text-primary);
}

.card:hover {
    box-shadow: var(--pa-shadow-hover);
    border-color: rgba(99, 102, 241, 0.4) !important;
}

.card h4 {
    margin-top: 0 !important;
    margin-bottom: 12px !important;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--pa-text-primary);
}

.feedback-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 4px 0 8px 0;
}

.feedback-header-icon {
    flex-shrink: 0;
    width: 38px;
    height: 38px;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--pa-indigo), var(--pa-purple));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
    color: white;
    box-shadow: var(--pa-btn-primary-shadow);
}

.feedback-header h3 {
    margin: 0 !important;
    padding-left: 0 !important;
    font-size: 19px;
}

.feedback-header h3::before { display: none; }

.feedback-header p {
    margin: 2px 0 0 0;
    font-size: 14px;
    color: var(--pa-text-secondary);
}

.feedback-flow {
    max-width: 640px;
    margin: 0 auto;
}

.feedback-section {
    padding: 22px 0 !important;
    border-bottom: 1px solid var(--pa-border);
}

.feedback-section-last {
    border-bottom: none !important;
    padding-bottom: 6px !important;
}

.feedback-section p {
    font-size: 15px !important;
    font-weight: 600;
    color: var(--pa-text-primary);
    margin-bottom: 12px !important;
}

.feedback-flow .wrap label, .feedback-flow div[role="radiogroup"] label {
    border-radius: 10px !important;
    border: 1px solid var(--pa-border) !important;
    background: transparent !important;
    color: var(--pa-text-secondary) !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
}

.feedback-flow .wrap label:hover, .feedback-flow div[role="radiogroup"] label:hover {
    border-color: rgba(99, 102, 241, 0.5) !important;
    color: var(--pa-text-primary) !important;
    transform: translateY(-1px);
}

.feedback-flow .wrap label.selected, .feedback-flow div[role="radiogroup"] label.selected {
    background: rgba(99, 102, 241, 0.14) !important;
    border-color: var(--pa-indigo) !important;
    color: var(--pa-indigo) !important;
    font-weight: 600 !important;
}

.upload-zone {
    border: 1.5px dashed rgba(99, 102, 241, 0.4) !important;
    border-radius: var(--pa-radius-lg) !important;
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.04)) !important;
    padding: 22px !important;
    text-align: center;
}

.upload-zone:hover {
    border-color: var(--pa-indigo) !important;
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.13), rgba(139, 92, 246, 0.06)) !important;
}

button.primary, .cta-button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    background: linear-gradient(135deg, var(--pa-indigo), var(--pa-purple)) !important;
    border: none !important;
    color: white !important;
    box-shadow: var(--pa-btn-primary-shadow);
    transition: box-shadow 0.15s ease, transform 0.15s ease, opacity 0.15s ease;
}

button.primary:hover, .cta-button:hover {
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
    transform: translateY(-1px);
}

button.primary:active, .cta-button:active {
    transform: translateY(0);
    box-shadow: var(--pa-btn-primary-shadow);
}

button.secondary {
    background: var(--pa-btn-secondary-bg) !important;
    border: 1px solid var(--pa-btn-secondary-border) !important;
    color: var(--pa-text-secondary) !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    transition: border-color 0.15s ease, color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}

button.secondary:hover {
    border-color: var(--pa-indigo) !important;
    color: var(--pa-indigo) !important;
    transform: translateY(-1px);
}

button.secondary:active {
    transform: translateY(0);
}

button:disabled, button.primary:disabled, button.secondary:disabled {
    background: var(--pa-btn-disabled-bg) !important;
    color: var(--pa-btn-disabled-text) !important;
    border-color: var(--pa-border) !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
    transform: none !important;
    opacity: 1 !important;
}

button {
    border-radius: 10px !important;
}

.tab-nav {
    gap: 6px;
    border-bottom: 1px solid var(--pa-border) !important;
    padding: 4px 2px 10px 2px;
    flex-wrap: wrap !important;
    row-gap: 8px;
    overflow: visible !important;
}

.tab-nav button {
    border-radius: 10px !important;
    font-weight: 500;
    font-size: 13.5px !important;
    padding: 8px 16px !important;
    opacity: 0.72;
    flex: 0 0 auto !important;
    letter-spacing: -0.005em;
    border: 1px solid transparent !important;
    transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
}

.tab-nav button:hover:not(.selected) {
    opacity: 1;
    background: var(--pa-subtle-fill) !important;
    color: var(--pa-text-primary) !important;
    transform: translateY(-1px);
}

.tab-nav button.selected {
    opacity: 1;
    font-weight: 700;
    color: #ffffff !important;
    background: linear-gradient(135deg, var(--pa-indigo), var(--pa-purple)) !important;
    border: 1px solid transparent !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.tab-nav > button[aria-label*="tab" i], .tab-nav > button[title*="tab" i], .tab-nav .dropdown-arrow {
    display: none !important;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 16px;
    margin-top: 10px;
}

.kpi-card {
    background: var(--pa-card-bg);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 20px 16px;
    text-align: center;
    box-shadow: var(--pa-shadow-soft);
    position: relative;
    overflow: hidden;
    color: var(--pa-text-primary);
}

.kpi-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--pa-indigo), var(--pa-purple), var(--pa-cyan));
    opacity: 0.85;
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--pa-shadow-hover);
    border-color: rgba(99, 102, 241, 0.4);
}

.kpi-icon {
    font-size: 24px;
    margin-bottom: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(139, 92, 246, 0.18));
    border: 1px solid rgba(99, 102, 241, 0.2);
}

.kpi-value {
    font-size: 27px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.025em;
    color: var(--pa-text-primary);
}

.kpi-label {
    font-size: 12.5px;
    color: var(--pa-text-secondary);
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.kpi-subchips {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-top: 10px;
    flex-wrap: wrap;
}

.kpi-subchip {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 999px;
    background: rgba(99, 102, 241, 0.12);
    color: var(--pa-indigo);
    text-transform: none;
    letter-spacing: 0;
}

.kpi-empty {
    padding: 40px 24px;
    border-radius: var(--pa-radius-lg);
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.06), rgba(139, 92, 246, 0.03));
    border: 1.5px dashed rgba(99, 102, 241, 0.35);
    text-align: center;
    color: var(--pa-text-secondary);
    font-size: 14.5px;
    position: relative;
}

.kpi-empty::before {
    content: " ";
    display: block;
    font-size: 26px;
    margin-bottom: 10px;
    background: linear-gradient(135deg, var(--pa-indigo), var(--pa-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.kpi-empty b {
    color: var(--pa-text-primary);
}

h3, h4 {
    position: relative;
    padding-left: 14px !important;
    margin: 20px 0 12px 0 !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
    color: var(--pa-text-primary) !important;
}

h3::before, h4::before {
    content: "";
    position: absolute;
    left: 0;
    top: 3px;
    bottom: 3px;
    width: 4px;
    border-radius: 4px;
    background: linear-gradient(180deg, var(--pa-indigo), var(--pa-purple));
}

h4::before {
    width: 3px;
    background: linear-gradient(180deg, var(--pa-purple), var(--pa-cyan));
}

.card h4, .card h4::before {
    padding-left: 0 !important;
}

.card h4::before { display: none; }

.readiness-card {
    display: flex;
    align-items: center;
    gap: 32px;
    flex-wrap: wrap;
    background: var(--pa-card-bg);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-lg);
    padding: 28px;
    box-shadow: var(--pa-shadow-soft);
    color: var(--pa-text-primary);
}

.readiness-gauge {
    flex-shrink: 0;
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--pa-shadow-soft), inset 0 0 0 1px var(--pa-border);
}

.readiness-gauge-inner {
    width: 108px;
    height: 108px;
    border-radius: 50%;
    background: var(--pa-card-bg-solid);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: var(--pa-shadow-resting);
}

.readiness-score {
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1;
    color: var(--pa-text-primary);
}

.readiness-score-max {
    font-size: 12px;
    color: var(--pa-text-muted);
    margin-top: 2px;
}

.readiness-details {
    flex: 1;
    min-width: 240px;
}

.readiness-badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 16px;
}

.readiness-bars {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.readiness-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    margin-bottom: 4px;
    color: var(--pa-text-secondary);
}

.readiness-bar-value {
    font-weight: 600;
    color: var(--pa-text-muted);
}

.readiness-bar-track {
    width: 100%;
    height: 7px;
    border-radius: 999px;
    background: var(--readiness-track-color);
    overflow: hidden;
}

.readiness-bar-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--pa-purple), var(--pa-indigo));
}

.meta-section-heading {
    margin-top: 34px !important;
}

.meta-card {
    background: var(--pa-card-bg);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-lg);
    padding: 20px;
    box-shadow: var(--pa-shadow-soft);
    overflow-x: auto;
}

.meta-subsection-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--pa-text-secondary);
    margin: 4px 0 10px 0;
}

.meta-subsection-title:not(:first-child) {
    margin-top: 20px;
}

.meta-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin-bottom: 8px;
}

.meta-table th {
    text-align: left;
    padding: 8px 12px;
    color: var(--pa-text-secondary);
    font-weight: 600;
    border-bottom: 1px solid var(--pa-border);
    white-space: nowrap;
}

.meta-table td {
    padding: 8px 12px;
    color: var(--pa-text-primary);
    border-bottom: 1px solid var(--pa-border);
    white-space: nowrap;
}

.meta-table tr:hover td {
    background: rgba(99, 102, 241, 0.05);
}

.profile-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
}

.profile-card {
    background: var(--pa-card-bg);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 16px;
    box-shadow: var(--pa-shadow-soft);
}

.profile-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-2px);
}

.profile-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.profile-col-name {
    font-weight: 700;
    font-size: 14px;
    color: var(--pa-text-primary);
}

.profile-dtype-badge {
    font-size: 10.5px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(99, 102, 241, 0.14);
    color: var(--pa-indigo);
}

.profile-card-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 10px;
}

.profile-stat {
    display: flex;
    justify-content: space-between;
    font-size: 12.5px;
    color: var(--pa-text-secondary);
}

.profile-stat b {
    color: var(--pa-text-primary);
}

.profile-usage {
    font-size: 12px;
    color: var(--pa-text-muted);
    border-top: 1px solid var(--pa-border);
    padding-top: 8px;
    font-style: italic;
}

.bi-kpi-block {
    margin-bottom: 22px;
}

.bi-kpi-column-title {
    font-weight: 700;
    font-size: 14px;
    color: var(--pa-indigo);
    margin-bottom: 8px;
}

.bi-kpi-grid .kpi-card {
    padding: 12px 8px;
}

.bi-kpi-grid .kpi-value {
    font-size: 17px;
}

.chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
}

.chart-card {
    background: var(--pa-card-bg);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 14px;
    box-shadow: var(--pa-shadow-soft);
    text-align: center;
}

.chart-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
}

.chart-card-title {
    font-weight: 600;
    font-size: 13px;
    color: var(--pa-text-secondary);
    margin-bottom: 8px;
}

.chart-card-img {
    width: 100%;
    height: auto;
    border-radius: 8px;
}

.chart-insight-box {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-top: 14px;
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-left: 3px solid var(--pa-indigo);
    border-radius: var(--pa-radius-md);
    padding: 14px 16px;
}

.chart-insight-icon {
    font-size: 17px;
    flex-shrink: 0;
    line-height: 1.4;
}

.chart-insight-text {
    font-size: 12.5px;
    line-height: 1.6;
    color: var(--pa-text-secondary);
}

.chart-insight-text b {
    color: var(--pa-text-primary);
}

.insight-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 14px;
}

.insight-card {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    background: var(--pa-card-bg);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 16px;
    box-shadow: var(--pa-shadow-soft);
}

.insight-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-2px);
}

.insight-icon {
    font-size: 20px;
    flex-shrink: 0;
}

.insight-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.insight-title {
    font-weight: 700;
    font-size: 13.5px;
    color: var(--pa-text-primary);
    margin-bottom: 0;
}

.insight-badge {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(99, 102, 241, 0.14);
    color: var(--pa-indigo);
    white-space: nowrap;
    flex-shrink: 0;
}

.insight-description {
    font-size: 12.5px;
    color: var(--pa-text-secondary);
    line-height: 1.4;
}

.workspace-chat-card {
    padding: 22px !important;
}

.workspace-chat-card .chatbot, .workspace-chat-card [data-testid="chatbot"] {
    border-radius: var(--pa-radius-md) !important;
}

.pivot-card {
    padding: 20px !important;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.pivot-field-row {
    gap: 20px !important;
}

.pivot-generate-button {
    margin-top: 2px !important;
}

.pivot-multiselect .token, .pivot-multiselect [class*="token"], .pivot-select .token, .pivot-select [class*="token"] {
    background: rgba(99, 102, 241, 0.16) !important;
    border: 1px solid rgba(99, 102, 241, 0.35) !important;
    color: var(--pa-indigo) !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    padding: 3px 10px !important;
    box-shadow: none !important;
}

.pivot-multiselect .token:hover, .pivot-multiselect [class*="token"]:hover {
    border-color: var(--pa-indigo) !important;
    background: rgba(99, 102, 241, 0.24) !important;
}

.pivot-multiselect .token svg, .pivot-multiselect [class*="token"] svg, .pivot-multiselect .token button, .pivot-multiselect [class*="token"] button {
    color: var(--pa-indigo) !important;
    opacity: 0.75;
}

.pivot-multiselect .wrap-inner, .pivot-select .wrap-inner, .pivot-multiselect [data-testid="dropdown"], .pivot-select [data-testid="dropdown"] {
    background: var(--pa-card-bg-solid) !important;
    border-radius: var(--pa-radius-md) !important;
    border: 1px solid var(--pa-border) !important;
}

.pivot-multiselect .wrap-inner:focus-within, .pivot-select .wrap-inner:focus-within {
    border-color: rgba(99, 102, 241, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
}

.pivot-result-card {
    padding: 20px !important;
}

.pivot-result-card .dataframe {
    border-radius: var(--pa-radius-md) !important;
}

.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12.5px;
    font-weight: 600;
}

.suggestion-chip-row {
    flex-wrap: wrap !important;
    gap: 8px !important;
    margin-bottom: 4px;
}

.suggestion-chip {
    border-radius: 999px !important;
    border: 1px solid var(--pa-border) !important;
    background: transparent !important;
    color: var(--pa-text-secondary) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    flex: 0 0 auto !important;
    box-shadow: none !important;
}

.suggestion-chip:hover {
    border-color: var(--pa-indigo) !important;
    color: var(--pa-indigo) !important;
    background: rgba(99, 102, 241, 0.08) !important;
    transform: translateY(-1px);
}

.examples-popover {
    max-height: 260px;
    overflow-y: auto;
    border-radius: var(--pa-radius-md) !important;
}

.cleaning-widget-note {
    font-size: 12px;
    color: var(--pa-text-muted);
    display: block;
    margin: -4px 0 10px 0;
}

.page-intro {
    margin-bottom: 20px;
}

.page-intro-eyebrow {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.08em;
    background: linear-gradient(90deg, var(--pa-indigo), var(--pa-blue-accent));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: var(--pa-indigo);
    margin-bottom: 4px;
}

.page-intro-title {
    font-size: 21px !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em;
    color: var(--pa-text-primary) !important;
    margin: 0 0 6px 0 !important;
}

.page-intro-subtitle {
    font-size: 13px;
    color: var(--pa-text-secondary);
    line-height: 1.6;
    max-width: 640px;
    margin: 0;
}

.toolkit-header {
    margin: 26px 0 14px 0;
}

.toolkit-title {
    font-size: 16px !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em;
    color: var(--pa-text-primary) !important;
    margin: 0 0 3px 0 !important;
}

.toolkit-subtitle {
    font-size: 12.5px;
    color: var(--pa-text-secondary);
    margin: 0;
}

.cleaning-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 18px;
    margin: 0 0 20px 0;
    align-items: stretch;
}

.cleaning-grid > .card.cleaning-tool-card {
    margin-bottom: 0 !important;
    padding: 20px !important;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.tool-card-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding-bottom: 12px;
    margin-bottom: 2px;
    border-bottom: 1px solid var(--pa-border);
}

.tool-card-icon {
    font-size: 18px;
    line-height: 1;
    flex-shrink: 0;
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.16), rgba(139, 92, 246, 0.16));
    border: 1px solid rgba(99, 102, 241, 0.18);
    color: var(--pa-indigo);
    border-radius: var(--pa-radius-md);
}

.tool-card-title {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.005em;
    color: var(--pa-text-primary);
    line-height: 1.3;
}

.tool-card-desc {
    font-size: 11.5px;
    color: var(--pa-text-secondary);
    margin-top: 2px;
}

.tool-method-note {
    font-size: 11.5px;
    color: var(--pa-text-muted);
    line-height: 1.5;
    background: var(--pa-subtle-fill);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 8px 10px;
}

.tool-method-note b {
    color: var(--pa-text-secondary);
}

.outlier-controls-row {
    gap: 10px !important;
    align-items: end !important;
}

.cleaning-plan-card {
    border-color: rgba(99, 102, 241, 0.3) !important;
    background: linear-gradient(180deg, rgba(99, 102, 241, 0.06), rgba(139, 92, 246, 0.02)) !important;
    padding: 20px !important;
}

.cleaning-field-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    color: var(--pa-text-secondary);
    margin-top: 2px;
}

.info-tooltip {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    background: rgba(99, 102, 241, 0.16);
    color: var(--pa-indigo);
    font-size: 10.5px;
    font-weight: 700;
    cursor: help;
    flex-shrink: 0;
}

.info-tooltip::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 135%;
    left: 50%;
    transform: translateX(-50%);
    background: var(--pa-tooltip-bg);
    color: var(--pa-tooltip-text);
    border: 1px solid var(--pa-border);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 11.5px;
    font-weight: 500;
    line-height: 1.45;
    white-space: normal;
    width: max-content;
    max-width: 230px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.15s ease;
    z-index: 60;
    pointer-events: none;
}

.info-tooltip::before {
    content: "";
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: var(--pa-tooltip-bg);
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.15s ease;
    z-index: 60;
}

.info-tooltip:hover::after, .info-tooltip:hover::before {
    opacity: 1;
    visibility: visible;
}

.segmented-control .wrap {
    display: flex !important;
    flex-wrap: wrap;
    gap: 8px !important;
    background: transparent !important;
}

.segmented-control label {
    border: 1px solid var(--pa-border) !important;
    border-radius: 999px !important;
    padding: 6px 14px !important;
    background: var(--pa-subtle-fill) !important;
    color: var(--pa-text-secondary) !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
}

.segmented-control label * {
    color: inherit !important;
}

.segmented-control input[type="radio"] {
    display: none !important;
}

.segmented-control label:hover {
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: var(--pa-text-primary) !important;
}

.segmented-control label:has(input:checked) {
    background: rgba(99, 102, 241, 0.18) !important;
    border-color: var(--pa-indigo) !important;
    color: var(--pa-indigo) !important;
}

.outlier-strategy-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    margin-top: 2px;
}

.outlier-strategy-legend-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11.5px;
    color: var(--pa-text-muted);
}

.mini-stat-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.mini-stat {
    background: var(--pa-subtle-fill);
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 8px 10px;
    text-align: center;
}

.mini-stat-value {
    font-size: 16px;
    font-weight: 800;
    color: var(--pa-text-primary);
    line-height: 1.2;
}

.mini-stat-label {
    font-size: 9.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--pa-text-muted);
    margin-top: 2px;
}

.mini-stat-empty {
    font-size: 12px;
    color: var(--pa-text-muted);
    padding: 8px 2px;
}

.mini-stat-clean {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--pa-text-secondary);
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: var(--pa-radius-md);
    padding: 9px 12px;
}

.mini-stat-clean-icon {
    color: #22c55e;
    font-weight: 800;
}

.cleaning-search-box input {
    font-size: 12.5px !important;
    border-radius: 999px !important;
    padding: 9px 16px !important;
    background: var(--pa-subtle-fill) !important;
    border: 1px solid var(--pa-border) !important;
    transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}

.cleaning-search-box input:focus {
    background: var(--pa-bg-elevated) !important;
    border-color: var(--pa-indigo) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
}

.cleaning-compact-table {
    max-height: 220px;
    overflow-y: auto !important;
}

.cleaning-compact-table table {
    font-size: 12px !important;
}

.form, .block { border-radius: var(--pa-radius-md) !important; }

.cleaning-export-card {
    margin-bottom: 4px !important;
    padding: 20px !important;
}

.export-card-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 14px;
}

.export-card-icon {
    font-size: 22px;
    line-height: 1;
    flex-shrink: 0;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.16), rgba(139, 92, 246, 0.16));
    border: 1px solid rgba(99, 102, 241, 0.18);
    border-radius: var(--pa-radius-md);
}

.export-card-title {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.005em;
    color: var(--pa-text-primary);
}

.export-card-subtitle {
    font-size: 12px;
    color: var(--pa-text-secondary);
    margin-top: 2px;
}

.export-options-row {
    gap: 12px !important;
}

.export-option-card {
    border: 1px solid var(--pa-border);
    border-radius: var(--pa-radius-md);
    padding: 10px 10px 12px 10px !important;
    text-align: center;
    transition: border-color 0.15s ease, transform 0.15s ease;
    background: var(--pa-subtle-fill);
}

.export-option-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-1px);
}

.export-option-btn {
    font-weight: 700 !important;
    width: 100%;
}

.export-option-caption {
    font-size: 10.5px;
    color: var(--pa-text-muted);
    margin-top: 6px;
}

.export-success-banner-inner {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--pa-text-primary);
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.35);
    border-radius: var(--pa-radius-md);
    padding: 10px 14px;
    margin-top: 4px;
}

.export-success-icon {
    font-size: 14px;
}

.export-output {
    margin-top: 6px;
}

.gradio-container {
    max-width: 1320px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 28px 32px 48px 32px !important;
}

@media (max-width: 900px) {
    .gradio-container { padding: 18px 16px 32px 16px !important; }
}

.app-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}

@keyframes pa-fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

.tabitem {
    animation: pa-fade-in 0.28s ease;
}

.kpi-card, .rec-card, .cleaning-tool-card, .export-option-card {
    animation: pa-fade-in 0.32s ease;
}

.accordion, .gr-accordion {
    transition: all 0.25s ease;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--pa-scrollbar-track); }
::-webkit-scrollbar-thumb {
    background: var(--pa-scrollbar-thumb);
    border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover { background: var(--pa-scrollbar-thumb-hover); }
* { scrollbar-width: thin; scrollbar-color: var(--pa-scrollbar-thumb) var(--pa-scrollbar-track); }
"""

# ----------------------------------------------------------------------
# THEME TOGGLE (Light / Dark)
# ----------------------------------------------------------------------
THEME_INIT_JS = """
() => {
    const applyClass = (isLight) => {
        document.body.classList.toggle('light-mode', isLight);
        document.querySelectorAll('.gradio-container').forEach((el) => {
            el.classList.toggle('light-mode', isLight);
        });
    };
    const saved = sessionStorage.getItem('datamind-theme');
    const isLight = saved === 'light';
    applyClass(isLight);
    let attempts = 0;
    const retry = setInterval(() => {
        applyClass(isLight);
        attempts += 1;
        if (attempts > 15) clearInterval(retry);
    }, 150);
    const wrapper = document.getElementById('theme-toggle-btn');
    const btn = wrapper ? (wrapper.querySelector('button') || wrapper) : null;
    if (btn) {
        btn.textContent = isLight ? '   Dark Mode' : '   Light Mode';
    }
}
"""

THEME_TOGGLE_JS = """
() => {
    const currentlyLight = document.body.classList.contains('light-mode');
    const isLight = !currentlyLight;
    document.body.classList.toggle('light-mode', isLight);
    document.querySelectorAll('.gradio-container').forEach((el) => {
        el.classList.toggle('light-mode', isLight);
    });
    sessionStorage.setItem('datamind-theme', isLight ? 'light' : 'dark');
    const wrapper = document.getElementById('theme-toggle-btn');
    const btn = wrapper ? (wrapper.querySelector('button') || wrapper) : null;
    if (btn) {
        btn.textContent = isLight ? '   Dark Mode' : '   Light Mode';
    }
}
"""

# ----------------------------------------------------------------------
# BUILD THE GRADIO APP
# ----------------------------------------------------------------------
with gr.Blocks(
    title="DataMind",
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="purple",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    ),
    css=CUSTOM_CSS,
    js=THEME_INIT_JS,
) as demo:
    with gr.Row(elem_classes="app-header-row"):
        gr.HTML(
            """
            <div class="app-header">
                <div class="app-header-icon"> </div>
                <div class="app-header-text">
                    <h1>DataMind</h1>
                    <p>Upload a CSV or Excel file to explore, clean, visualize, and chat with your data. Developed by Ridham Bansal.</p>
                </div>
            </div>
            """
        )
        theme_toggle_button = gr.Button(
            "   Light Mode", elem_id="theme-toggle-btn", elem_classes="theme-toggle-btn",
        )

    dataset_state = gr.State(value=None)

    with gr.Group(elem_classes="upload-zone"):
        gr.Markdown("**Upload your dataset**   CSV or Excel (.xlsx / .xls)")
        file_input = gr.File(
            label="",
            show_label=False,
            file_types=[".csv", ".xlsx", ".xls"],
        )
        load_button = gr.Button("Load Dataset", variant="primary", elem_classes="cta-button")
    status_box = gr.Markdown("No file loaded yet.")

    with gr.Accordion("Upload History", open=False):
        upload_history_output = gr.Dataframe(
            value=get_upload_history(),
            label="Every dataset you've loaded, most recent first",
            headers=["Filename", "Timestamp", "Rows", "Columns"],
            wrap=True,
        )

    with gr.Tabs():
        # ============================ TAB 1: DASHBOARD ============================
        with gr.Tab("   Dashboard"):
            gr.Markdown("### Overview of your dataset")
            dashboard_output = gr.HTML(format_stats_as_kpi_cards({}))
            gr.Markdown("###   Dataset Preview (first 10 rows)")
            preview_output = gr.Dataframe(label="Preview", wrap=True)

        # ============================ TAB 2: DATASET METADATA ============================
        with gr.Tab("  Data Insights"):
            gr.Markdown(
                "### Dataset Analytics Report\n"
                "An automatically generated analytical report   statistical summaries, dataset-aware "
                "charts, BI-style KPIs, and smart insights."
            )
            metadata_top_output = gr.HTML(render_metadata_top_html(None))
            gr.Markdown("### Business Intelligence KPIs")
            metric_selector_dropdown = gr.Dropdown(
                choices=[], value=None, label="Select Metric to Analyze",
            )
            bi_kpis_output = gr.HTML(format_bi_kpis_html({}))
            gr.Markdown("### Quick Visual Summary")
            gr.Markdown(
                "<span class='cleaning-widget-note'>Explore any column without leaving this tab   "
                "pick one below to see its distribution, plus a short AI-generated insight.</span>"
            )
            visual_summary_column_dropdown = gr.Dropdown(
                choices=[], value=None, label="Select a Column",
            )
            visual_summary_output = gr.HTML(
                "<div class='kpi-empty'>Load a dataset to explore its columns visually.</div>"
            )
            metadata_bottom_output = gr.HTML("")

        # ============================ TAB 3: DATA CLEANING ============================
        with gr.Tab("   PreProcessing"):
            gr.HTML(
                "<div class='page-intro'>"
                "<div class='page-intro-eyebrow'>DATA PREPARATION</div>"
                "<h3 class='page-intro-title'>Clean your dataset</h3>"
                "<p class='page-intro-subtitle'>A focused toolkit: handle missing values and "
                "outliers, preview the plan, then export the result. Your original dataset in the "
                "other tabs is never changed.</p>"
                "</div>"
            )
            cleaned_dataset_state = gr.State(value=None)

            with gr.Group(elem_classes="card cleaning-export-card"):
                gr.HTML(
                    "<div class='export-card-header'>"
                    "<div class='export-card-icon'> </div>"
                    "<div>"
                    "<div class='export-card-title'>Export Cleaned Dataset</div>"
                    "<div class='export-card-subtitle'>Pick a format once you've applied changes "
                    "below.</div>"
                    "</div>"
                    "</div>"
                )
                with gr.Row(elem_classes="export-options-row"):
                    with gr.Column(elem_classes="export-option-card", min_width=140):
                        export_csv_button = gr.Button("   CSV", elem_classes="export-option-btn")
                        gr.HTML("<div class='export-option-caption'>Universal spreadsheet format</div>")
                    with gr.Column(elem_classes="export-option-card", min_width=140):
                        export_excel_button = gr.Button("   Excel", elem_classes="export-option-btn")
                        gr.HTML("<div class='export-option-caption'>.xlsx with column formatting</div>")
                
                export_success_banner = gr.HTML(visible=False)
                export_file_output = gr.File(
                    label="Your cleaned dataset",
                    interactive=False,
                    visible=False,
                    elem_classes="export-output",
                )

            gr.HTML(
                "<div class='toolkit-header'>"
                "<h3 class='toolkit-title'>Cleaning Toolkit</h3>"
                "<p class='toolkit-subtitle'>Two focused tools   hover the   next to any option "
                "for a quick explanation.</p>"
                "</div>"
            )

            with gr.Column(elem_classes="cleaning-grid"):
                # TOOL 1: MISSING VALUES
                with gr.Group(elem_classes="card cleaning-tool-card"):
                    gr.HTML(
                        "<div class='tool-card-header'>"
                        "<div class='tool-card-icon'> </div>"
                        "<div>"
                        "<div class='tool-card-title'>Missing Values</div>"
                        "<div class='tool-card-desc'>Find and fill gaps in your data.</div>"
                        "</div>"
                        "</div>"
                    )
                    missing_stats_output = gr.HTML(format_missing_value_stats_html(get_missing_value_stats(None)))
                    missing_search_box = gr.Textbox(
                        placeholder="  Search columns...",
                        show_label=False,
                        elem_classes="cleaning-search-box",
                    )
                    missing_summary_output = gr.Dataframe(
                        value=get_missing_summary(None),
                        headers=["Column", "Missing Count", "Missing %"],
                        wrap=True,
                        show_label=False,
                        elem_classes="cleaning-compact-table",
                    )
                    gr.HTML(
                        "<div class='cleaning-field-label'>Cleaning Strategy"
                        "<span class='info-tooltip' data-tooltip='Choose how missing values are "
                        "handled: drop incomplete rows, or automatically fill numeric columns "
                        "(mean/median) or categorical columns (most frequent value).'> </span></div>"
                    )
                    missing_strategy_dropdown = gr.Dropdown(
                        choices=MISSING_VALUE_STRATEGIES,
                        value="Do Nothing",
                        show_label=False,
                    )

                # TOOL 2: OUTLIER HANDLING
                with gr.Group(elem_classes="card cleaning-tool-card"):
                    gr.HTML(
                        "<div class='tool-card-header'>"
                        "<div class='tool-card-icon'> </div>"
                        "<div>"
                        "<div class='tool-card-title'>Outlier Handling</div>"
                        "<div class='tool-card-desc'>Spot and neutralize extreme values.</div>"
                        "</div>"
                        "</div>"
                    )
                    gr.HTML(
                        "<div class='tool-method-note'>Detection uses the <b>1.5 IQR rule</b>: any "
                        "value below Q1   1.5 IQR or above Q3 + 1.5 IQR is flagged as an outlier.</div>"
                    )
                    with gr.Row(elem_classes="outlier-controls-row"):
                        outlier_column_dropdown = gr.Dropdown(
                            choices=[], value=None, label="Numeric Column", scale=3,
                        )
                        detect_outliers_button = gr.Button("Detect", elem_classes="export-option-btn", scale=1)
                    outlier_status_output = gr.Markdown("")
                    gr.HTML("<div class='cleaning-field-label'>Outlier Strategy</div>")
                    outlier_strategy_radio = gr.Radio(
                        choices=OUTLIER_STRATEGIES,
                        value="Do Nothing",
                        show_label=False,
                        elem_classes="segmented-control",
                    )
                    gr.HTML(
                        "<div class='outlier-strategy-legend'>"
                        "<span class='outlier-strategy-legend-item'>Remove Outliers"
                        "<span class='info-tooltip' data-tooltip='Permanently removes rows "
                        "containing detected outliers from the cleaned dataset.'> </span></span>"
                        "<span class='outlier-strategy-legend-item'>Replace with Maximum Value"
                        "<span class='info-tooltip' data-tooltip='Replaces each detected outlier "
                        "with the maximum valid (non-outlier) value found in that column, keeping "
                        "the row instead of deleting it.'> </span></span>"
                        "</div>"
                    )

            with gr.Group(elem_classes="card cleaning-plan-card"):
                gr.Markdown("####   Planned Changes")
                cleaning_plan_output = gr.Markdown("Upload a dataset to see the cleaning plan.")

            apply_cleaning_button = gr.Button("Apply Cleaning", variant="primary", size="lg")
            cleaning_summary_output = gr.Markdown("")
            gr.Markdown("#### Cleaned Data Preview (first 10 rows)")
            cleaned_preview_output = gr.Dataframe(label="Cleaned Preview", wrap=True)

        # ============================ TAB 4: AI WORKSPACE ============================
        with gr.Tab("   AI Workspace"):
            openai_status = (
                "  OpenAI-assisted routing is active for tricky questions."
                if is_openai_available()
                else "  Running in rule-based mode   still fully functional for common questions."
            )
            gr.HTML(
                f"""
                <div class="feedback-header">
                    <div class="feedback-header-icon"> </div>
                    <div>
                        <h3>AI Assistant</h3>
                        <p>Ask anything about your dataset   answers are computed directly from your data. {openai_status}</p>
                    </div>
                </div>
                """
            )
            with gr.Row(elem_classes="suggestion-chip-row") as suggestion_chips_row:
                chip_summarize = gr.Button("Summarize Dataset", elem_classes="suggestion-chip", size="sm")
                chip_missing = gr.Button("Explain Missing Values", elem_classes="suggestion-chip", size="sm")
                chip_outliers = gr.Button("Find Outliers", elem_classes="suggestion-chip", size="sm")
                chip_correlation = gr.Button("Correlation Analysis", elem_classes="suggestion-chip", size="sm")
                chip_cleaning = gr.Button("Cleaning Suggestions", elem_classes="suggestion-chip", size="sm")
                chip_target = gr.Button("Best Target Column", elem_classes="suggestion-chip", size="sm")

            with gr.Group(elem_classes="card workspace-chat-card"):
                chat_history_state = gr.State(value=[])
                chatbot_display = gr.Chatbot(
                    label="VizBot",
                    height=560,
                    placeholder="  **Ask a question about your dataset to get started.**\n\nExamples: *\"What is the average salary?\"*   *\"Summarize this dataset\"*   *\"Which columns have missing values?\"*",
                )
                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder="Ask a question about your dataset...",
                        show_label=False,
                        scale=4,
                    )
                    chat_send_button = gr.Button("  Send", variant="primary", scale=1)
                chat_clear_button = gr.Button("  Clear Chat")

            with gr.Accordion("More examples", open=False, elem_classes="examples-popover"):
                gr.Markdown(get_example_questions_markdown())

        # ============================ TAB 5: VISUALIZATION STUDIO ============================
        with gr.Tab("   Visualization"):
            gr.Markdown(
                "### Build your own chart\n"
                "Pick a chart type and feature(s), then click **Generate Visualization**. "
                "Nothing is drawn automatically."
            )
            with gr.Row():
                with gr.Column(scale=1):
                    chart_type_dropdown = gr.Dropdown(
                        choices=CHART_TYPES,
                        value="Histogram",
                        label="Chart Type",
                    )
                with gr.Column(scale=1):
                    feature1_dropdown = gr.Dropdown(
                        choices=[], value=None, label="Feature 1 (Numeric Column)",
                        visible=True, interactive=True,
                    )
                with gr.Column(scale=1):
                    feature2_dropdown = gr.Dropdown(
                        choices=[], value=None, label="Feature 2 (not needed for this chart)",
                        visible=True, interactive=False,
                    )

            viz_availability_warning = gr.Markdown("")
            generate_viz_button = gr.Button("  Generate Visualization", variant="primary")
            viz_status_output = gr.Markdown("")
            viz_plot_output = gr.Plot(label="Chart")

            gr.Markdown(
                "### Pivot Table Builder\n"
                "Configure **Rows**, **Columns**, **Values**, and an **Aggregation**   just like "
                "Excel's PivotTable   then click **Generate Pivot Table**. Add an optional **Filter** "
                "to narrow the data first."
            )
            with gr.Group(elem_classes="card pivot-card"):
                with gr.Row(elem_classes="pivot-field-row"):
                    pivot_rows_dropdown = gr.Dropdown(
                        choices=[], value=[], multiselect=True,
                        label="Rows", elem_classes="pivot-multiselect",
                    )
                    pivot_columns_dropdown = gr.Dropdown(
                        choices=[], value=[], multiselect=True,
                        label="Columns (optional)", elem_classes="pivot-multiselect",
                    )
                with gr.Row(elem_classes="pivot-field-row"):
                    pivot_values_dropdown = gr.Dropdown(
                        choices=[], value=[], multiselect=True,
                        label="Values", elem_classes="pivot-multiselect",
                    )
                    pivot_aggregation_dropdown = gr.Dropdown(
                        choices=PIVOT_AGGREGATIONS, value="Sum",
                        label="Aggregation", elem_classes="pivot-select",
                    )
                with gr.Row(elem_classes="pivot-field-row"):
                    pivot_filter_column_dropdown = gr.Dropdown(
                        choices=[], value=None,
                        label="Filter Field (optional)", elem_classes="pivot-select",
                    )
                    pivot_filter_value_dropdown = gr.Dropdown(
                        choices=[], value=[], multiselect=True,
                        label="Filter Values", elem_classes="pivot-multiselect",
                    )
                generate_pivot_button = gr.Button(
                    "  Generate Pivot Table", variant="primary", elem_classes="pivot-generate-button"
                )

            with gr.Group(elem_classes="card pivot-result-card"):
                pivot_status_output = gr.Markdown("")
                pivot_table_output = gr.Dataframe(label="Pivot Table", wrap=True)

        # ============================ TAB 6: FEEDBACK ============================
        with gr.Tab("   Feedback"):
            gr.HTML(
                """
                <div class="feedback-header">
                    <div class="feedback-header-icon"> </div>
                    <div>
                        <h3>We'd love your feedback</h3>
                        <p>Help us improve DataMind   it takes less than a minute.</p>
                    </div>
                </div>
                """
            )
            with gr.Column(elem_classes="feedback-flow"):
                with gr.Column(elem_classes="feedback-section"):
                    gr.Markdown("**How was your experience?**")
                    rating_input = gr.Radio(
                        choices=[
                            ("1   Poor", 1),
                            ("2", 2),
                            ("3", 3),
                            ("4", 4),
                            ("5   Excellent", 5),
                        ],
                        show_label=False,
                        value=None,
                    )
                with gr.Column(elem_classes="feedback-section"):
                    gr.Markdown("**Were the AI insights useful?**")
                    ai_helpful_input = gr.Radio(
                        choices=[("Yes", "Yes"), ("No", "No")],
                        show_label=False,
                        value=None,
                    )
                with gr.Column(elem_classes="feedback-section"):
                    gr.Markdown("**Did the visualizations help you understand your data?**")
                    viz_useful_input = gr.Radio(
                        choices=[("Yes", "Yes"), ("No", "No")],
                        show_label=False,
                        value=None,
                    )
                with gr.Column(elem_classes="feedback-section"):
                    gr.Markdown("**Would you recommend this platform?**")
                    recommend_input = gr.Radio(
                        choices=[("Yes", "Yes"), ("No", "No")],
                        show_label=False,
                        value=None,
                    )
                with gr.Column(elem_classes="feedback-section feedback-section-last"):
                    gr.Markdown("**Anything you'd like us to improve?**")
                    suggestions_input = gr.Textbox(
                        show_label=False,
                        placeholder="Optional   share your thoughts...",
                        lines=3,
                    )
                submit_feedback_button = gr.Button(
                    "Submit feedback", variant="primary", elem_classes="cta-button", size="lg"
                )
                feedback_status_output = gr.Markdown("")

        # ============================ TAB 7: ABOUT ============================
        with gr.Tab("   About"):
            initial_stats, initial_latest_entries = get_feedback_stats()
            gr.Markdown(format_about_intro_markdown())
            gr.Markdown("###   Community Feedback Summary")
            about_output = gr.HTML(format_about_kpi_cards(initial_stats))
            gr.Markdown("###   Latest 5 Feedback Entries")
            latest_entries_output = gr.Dataframe(
                value=initial_latest_entries,
                label="Recent Feedback",
                wrap=True,
            )
            refresh_about_button = gr.Button("  Refresh Stats")

    # Event Bindings
    load_button.click(
        fn=handle_file_upload,
        inputs=[file_input],
        outputs=[
            status_box, dataset_state, dashboard_output, preview_output,
            metadata_top_output, metric_selector_dropdown, bi_kpis_output, metadata_bottom_output,
            chart_type_dropdown, feature1_dropdown, feature2_dropdown, viz_plot_output, viz_status_output,
            upload_history_output, chatbot_display, chat_history_state,
            missing_summary_output, outlier_column_dropdown, cleaned_dataset_state,
            cleaning_summary_output, cleaned_preview_output, export_file_output,
            viz_availability_warning, suggestion_chips_row,
            visual_summary_column_dropdown, visual_summary_output, cleaning_plan_output,
            pivot_rows_dropdown, pivot_columns_dropdown, pivot_values_dropdown,
            pivot_filter_column_dropdown, pivot_filter_value_dropdown,
            pivot_table_output, pivot_status_output,
            missing_stats_output, missing_search_box, export_success_banner,
        ],
    )

    metric_selector_dropdown.change(
        fn=handle_metric_change,
        inputs=[metric_selector_dropdown, dataset_state],
        outputs=[bi_kpis_output],
    )

    visual_summary_column_dropdown.change(
        fn=handle_visual_summary_change,
        inputs=[visual_summary_column_dropdown, dataset_state],
        outputs=[visual_summary_output],
    )

    chart_type_dropdown.change(
        fn=handle_chart_type_change,
        inputs=[chart_type_dropdown, dataset_state],
        outputs=[feature1_dropdown, feature2_dropdown, viz_availability_warning],
    )

    generate_viz_button.click(
        fn=generate_visualization,
        inputs=[dataset_state, chart_type_dropdown, feature1_dropdown, feature2_dropdown],
        outputs=[viz_plot_output, viz_status_output],
    )

    pivot_filter_column_dropdown.change(
        fn=handle_pivot_filter_column_change,
        inputs=[dataset_state, pivot_filter_column_dropdown],
        outputs=[pivot_filter_value_dropdown],
    )

    generate_pivot_button.click(
        fn=handle_generate_pivot,
        inputs=[
            dataset_state, pivot_rows_dropdown, pivot_columns_dropdown, pivot_values_dropdown,
            pivot_aggregation_dropdown, pivot_filter_column_dropdown, pivot_filter_value_dropdown,
        ],
        outputs=[pivot_table_output, pivot_status_output],
    )

    submit_feedback_button.click(
        fn=handle_feedback_submit,
        inputs=[rating_input, ai_helpful_input, viz_useful_input, recommend_input, suggestions_input],
        outputs=[
            feedback_status_output, about_output, latest_entries_output,
            rating_input, ai_helpful_input, viz_useful_input, recommend_input, suggestions_input,
        ],
    )

    refresh_about_button.click(
        fn=handle_about_refresh,
        inputs=[],
        outputs=[about_output, latest_entries_output],
    )

    chat_send_button.click(
        fn=handle_chat_message,
        inputs=[chat_input, chat_history_state, dataset_state],
        outputs=[chatbot_display, chat_history_state, chat_input, suggestion_chips_row],
    )

    chat_input.submit(
        fn=handle_chat_message,
        inputs=[chat_input, chat_history_state, dataset_state],
        outputs=[chatbot_display, chat_history_state, chat_input, suggestion_chips_row],
    )

    chat_clear_button.click(
        fn=handle_chat_clear,
        inputs=[],
        outputs=[chatbot_display, chat_history_state, chat_input, suggestion_chips_row],
    )

    _CHIP_PROMPTS = {
        chip_summarize: "Summarize this dataset",
        chip_missing: "Which columns have missing values?",
        chip_outliers: "Does the dataset contain outliers?",
        chip_correlation: "Show correlation",
        chip_cleaning: "Recommend preprocessing steps",
        chip_target: "What is the best target column?",
    }

    for chip_button, preset_prompt in _CHIP_PROMPTS.items():
        chip_button.click(
            fn=functools.partial(handle_chat_message, preset_prompt),
            inputs=[chat_history_state, dataset_state],
            outputs=[chatbot_display, chat_history_state, chat_input, suggestion_chips_row],
        )

    detect_outliers_button.click(
        fn=handle_detect_outliers,
        inputs=[dataset_state, outlier_column_dropdown],
        outputs=[outlier_status_output],
    )

    apply_cleaning_button.click(
        fn=handle_apply_cleaning,
        inputs=[
            dataset_state, missing_strategy_dropdown,
            outlier_strategy_radio, outlier_column_dropdown,
        ],
        outputs=[
            cleaned_dataset_state, cleaning_summary_output, cleaned_preview_output, missing_summary_output,
            missing_stats_output, export_success_banner, export_file_output,
        ],
    )

    export_csv_button.click(
        fn=handle_export_csv,
        inputs=[cleaned_dataset_state],
        outputs=[export_success_banner, export_file_output],
    )

    export_excel_button.click(
        fn=handle_export_excel,
        inputs=[cleaned_dataset_state],
        outputs=[export_success_banner, export_file_output],
    )

    missing_search_box.change(
        fn=handle_missing_search,
        inputs=[dataset_state, missing_search_box],
        outputs=[missing_summary_output],
    )

    _cleaning_plan_inputs = [
        dataset_state, missing_strategy_dropdown,
        outlier_strategy_radio, outlier_column_dropdown,
    ]

    missing_strategy_dropdown.change(
        fn=handle_cleaning_plan_preview, inputs=_cleaning_plan_inputs, outputs=[cleaning_plan_output],
    )

    outlier_column_dropdown.change(
        fn=handle_cleaning_plan_preview, inputs=_cleaning_plan_inputs, outputs=[cleaning_plan_output],
    )

    outlier_strategy_radio.change(
        fn=handle_cleaning_plan_preview, inputs=_cleaning_plan_inputs, outputs=[cleaning_plan_output],
    )

    theme_toggle_button.click(fn=None, js=THEME_TOGGLE_JS)

# ----------------------------------------------------------------------
# LAUNCH
# ----------------------------------------------------------------------
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860))
    )