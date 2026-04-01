import requests
from django.conf import settings


def expand_query(query: str):
    try:
        prompt = f"""
Generate 3 different rephrased versions of this query.
Keep them short and meaningful.

Query:
{query}

Return each query on a new line.
"""

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        response = requests.post(url, json=payload)

        if response.status_code != 200:
            return []

        result = response.json()
        text = result["candidates"][0]["content"]["parts"][0]["text"]

        # split lines
        queries = text.split("\n")

        # clean queries
        cleaned = []
        for q in queries:
            q = q.strip().lstrip("-•123456789. ")
            if q:
                cleaned.append(q)

        return cleaned[:3]

    except Exception as e:
        print("Query Expansion Error:", e)
        return []