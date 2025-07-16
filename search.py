# search.py (Updated with new importance weights)
import os
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime
from exa_py import Exa
from dotenv import load_dotenv
import praw

load_dotenv("api.env")

# Load API keys
Github_key = os.getenv("GITHUB_TOKEN")
EXA_key = os.getenv("EXA_API_KEY")
Reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
Reddit_secret = os.getenv("REDDIT_SECRET")
Reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

Arxiv_api_URL = "http://export.arxiv.org/api/query"

# Create data directory
Data_location = "data"
os.makedirs(Data_location, exist_ok=True)

def call_arxiv(query="cat:cs.LG", max_results=100):
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    try:
        response = requests.get(Arxiv_api_URL, params=params, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        return [{
            "title": entry.find("{http://www.w3.org/2005/Atom}title").text.strip(),
            "url": entry.find("{http://www.w3.org/2005/Atom}id").text,
            "published": entry.find("{http://www.w3.org/2005/Atom}published").text,
            "summary": entry.find("{http://www.w3.org/2005/Atom}summary").text.strip(),
            "source": "arxiv",
            "score_weight": 0.4  # Second most important (unchanged)
        } for entry in root.findall("{http://www.w3.org/2005/Atom}entry")]
    except Exception as e:
        print(f"⚠️ arXiv fetch failed: {str(e)}")
        return []

def call_github(keywords=["llm", "moe"]):
    headers = {
        "Authorization": f"Bearer {Github_key}",
        "Accept": "application/vnd.github.v3+json"
    }
    repos = []
    for keyword in keywords:
        try:
            response = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params={
                    "q": f"{keyword} in:name,description,topics",
                    "sort": "updated",
                    "per_page": 50
                },
                timeout=10
            )
            response.raise_for_status()
            repos.extend([{
                "title": item["name"],
                "url": item["html_url"],
                "description": item["description"],
                "stars": item["stargazers_count"],
                "updated_at": item["updated_at"],
                "source": "github",
                "score_weight": 0.6  # Third importance (was 0.2)
            } for item in response.json()["items"]])
        except Exception as e:
            print(f"⚠️ GitHub fetch failed for '{keyword}': {str(e)}")
    return repos

def calling_exa(query="emerging AI trends"):
    try:
        exa = Exa(EXA_key)
        response = exa.search_and_contents(
            query,
            use_autoprompt=True,
            num_results=25,
            include_domains=["arxiv.org", "github.com", "medium.com"]
        )
        return [{
            "title": result.title,
            "url": result.url,
            "text": result.text[:500] + "..." if result.text else "",
            "published_date": result.published_date,
            "source": "exa",
            "score_weight": 0.2  # Most important (was 0.6)
        } for result in response.results]
    except Exception as e:
        print(f"⚠️ Exa fetch failed: {str(e)}")
        return []

def calling_reddit(subreddits=["MachineLearning"]):
    try:
        reddit = praw.Reddit(
            client_id=Reddit_client_id,
            client_secret=Reddit_secret,
            user_agent=Reddit_user_agent
        )
        posts = []
        for sub in subreddits:
            for submission in reddit.subreddit(sub).hot(limit=25):
                posts.append({
                    "title": submission.title,
                    "url": f"https://reddit.com{submission.permalink}",
                    "upvotes": submission.score,
                    "comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "source": "reddit",
                    "score_weight": 0.8  # Least important (was 0.1)
                })
        return posts
    except Exception as e:
        print(f"⚠️ Reddit fetch failed: {str(e)}")
        return []

def saving_data(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"snapshot_{timestamp}.json"
    path = os.path.join(Data_location, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    # Keep only latest 4
    snapshots = sorted([f for f in os.listdir(Data_location) if f.startswith("snapshot_")])
    for old_file in snapshots[:-4]:
        os.remove(os.path.join(Data_location, old_file))
    return path


