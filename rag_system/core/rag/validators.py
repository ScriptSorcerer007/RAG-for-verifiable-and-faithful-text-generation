import os
import re

ALLOWED_EXTENSIONS = [".pdf", ".txt", ".docx"]

def validate_query(query):
    if not query.strip():
        return False, "Empty query"

    if len(query) > 1000:
        return False, "Query too long"

    if re.search(r"<script>|</script>", query.lower()):
        return False, "Unsafe input"

    return True, "OK"


def validate_file(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, "Unsupported file type"

    if file.size > 5 * 1024 * 1024:
        return False, "File too large (max 5MB)"

    return True, "OK"