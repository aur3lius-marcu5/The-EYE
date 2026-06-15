import requests

class CVEEngine:
    def fetch(self, service: str):
        try:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={service}"
            r = requests.get(url, timeout=5)
            data = r.json()

            return [
                v["cve"]["id"]
                for v in data.get("vulnerabilities", [])[:3]
            ]
        except:
            return []
