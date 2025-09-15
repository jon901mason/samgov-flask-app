from flask import Flask, Response
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)

@app.route('/')
def check_opportunities():
    api_key = os.environ.get('SAM_GOV_API_KEY')
    if not api_key:
        return Response("<p><strong>Error:</strong> SAM.gov API key not configured.</p>", mimetype='text/html')

    posted_from = (datetime.utcnow() - timedelta(days=30)).strftime("%m/%d/%Y")
    posted_to = datetime.utcnow().strftime("%m/%d/%Y")

    url = "https://api.sam.gov/opportunities/v2/search"  
    limit = 100
    max_pages = 5  # 5 pages × 100 results = 500 max

    target_naics = {
        "541613", "541870", "518210", "541810", "541890",
        "541430", "541820", "541511", "541830"
    }

    html = "<h3>Filtered opportunities from SAM.gov (past 30 days):</h3><ul>"
    found_match = False

    try:
        for page in range(max_pages):
            start = page * limit
            params = {
                "api_key": api_key,
                "postedFrom": posted_from,
                "postedTo": posted_to,
                "start": start,
                "limit": limit
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            opportunities = data.get("opportunitiesData", [])

            if not opportunities:
                break  # No more data

            for opp in opportunities:
                opp_naics = opp.get("naicsCodes", [])
                if not set(opp_naics) & target_naics:
                    continue

                found_match = True
                title = opp.get("title", "No title")
                link = opp.get("uiLink", "#")
                naics_str = ", ".join(opp_naics)
                html += f'<li><a href="{link}" target="_blank">{title}</a><br><strong>NAICS:</strong> {naics_str}</li><br>'

        html += "</ul>"

        if not found_match:
            return Response("<p>No matching NAICS codes found. 541613–541870–518210–541810–541890–541430–541820–541511–541830</p>", mimetype='text/html')

        return Response(html, mimetype='text/html')

    except requests.exceptions.RequestException as e:
        return Response(f"<p><strong>API request failed:</strong> {str(e)}</p>", mimetype='text/html')


@app.route('/health')
def health():
    return 'OK', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
