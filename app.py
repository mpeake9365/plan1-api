#!/usr/bin/env python3
"""
Plan #1 Auto-Deploy Script
Run this once to update your Render server whenever Claude makes changes.
Usage: python3 deploy.py
"""
import os
import sys
import base64
import urllib.request
import urllib.error
import json

GITHUB_USER = "mpeake9365"
GITHUB_REPO = "plan1-api"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

FILES_TO_UPLOAD = [
    "app.py",
    "plan1_mark.html", 
    "plan1_bill.html",
    "requirements.txt",
    "render.yaml",
]

def github_api(method, path, data=None):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "Plan1-Deploy"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def upload_file(filename):
    # Read file content
    with open(filename, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    
    # Get current SHA (needed to update existing file)
    existing = github_api("GET", filename)
    sha = existing.get("sha")
    
    data = {
        "message": f"Update {filename}",
        "content": content,
    }
    if sha:
        data["sha"] = sha
    
    result = github_api("PUT", filename, data)
    if "content" in result:
        print(f"  ✓ {filename} uploaded")
        return True
    else:
        print(f"  ✗ {filename} failed: {result.get('message', result)}")
        return False

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("ERROR: Set your GitHub token first:")
        print("  export GITHUB_TOKEN=your_token_here")
        print("")
        print("Get a token at: https://github.com/settings/tokens/new")
        print("Select scope: repo (full control)")
        sys.exit(1)
    
    print(f"Deploying to {GITHUB_USER}/{GITHUB_REPO}...")
    print("")
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = 0
    for f in FILES_TO_UPLOAD:
        if os.path.exists(f):
            if upload_file(f):
                success += 1
        else:
            print(f"  - {f} not found, skipping")
    
    print("")
    print(f"Done! {success} files uploaded.")
    print("Render will auto-deploy in ~2 minutes.")
    print("Then refresh: https://plan1-api.onrender.com/mark")
