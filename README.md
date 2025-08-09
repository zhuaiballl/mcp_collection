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
Each entry typically includes:

- `name` – Name of the client/server  
- `description` – Brief description  
- `github_url` – GitHub repository URL  
- `categories` – Classification categories  
- `author` – Creator or maintainer  
- `tags` – Relevant tags  
- `stars` – GitHub stars count  

---

### 2. Scripts

#### **Clone Repositories**

`clone_repos_from_json.py` – Clones GitHub repositories from JSON metadata.

```bash
python scripts/clone_repos_from_json.py <input_json_file> <output_directory>
```

Process:

1. Read GitHub URLs from the JSON file  
2. Validate and normalize URLs  
3. Clone repositories to the output directory  
4. Append counters to duplicate names  
5. Log failed clones to `clone_failed.txt`  

---

#### **Merge JSON Files**

`merge_json.py` – Merges two JSON metadata files (paths currently hard-coded).

```bash
python scripts/merge_json.py
```

---

#### **Other Utilities**

- `normalize_github_urls.py` – Standardizes GitHub URLs  
- `remove_duplicates.py` – Removes duplicate entries  
- `update_categories_from_xlsx.py` – Updates categories from Excel  
- `convert_xlsx_to_json.py` – Converts Excel metadata to JSON  

---

## 🚀 Usage Example

Clone all repositories from a metadata JSON file:

```bash
python scripts/clone_repos_from_json.py metadata/clients/merged_clients.json cloned_repos
```

---

## 🤝 Contributing

Contributions are welcome!  
Feel free to submit PRs with:

- New metadata entries  
- Improved scripts  
- Documentation enhancements  

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
