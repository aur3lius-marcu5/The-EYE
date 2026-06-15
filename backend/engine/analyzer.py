class RiskAnalyzer:
    def analyze(self, ports):
        score = 0

        if 22 in ports:
            score += 2
        if 3389 in ports:
            score += 3
        if len(ports) > 5:
            score += 2

        score = min(score, 10)

        return {
            "risk_score": score,
            "summary": f"{len(ports)} open ports detected"
        }
