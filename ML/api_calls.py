import os
from dotenv import load_dotenv
import praw
load_dotenv("api.env")

#load api from env file
Github_key = os.getenv("GITHUB_TOKEN")
EXA_key = os.getenv("EXA_API_KEY")
      # reddit keys
Reddit_client_id =os.getenv("REDDIT_CLIENT_ID")
Reddit_secret = os.getenv("REDDIT_SECRET")
Reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
      #Arxiv_URL
Arxiv_api_URL = "http://export.arxiv.org/api/query"
 # api key check if any key missing in env file
required_keys = ["GITHUB_TOKEN", "EXA_API_KEY", "REDDIT_CLIENT_ID", "REDDIT_SECRET", "REDDIT_USER_AGENT"]
"""missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    print(f"Missing keys in .env file: {', '.join(missing_keys)}")
else:
    print("key found")"""




import os               
import requests         
from datetime import datetime  
import xml.etree.ElementTree as ET  # For stringformating 
import json             
import praw             #  For Reddit api using 
from exa_py import Exa  
# import api keys
"""from load_API import (
    Github_key,
    EXA_key,
    Reddit_client_id,
    Reddit_secret,
    Reddit_user_agent,
    Arxiv_api_URL 

)"""
# making file location
Data_location = "data"
os.makedirs(Data_location, exist_ok=True)
# MAKING API CALL FOR ARXIV
def call_arxiv(query="cat:cs.LG", max_results=100):
        
    params = {
        "search_query": query,       
        "start": 0,                   
        "max_results": max_results,   
        "sortBy": "submittedDate",   
        "sortOrder": "descending"    
    }
    try:
        # Make API request
        response = requests.get(Arxiv_api_URL, params=params, timeout=10)
        response.raise_for_status()  
        
        # making tree using xml
        root = ET.fromstring(response.content)
        
        # Extract paper data from XML
        return [{
            "title": entry.find("{http://www.w3.org/2005/Atom}title").text.strip(),
            "url": entry.find("{http://www.w3.org/2005/Atom}id").text,
            "published": entry.find("{http://www.w3.org/2005/Atom}published").text,
            "summary": entry.find("{http://www.w3.org/2005/Atom}summary").text.strip(),
            "source": "arxiv",       # Source identifier
            "score_weight": 0.6      # Priority weight
        } for entry in root.findall("{http://www.w3.org/2005/Atom}entry")]
        
    except Exception as e:
        print(f"⚠️ arXiv fetch failed: {str(e)}")
        return []  
# MAKING API CALL FOR GIT HUB
def call_github(keywords=["llm", "moe"]):
    
    
    # Set up API headers 
    headers = {
        "Authorization": f"Bearer {Github_key}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    repos = []
    for keyword in keywords:
        try:
            # CALLING API
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
            
            # Procesing data
            repos.extend([{
                "title": item["name"],
                "url": item["html_url"],
                "description": item["description"],
                "stars": item["stargazers_count"],  
                "updated_at": item["updated_at"],   
                "source": "github",
                "score_weight": 0.3
            } for item in response.json()["items"]])
            
        except Exception as e:
            print(f"⚠️ GitHub fetch failed for '{keyword}': {str(e)}")
    
    return repos

# MAKING EXA API CALL 
def calling_exa(query="emerging AI trends"):
    try:
        # intialize
        exa = Exa(EXA_key)
        
        # Performing search
        response = exa.search_and_contents(
            query,
            use_autoprompt=True,      
            num_results=25,           
            include_domains=["arxiv.org", "github.com", "medium.com"]  # Trusted domains
        )
        
        # Formating data
        return [{
            "title": result.title,
            "url": result.url,
            "text": result.text[:500] + "..." if result.text else "",  # Preview text
            "published_date": result.publish_date,
            "source": "exa",
            "score_weight": 0.1
        } for result in response.results]
        
    except Exception as e:
        print(f"⚠️ Exa fetch failed: {str(e)}")
        return []
# MAKING REDDIT API CALL
def calling_reddit(subreddits=["MachineLearning"]):
        try:
            # Initializing api calls
            reddit=praw.Reddit(
            client_id=Reddit_client_id,
            client_secret=Reddit_secret,
            user_agent=Reddit_user_agent
        )
        
            posts = []
            for sub in subreddits:
            # extracting data 
                for submission in reddit.subreddit(sub).hot(limit=25):
                    posts.append({
                    "title": submission.title,
                    "url": f"https://reddit.com{submission.permalink}",
                    "upvotes": submission.score,       
                    "comments": submission.num_comments,  
                    "created_utc": submission.created_utc,  
                    "source": "reddit",
                    "score_weight": 0.05
                    })
            return posts
        
        except Exception as e:
                print(f"⚠️ Reddit fetch failed: {str(e)}")
                return []
# SAVING DATA FROM ALL API CALLS
def saving_data(data):

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"snapshot_{timestamp}.json"
    path = os.path.join(Data_location, filename)
    
    # Save data as JSON
    with open(path, "w") as f:
        json.dump(data, f, indent=2)  
    
    # Clean up old snapshots (keep last 4)
    snapshots = sorted([f for f in os.listdir(Data_location) if f.startswith("snapshot_")])
    for old_file in snapshots[:-4]:
        os.remove(os.path.join(Data_location,old_file))
    
    return path
# function calling
if __name__ == "__main__":
    print("🚀 Fetching AI trends from all sources...")
    
    # Fetch data from all sources
    data = []
    data.extend(call_arxiv())      # arXiv
    data.extend(call_github())     # GitHub
    data.extend(calling_exa())     # Exa
    data.extend(calling_reddit())  # Reddit
    
    # Save and report results
    saved_path = saving_data(data)
    print(f"✅ Successfully fetched {len(data)} items")
    print(f"📁 Data saved to: {saved_path}")
    
# Source breakdown
print("\nSource Breakdown:")
for source in ["arxiv", "github", "exa", "reddit"]:
    count = len([x for x in data if x["source"] == source])
    print(f"- {source.capitalize()}: {count} items")
