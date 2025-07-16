# analyze_trends.py (Updated for new weight system)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from keybert import KeyBERT
import numpy as np

class TrendAnalyzer:   
    def __init__(self):
        try:
            self.kw_model = KeyBERT()
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                min_df=2  # Ignore terms that appear in only 1 document
            )
            self.kmeans = KMeans(
                n_clusters=5,
                random_state=42,
                n_init=10  # Explicitly set to avoid future warnings
            )
        except Exception as e:
            print(f"⚠️ Analyzer initialization failed: {str(e)}")
            raise

    def analyze(self, data):
        if not data or len(data) == 0:
            print("⚠️ No data to analyze")
            return data

        try:
            # 1. Prepare text and extract keywords
            texts = []
            for item in data:
                try:
                    text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('description', '')}"
                    texts.append(text.strip())
                except Exception as e:
                    print(f"⚠️ Error processing item: {str(e)}")
                    continue

            if not texts:
                print("⚠️ No valid text content found")
                return data

            # 2. Extract keywords with fallback
            for i, text in enumerate(texts):
                try:
                    keywords = self.kw_model.extract_keywords(text, top_n=3)
                    data[i]['_keywords'] = [kw[0] for kw in keywords] if keywords else []
                except Exception as e:
                    print(f"⚠️ Keyword extraction failed for item {i}: {str(e)}")
                    data[i]['_keywords'] = []

            # 3. Cluster based on keywords with error handling
            try:
                tfidf = self.vectorizer.fit_transform(texts)
                if tfidf.shape[0] > 1:  # Need at least 2 samples for clustering
                    clusters = self.kmeans.fit_predict(tfidf)
                    for i, cluster in enumerate(clusters):
                        data[i]['cluster'] = int(cluster)
                else:
                    print("⚠️ Not enough samples for clustering")
                    for item in data:
                        item['cluster'] = -1
            except Exception as e:
                print(f"⚠️ Clustering failed: {str(e)}")
                for item in data:
                    item['cluster'] = -1

            # 4. Calculate scores with new weight system (lower weight = more important)
            max_weight = 0.8  # The highest weight in our system (Reddit)
            min_weight = 0.2  # The lowest weight (Exa)
            
            for item in data:
                try:
                    # Normalize components to 0-1 range
                    keyword_score = min(len(item.get('_keywords', [])) / 3, 1.0)
                    
                    # Convert weight to importance (0.2 → 1.0, 0.8 → 0.0)
                    source_importance = 1 - ((item['score_weight'] - min_weight) / (max_weight - min_weight))
                    
                    # Weighted combination (70% keywords, 30% source importance)
                    raw_score = 0.7 * keyword_score + 0.3 * source_importance
                    
                    # Scale to 0-100 and round
                    item['score'] = round(raw_score * 100, 1)
                    
                    # Add debug info (optional)
                    item['_score_components'] = {
                        'keywords': keyword_score,
                        'source_importance': source_importance
                    }
                except Exception as e:
                    print(f"⚠️ Scoring failed for item: {str(e)}")
                    item['score'] = 0.0

            return data
        except Exception as e:
            print(f"⚠️ Critical analysis error: {str(e)}")
            return data