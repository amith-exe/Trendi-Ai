import streamlit as st
from search import call_arxiv, call_github, calling_exa, calling_reddit
from analyze_trends import TrendAnalyzer
import pandas as pd
from datetime import datetime

# Custom Dark Mode CSS
def inject_css():
    st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
        }
        .stTextInput > div > div > input {
            background-color: #2b2b2b;
            color: #ffffff;
            padding: 12px;
            border-radius: 24px;
            border: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }
        .stButton > button {
            background-color: #444;
            color: #fff;
            border-radius: 20px;
            padding: 8px 16px;
            font-weight: 500;
            border: none;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255, 255, 255, 0.2);
        }
        .stExpander {
            background: #2a2a2a;
            color: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(255,255,255,0.1);
            margin-bottom: 16px;
            border: none;
        }
        .st-emotion-cache-10trblm {
            color: #ffffff !important;
        }
        .source-tag {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
        }
        @media (max-width: 768px) {
            .stTextInput>div>div>input {
                padding: 10px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# Inject dark mode styles
inject_css()

# Initialize analyzer
analyzer = TrendAnalyzer()

# Streamlit config
st.set_page_config(
    page_title="AI Trend Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state defaults
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'current_cluster' not in st.session_state:
    st.session_state.current_cluster = 0

def run_search(query):
    with st.spinner("Searching across platforms..."):
        results = []
        if st.session_state.arxiv_enabled:
            results.extend(call_arxiv(query))
        if st.session_state.github_enabled:
            results.extend(call_github([query]))
        if st.session_state.exa_enabled:
            results.extend(calling_exa(query))
        if st.session_state.reddit_enabled:
            results.extend(calling_reddit())

    with st.spinner("Analyzing trends..."):
        analyzed_data = analyzer.analyze(results)
        df = pd.DataFrame(analyzed_data)
        if 'cluster' in df.columns:
            top_clusters = df.groupby('cluster')['score'].mean().sort_values(ascending=False).head(5).index.tolist()
            analyzed_data = [item for item in analyzed_data if item['cluster'] in top_clusters]
        st.session_state.search_results = analyzed_data
        st.session_state.last_query = query
        st.session_state.current_cluster = 0

def get_cluster_name(cluster_data):
    keywords = []
    for item in cluster_data:
        keywords.extend(item.get('_keywords', []))
    if not keywords:
        return "Trending Topic"
    return " ".join(sorted(set(keywords), key=lambda x: -keywords.count(x))[:3]).title()

def show_home():
    st.title("AI Trend Finder 🔍")
    st.markdown("Discover the latest trends in AI research across multiple platforms")

    with st.form("main_search"):
        query = st.text_input(
            "Search for AI trends",
            placeholder="e.g. LLM advancements, Mixture of Experts",
            key="main_search_query"
        )
        cols = st.columns(4)
        with cols[0]:
            arxiv = st.checkbox("arXiv", True, key="arxiv_home")
        with cols[1]:
            github = st.checkbox("GitHub", True, key="github_home")
        with cols[2]:
            exa = st.checkbox("Exa", True, key="exa_home")
        with cols[3]:
            reddit = st.checkbox("Reddit", True, key="reddit_home")

        if st.form_submit_button("Search"):
            st.session_state.arxiv_enabled = arxiv
            st.session_state.github_enabled = github
            st.session_state.exa_enabled = exa
            st.session_state.reddit_enabled = reddit
            st.session_state.page = "results"
            run_search(query)
            st.rerun()

def show_results():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("Search Results")
    with col2:
        if st.button("🏠 Back to Home"):
            st.session_state.page = "home"
            st.rerun()

    with st.form("results_search"):
        query = st.text_input(
            "Search again",
            value=st.session_state.get('last_query', ''),
            key="results_search_query"
        )
        if st.form_submit_button("🔍 New Search"):
            run_search(query)
            st.rerun()

    if not st.session_state.search_results:
        st.warning("No results found. Try a different search query.")
        return

    df = pd.DataFrame(st.session_state.search_results)
    if 'cluster' not in df.columns:
        st.error("Clustering failed - showing all results together")
        current_cluster = -1
        cluster_data = st.session_state.search_results
    else:
        clusters = sorted(df['cluster'].unique())
        current_cluster = clusters[st.session_state.current_cluster % len(clusters)]
        cluster_data = [item for item in st.session_state.search_results if item['cluster'] == current_cluster]

    st.subheader(f"📌 {get_cluster_name(cluster_data)}")

    source_colors = {
        "arxiv": "#b31b1b",
        "github": "#24292e",
        "exa": "#6e40c9",
        "reddit": "#ff4500"
    }

    for item in sorted(cluster_data, key=lambda x: -x['score']):
        with st.expander(f"{item['title']} (Score: {item['score']:.1f})"):
            st.markdown(
                f"<span class='source-tag' style='background:{source_colors.get(item['source'].lower(), '#777')};color:white'>"
                f"{item['source'].upper()}</span>",
                unsafe_allow_html=True
            )
            st.markdown(f"**Published**: {item.get('published', item.get('updated_at', 'N/A'))}")
            if 'summary' in item:
                st.write(item['summary'])
            elif 'description' in item:
                st.write(item['description'])
            elif 'text' in item:
                st.write(item['text'])
            st.markdown(f"[🔗 Open Link]({item['url']})", unsafe_allow_html=True)

    if 'cluster' in df.columns:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous Cluster"):
                st.session_state.current_cluster -= 1
                st.rerun()
        with col3:
            if st.button("Next Cluster ➡️"):
                st.session_state.current_cluster += 1
                st.rerun()
        with col2:
            st.write(f"Cluster {st.session_state.current_cluster + 1} of {len(df['cluster'].unique())}")

# Page routing
if 'page' not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    show_home()
else:
    show_results()



