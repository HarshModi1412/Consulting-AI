import streamlit as st
import pandas as pd
import json
import plotly.express as px
import chardet
from io import BytesIO
import requests

# --- Your Gemini API Key ---
GEMINI_API_KEY = "AIzaSyD9DfnqPz7vMgh5aUHaMAVjeJbg20VZMvU"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


# --- Load CSV or Excel Smartly ---
def load_data_smart(file):
    file_name = file.name.lower()
    try:
        raw = file.read()
        if file_name.endswith(".csv"):
            detected = chardet.detect(raw)
            encoding = detected["encoding"] or "ISO-8859-1"
            return pd.read_csv(BytesIO(raw), encoding=encoding)
        elif file_name.endswith(".xlsx"):
            return pd.read_excel(BytesIO(raw), engine="openpyxl")
        else:
            st.error("Unsupported file format. Upload a CSV or Excel (.xlsx) file.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()


# --- Call Gemini REST API ---
def ask_llm(prompt):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GEMINI_API_KEY
    }
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()

        # DEBUG: show raw output
        st.code(json.dumps(result, indent=2), language="json")

        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Gemini Error: {e}"

# --- Chart Generator using Gemini ---
# --- Chart Generator using Gemini ---
def get_chart_recommendations(df):
    preview = df.head(10).to_string(index=False)
    prompt = f"""
You are a data visualization expert.

Given the following table:
{preview}

Suggest 2–3 useful charts. For each chart, include:
1. Chart Type (bar, line, pie, scatter, etc.)
2. X-axis and Y-axis columns
3. A short Chart Title
4. One-sentence business insight about why this chart is useful.

Format your answer as a JSON list like this:
[
  {{
    "chart_type": "bar",
    "x": "Category",
    "y": "Profit",
    "title": "Profit by Category",
    "insight": "Helps identify most profitable segments"
  }}
]
"""
    raw_response = ask_llm(prompt)

    # ✅ Clean Markdown formatting if present
    if "```json" in raw_response:
        raw_response = raw_response.split("```json")[-1]
    if "```" in raw_response:
        raw_response = raw_response.split("```")[0]

    try:
        return json.loads(raw_response)
    except Exception as e:
        st.warning(f"⚠️ JSON parse failed: {e}")
        return []

# --- Generate Plotly Chart ---
def generate_chart(df, spec):
    try:
        chart_type = spec["chart_type"].lower()
        x = spec["x"]
        y = spec["y"]
        title = spec.get("title", "Chart")
        if chart_type == "bar":
            return px.bar(df, x=x, y=y, title=title)
        elif chart_type == "line":
            return px.line(df, x=x, y=y, title=title)
        elif chart_type == "scatter":
            return px.scatter(df, x=x, y=y, title=title)
        elif chart_type == "pie":
            return px.pie(df, names=x, values=y, title=title)
    except:
        return None


# --- Insight Generator ---
def get_insights(df):
    preview = df.head(15).to_string(index=False)
    prompt = f"""
You are a Mckinsey level business strategy consultant.

Based on the dataset below, return 3–5 actionable business insights. Each insight should include:
- Decision
- What you observed
- Why it matters
- What action the business should take
- Possible Impact after implementation in terms of numbers 

above all should be very crips and to the point avoid long sentences

Data sample:
{preview}

Respond in numbered bullet points.
"""
    return ask_llm(prompt)


# --- Streamlit UI ---
st.set_page_config(page_title="🧠 AI Data Analyst (Gemini)", layout="wide")
st.title("🤖 Gemini-Powered Data Analyst (via REST API)")

uploaded_file = st.file_uploader("📁 Upload CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    df = load_data_smart(uploaded_file)

    if not df.empty:
        st.subheader("📊 Data Preview")
        st.dataframe(df.head(20))

        st.subheader("🔍 AI-Generated Insights")
        with st.spinner("Analyzing..."):
            insights = get_insights(df)
        st.markdown(insights)

        st.subheader("📈 Smart Chart Recommendations")
        with st.spinner("Generating charts..."):
            recs = get_chart_recommendations(df)

        for rec in recs:
            st.markdown(f"**{rec.get('title', '')}**")
            st.caption(f"_Why: {rec.get('insight', '')}_")
            fig = generate_chart(df, rec)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
