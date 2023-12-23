# MusicAgent User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the MusicAgent](#running-the-musicagent)
6. [Creating Your Song](#creating-your-song)
7. [Output](#output)

---

### Introduction

MusicAgent is a Python agent that programs songs in Sonic Pi. 
It uses AI to generate song structures based on user preferences.
This manual provides instructions on installation, configuration, and song generation.

### Prerequisites

- **Sonic Pi:** Must be installed on your system (needed to run the *.rb files): https://sonic-pi.net/
- **OPENAI_API_KEY:** Set as a system environment variable or in `ArtistConfig/mITyJohn/ArtistConfig.json`.
- **Python** Must be installed on your machine

### Installation

```bash
# Clone the repository
git clone [repository link]

# Install dependencies
pip install -r requirements.txt
```
### Configuration
Set **OPENAI_API_KEY** in `ArtistConfig/mITyJohn/ArtistConfig.json` if not set as a system variable.
Adjust settings in ArtistConfig.json as needed.

### Starting the MusicAgent
```bash
python run.py
```
Once launched you'll be able to pass multiple criteria:
- Choose an AI model when prompted: "gpt-3.5-turbo", "gpt-4", etc.
- Provide song details: name, duration, style
- Optionally add specific requests like chord progressions or musical influences.

### Output
- Track File Generated: the *.rb file can be found in the Songs directory.
- To play Your Song track: load this file in Sonic Pi.
