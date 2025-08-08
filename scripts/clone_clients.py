import subprocess
import pandas as pd
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time

# if you have formatted urls
# Github repo urls here
# make sure the url's format like 'https://github.com/user/repo'
# urls = [line.strip() for line in open("github_urls.txt", encoding="utf-8") if line.strip()]

# if you don't have formatted urls, use the following function to get the urls from excel files
def load_urls_from_excel():
    """read github urls from excel files"""
    xlsx_dir = Path("../metadata/clients/xlsx")
    all_urls = set()
    non_github_urls = set()
    extracted_github_urls = set()
    failed_extractions = set()
    
    for excel_file in xlsx_dir.glob("*.xlsx"):
        try:
            df = pd.read_excel(excel_file)
            if 'github_url-href' in df.columns:
                github_urls = df['github_url-href'].dropna().tolist()
                
                for url in github_urls:
                    if pd.isna(url) or url == '':
                        continue
                    
                    url = str(url).strip()
                    
                    if 'github.com' in url.lower():
                        # format github url
                        processed_url = process_github_url(url)
                        if processed_url:
                            # all convert to lower case
                            all_urls.add(processed_url.lower())
                    else:
                        # try to extract github url from non-github website
                        github_links = extract_github_from_website(url)
                        
                        if github_links:
                            # found github url, add to main set
                            for github_link in github_links:
                                all_urls.add(github_link.lower())
                                extracted_github_urls.add(github_link.lower())
                            print(f"✅ successfully extracted {len(github_links)} github urls from {url}")
                        else:
                            # no github url found, record as non-github url
                            non_github_urls.add(url)
                            failed_extractions.add(url)
                        
                        # add delay to avoid too frequent requests
                        time.sleep(1)
                        
        except Exception as e:
            print(f"Error reading {excel_file}: {e}")
    
    # print extracted github urls summary
    if extracted_github_urls:
        print(f"✅ successfully extracted {len(extracted_github_urls)} github urls from non-github websites")
    
    # save non-github urls
    if non_github_urls:
        with open("non_github_urls.txt", "w", encoding="utf-8") as f:
            f.write(f"Non-GitHub URLs (no GitHub links found): {len(non_github_urls)}\n")
            f.write("=" * 50 + "\n\n")
            for url in sorted(non_github_urls):
                f.write(f"URL: {url}\n")
                f.write("-" * 30 + "\n")
        print(f"⚠️ still {len(non_github_urls)} urls cannot be extracted from non-github websites, saved to non_github_urls.txt")
    
    return list(all_urls)

def process_github_url(url):
    """process github url, and extract standard format: https://github.com/user/repo"""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if url.startswith('//github.com'):
        url = 'https:' + url
    elif url.startswith('github.com'):
        url = 'https://' + url
    
    # convert to lower case for processing
    url_lower = url.lower()
    
    # remove extra parts (like /tree/main, /blob/master, /issues, /wiki, etc.)
    # match 'https://github.com/user/repo' format
    pattern = r'https?://github\.com/([^/\s?#]+)/([^/\s?#\.]+)'
    match = re.search(pattern, url_lower)
    
    if match:
        user = match.group(1).strip()
        repo = match.group(2).strip()
        
        # remove common git-related suffixes that might be incorrectly included
        git_suffixes = ['.git', '.gitcd', '.github', '.gitignore', '.gitmodules']
        for suffix in git_suffixes:
            if repo.endswith(suffix):
                repo = repo[:-len(suffix)]
        
        # validate user and repo names
        # GitHub usernames and repo names can contain alphanumeric characters, hyphens, and underscores
        user_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-_]*[a-zA-Z0-9])?$'
        repo_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-_\.]*[a-zA-Z0-9])?$'
        
        if (user and repo and 
            re.match(user_pattern, user) and re.match(repo_pattern, repo) and 
            len(user) <= 39 and len(repo) <= 100):  # GitHub limits
            return f"https://github.com/{user}/{repo}"
    
    return None

def load_urls_from_txt():
    """read urls from txt file"""
    try:
        with open("github_urls.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def extract_github_from_website(url, timeout=10):
    """extract github urls from website"""
    github_links = set()
    
    try:
        print(f"🔍 analyzing website: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # find all links containing github.com
        # 1. find github urls from href attribute
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'github.com' in href.lower():
                processed_url = process_github_url(href)
                if processed_url:
                    github_links.add(processed_url.lower())
        
        # 2. find github urls from text content
        text_content = soup.get_text()
        github_pattern = r'https?://github\.com/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_\.]+(?:/[^\s<>"\']*)?'
        matches = re.findall(github_pattern, text_content, re.IGNORECASE)
        
        for match in matches:
            processed_url = process_github_url(match)
            if processed_url:
                github_links.add(processed_url.lower())
        
        # 3. find github urls from script tags and other attributes
        for script in soup.find_all(['script', 'meta', 'link']):
            for attr in ['src', 'content', 'href']:
                if script.get(attr) and 'github.com' in str(script.get(attr)).lower():
                    processed_url = process_github_url(str(script.get(attr)))
                    if processed_url:
                        github_links.add(processed_url.lower())
        
        if github_links:
            print(f"✅ found {len(github_links)} github urls from {url}")
            for link in github_links:
                print(f"   - {link}")
        else:
            print(f"❌ no github urls found from {url}")
            
        return list(github_links)
        
    except requests.exceptions.Timeout:
        print(f"⏰ timeout: {url}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ request failed: {url}: {e}")
        return []
    except Exception as e:
        print(f"❌ parse failed: {url}: {e}")
        return []

# get urls from excel files (already deduplicated)
urls_from_excel = load_urls_from_excel()
# urls_from_txt = load_urls_from_txt()
# all urls
urls = urls_from_excel

# Output directory here
output_dir = Path("clients")
output_dir.mkdir(exist_ok=True)

def clone_repo(url, idx):
    parts = url.rstrip("/").split("/")
    user, repo = parts[-2], parts[-1]
    folder_name = f"{user}_{repo}"
    dest = output_dir / folder_name

    if dest.exists():
        print(f"already exist: {dest}")
        return None

    print(f"\n [{idx+1}/{len(urls)}] cloning: {dest}")
    process = subprocess.Popen(
        ["git", "clone", "--depth", "1", url, str(dest)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        print(f"   [{folder_name}] {line.strip()}")
    retcode = process.wait()
    if retcode != 0:
        print(f"❌ clone failed: {dest}")
        return url
    else:
        print(f"✅ clone succeeded: {dest}")
        return None

if __name__ == "__main__":
    
    print(f"\n📊 GitHub repository statistics:")
    print(f"   - Total unique GitHub repositories after deduplication: {len(urls)}")
    print(f"\n🚀 Starting to clone {len(urls)} repositories...")
    
    failed_urls = []
    for idx, url in enumerate(urls):
        failed = clone_repo(url, idx)
        if failed:
            failed_urls.append(failed)

    if failed_urls:
        with open("clone_failed.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed_urls))
        print(f"\n⚠️ {len(failed_urls)} repos failed, see clone_failed.txt")
    else:
        print("\n🎉 all repos cloned successfully")
