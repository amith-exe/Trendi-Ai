<h1 align="center">TrendiAI: Cross-Platform AI Research Trend Tracker</h1>

<p align="center">
  A powerful research trend discovery tool that fetches and clusters AI topics from <strong>arXiv, GitHub, Reddit</strong>, and <strong>Exa</strong>. Built using Python, NLP, and Streamlit.
</p>

<hr>

<h2>Features</h2>

<ul>
  <li>Unified search across 4 AI research platforms</li>
  <li> KMeans clustering to group topics</li>
  <li> Keyword extraction using KeyBERT</li>
  <li>Ranking based on source priority, relevance, and recency</li>
  <li>Google-style UI built with Streamlit</li>
  <li> Secure API key management using <code>.env</code></li>
</ul>

<hr>

<h2> Technologies Used</h2>

<ul>
  <li><strong>Python 3.10+</strong></li>
  <li><strong>Streamlit</strong></li>
  <li><strong>scikit-learn</strong> (TF-IDF, KMeans)</li>
  <li><strong>KeyBERT</strong> for keyword extraction</li>
  <li><strong>PRAW</strong> (Reddit API), <strong>requests</strong>, <strong>dotenv</strong></li>
</ul>

<hr>

<h2> How It Works</h2>

<ol>
  <li>User enters a research query.</li>
  <li>API calls made to <strong>arXiv, GitHub, Reddit, Exa</strong>.</li>
  <li>Fetched text is cleaned and vectorized using TF-IDF.</li>
  <li><strong>KMeans</strong> clustering groups similar content.</li>
  <li><strong>KeyBERT</strong> extracts keywords to name clusters.</li>
  <li>Results ranked by source, relevance, and recency.</li>
  <li>Top 5 clusters with 10 trends each are displayed in Streamlit UI.</li>
</ol>

<hr>

<h2> Local Setup</h2>

<h4>Clone the repo</h4>

```bash
git clone https://github.com/amith-exe/Trendi-Ai.git
cd Trendi-Ai
