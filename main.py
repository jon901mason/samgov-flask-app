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

    url = "https://api.sam.gov/prod/opportunities/v1/search"
    params = {
        "api_key": api_key,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": 1000
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        opportunities = data.get("opportunitiesData", [])
        if not opportunities:
            return Response("<p>No new opportunities found.</p>", mimetype='text/html')

        html = "<h3>Today's filtered opportunities from SAM.gov:</h3><ul>"

        # Define allowed NAICS codes
        target_naics = {
            "541613", "541870", "518210", "541810", "541890",
            "541430", "541820", "541511", "541830"
        }

        for opp in opportunities:
            opp_naics = opp.get("naicsCodes", [])
            if not set(opp_naics) & target_naics:
                continue  # Skip if no matching NAICS codes

            title = opp.get("title", "No title")
            link = opp.get("uiLink", "#")
            naics_str = ", ".join(opp_naics)

            html += f'<li><a href="{link}" target="_blank">{title}</a><br><strong>NAICS:</strong> {naics_str}</li><br>'

        html += "</ul>"

        if html == "<h3>Today's filtered opportunities from SAM.gov:</h3><ul></ul>":
            return Response("<p>No matching NAICS codes found. 541613-541870-518210-541810-541890-541430-541820-541511-541830</p>", mimetype='text/html')

        return Response(html, mimetype='text/html')

    except requests.exceptions.RequestException as e:
        error_html = f"<p><strong>API request failed:</strong> {str(e)}</p>"
        return Response(error_html, mimetype='text/html')

# Add this health check route for uptime monitors
@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
