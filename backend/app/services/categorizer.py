CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "AI/ML": ["openai", "llm", "model", "anthropic", "machine learning", "gpt", "neural"],
    "Cybersecurity": ["breach", "vulnerability", "cve", "malware", "ransomware", "security"],
    "Startups": ["startup", "funding", "series a", "venture", "yc", "accelerator"],
    "Developer Tools": ["developer tool", "ide", "sdk", "api", "framework", "devtools"],
    "Cloud": ["aws", "azure", "gcp", "cloudflare", "kubernetes", "docker"],
    "Programming": ["python", "javascript", "rust", "golang", "programming"],
    "Data Science": ["data science", "pandas", "numpy", "analytics", "dataset"],
}


def categorize(title: str, summary: str | None = None) -> str:
    text = f"{title} {summary or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "Other"
