# MCP Collection

A research-purpose collection of **Model Context Protocol (MCP)** clients, servers, and related utilities.

---

## 📌 Project Overview

This project provides:

- **Metadata** for MCP clients and servers  
- **Utility scripts** for processing and managing MCP resources  
- **Tools** for cloning, merging, and analyzing MCP repositories  

---

## 📂 Project Structure

```
metadata/
  clients/               # Metadata for MCP clients
    glama_client.json
    mcp_so_client.json
    merged_clients.json
    ...
    xlsx/                # Excel files with client data

  servers/               # Metadata for MCP servers
    awesome.json
    glama.json
    merged_servers.json
    ...
    xlsx/                # Excel files with server data

scripts/
  clients/               # Scripts for client processing
    convert_glama_client.py
    convert_xlsx_to_json.py
    ...
  clone_repos_from_json.py   # Clone GitHub repos from JSON metadata
  merge_json.py              # Merge JSON metadata files
  normalize_github_urls.py   # Normalize GitHub URLs
  remove_duplicates.py       # Remove duplicate entries
  ...
```

---

## 🧩 Key Components

### 1. Metadata

Structured JSON information about MCP clients and servers.  
[Complete list of clients](./metadata/clients/merged_clients.json)
[Complete list of servers](./metadata/servers/merged_servers.json)

---

### 2. Scripts

#### Clone Repositories

`clone_repos_from_json.py` – Clones GitHub repositories from JSON metadata.

```bash
export GITHUB_TOKEN="YOUR_GITHUB_ACCESS_TOKEN" && python scripts/clone_repos_from_json.py <input_json_file> <output_directory>
```

Process:

1. Read GitHub URLs from the JSON file  
2. Validate and normalize URLs  
3. Clone repositories to the output directory  
4. Append counters to duplicate names  
5. Log failed clones to `clone_failed.txt`  

---

#### Merge JSON Files

`merge_json.py` – Merges two JSON metadata files (paths currently hard-coded).

```bash
python scripts/merge_json.py
```

---

#### Analyze Repos

`enhanced_repo_analysis.py` - Run some analysis on GitHub repos.

```bash
python scripts/enhanced_repo_analysis.py clone <json_file_path> <output_directory>
python scripts/enhanced_repo_analysis.py analyze --repo-dir ../mcp_servers --output-dir analysis
```

## 📜 License

This project is licensed under the [MIT License](LICENSE).
