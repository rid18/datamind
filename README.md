---
title: DataMind
emoji: 📊
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.29.0
app_file: app.py
pinned: false
license: mit
---

# DataMind

**DataMind** is an AI-assisted data analyst workspace built with [Gradio](https://www.gradio.app/). Upload a CSV or Excel file and explore, clean, visualize, and chat with your dataset — all from one dashboard, with zero code required. Developed and maintained by **Ridham Bansal**.

> Upload a dataset — get instant statistics, an AI-readiness read, a guided cleaning workflow, a chart/pivot-table builder, and a rule-based (optionally OpenAI-assisted) chat assistant that answers questions about your data.

## Features

### Dashboard
- KPI cards: total rows, total columns, missing values, missing %, duplicate records, memory usage, numeric vs. categorical feature counts
- Instant dataset preview (first 10 rows)
- Upload history log — every dataset you've loaded, with row/column counts and timestamps

### Data Insights
- Full statistical summary (per-column type-aware stats)
- Business Intelligence KPI cards (average / total / max / min / median / std) for any numeric column you pick
- Automatic Visual Analytics — dataset-aware charts generated only when they make sense for your data
- **Quick Visual Summary**: pick any column and get a histogram + box plot (numeric) or a top-categories bar chart (categorical), plus a short **AI-generated insight** underneath — range, distribution shape, outlier bounds, and what they mean, regenerated live for whichever column you select
- Smart AI Insights: pattern-based observations computed directly from the data (correlation, skew, missingness, etc.)

### PreProcessing
A focused, two-tool cleaning workspace:
- **Missing Values** — compact stats (columns affected / missing cells / highest %), a searchable per-column table, and a cleaning strategy (drop rows, fill numeric with mean/median, fill categorical with mode)
- **Outlier Handling** — IQR-based detection (1.5 IQR rule) with a live preview, and a choice of **Remove Outliers** or **Replace with Maximum Value** (caps outliers to the largest valid value instead of dropping the row)
- Live "Planned Changes" preview before you commit anything
- Export the cleaned dataset as CSV or Excel — your original dataset elsewhere in the app is never modified

### AI Workspace (VizBot)
- A hybrid AI chat assistant: a fast, fully offline rule-based classifier handles common questions instantly; if it can't confidently classify a question **and** an OpenAI API key is configured, it falls back to OpenAI for routing — the answer itself always comes from your actual data, never a hallucinated one
- One-click suggestion chips (Summarize Dataset, Explain Missing Values, Find Outliers, Correlation Analysis, Cleaning Suggestions, Best Target Column)
- Every question type works fully offline — OpenAI is optional and only improves routing for ambiguous phrasing

### Visualization Studio
- Chart builder: Histogram, Bar Chart, Scatter Plot, Line Chart, Box Plot, Correlation Heatmap — with recommended/less-recommended column tagging (e.g. ID/date-like columns flagged for numeric axes)
- **Pivot Table Builder**: a full Excel-style pivot — Rows, Columns, Values, Aggregation (Sum/Count/Average/Min/Max/Median/Std Dev/Count Distinct), and an optional Filter — built dynamically from your selections, with high-cardinality columns flagged before you pick them for Columns

### Feedback & About
- Quick in-app feedback form (rating, AI helpfulness, visualization usefulness, recommendation)
- About tab shows aggregated community feedback stats

### Theme
- Light / Dark mode toggle, remembered for the session — both themes are independently designed (not a simple color inversion), covering cards, tables, buttons, inputs, navigation, and charts

## Tech Stack

| Layer | Tools |
|---|---|
| UI framework | [Gradio](https://www.gradio.app/) (Blocks API) |
| Data handling | pandas |
| Charts | Matplotlib, Seaborn |
| Excel I/O | openpyxl |
| AI chat routing | Rule-based classifier (offline) + optional OpenAI API |

## Project Structure