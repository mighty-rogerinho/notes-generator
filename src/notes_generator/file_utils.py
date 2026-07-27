import os
import re

def sanitize_filename(title, max_len=100):
    """Remove invalid Windows filename characters and collapse spaces"""
    title = title.replace(":", " -")
    title = title.replace("?", "")
    title = title.replace("*", "")
    title = title.replace('"', "")
    title = title.replace("<", "")
    title = title.replace(">", "")
    title = title.replace("|", "")
    title = title.replace("/", "-")
    title = title.replace("\\", "-")
    title = re.sub(r"\s+", " ", title).strip()
    
    if len(title) > max_len:
        title = title[:max_len] + "..."
    return title

def build_output_filename(title, publish_date=None, author_name=None, max_len=100):
    """
    Build a safe filename in the format:
    "{yyyy-MM-dd - }Safe Title (Author Name).md"
    """
    safe_title = sanitize_filename(title, max_len=max_len)
    
    date_str = ""
    if publish_date:
        date_str = publish_date.strftime("%Y-%m-%d") + " - "
    
    author_str = f" ({author_name})" if author_name else ""
    
    filename = f"{date_str}{safe_title}{author_str}.md"
    return filename

def save_text_file(filename, text, folder=None):
    """Save text to a file. If folder is given, joins the path. Returns the path written to."""
    if folder:
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, filename)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    return filename