SKILLS = [
    "Python", "Java", "C++", "JavaScript", "TypeScript", "React", "Next.js",
    "Node.js", "FastAPI", "SQL", "PostgreSQL", "Machine Learning", "Pandas",
    "NumPy", "Docker", "AWS", "Git", "Linux",
]


def extract_skills(text: str | None) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    found: list[str] = []
    for skill in SKILLS:
        if skill.lower() in lower and skill not in found:
            found.append(skill)
    return found
