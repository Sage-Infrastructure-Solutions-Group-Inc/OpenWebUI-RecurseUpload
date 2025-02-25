# Open-WebUI Recurse Upload
This program is a very basic utility that will recurse a provided directory 
and upload all the files contained within provided the match the configured
inclusion filter.

## What is Sage Infrastructure Solutions Group Inc.
Sage Infrastructure Solutions Group Inc. (Sage ISG) is a niche cybersecurity firm 
located in Calgary, Alberta Canada. We provide various cybersecurity services and solutions
to our customers, for more information please [take a look at our website](https://sageisg.com).

This tool was created as part of an internal initiative, whose goal is to ensure the secure and ethical implementation of AI across our operations. It prioritizes maintaining the privacy of our customers at all times.
## Why?
Our team needed a quick tool that could upload a very large number (~2000) of files to a knowledge base reliably.
## Setup
The setup here is the same as any other `python` project:
```bash
# The following assumes you have installed Python3 and Python3-venv for your OS
git clone https://github.com/Sage-Infrastructure-Solutions-Group-Inc/OpenWebUI-RecurseUpload.git
cd OpenWebUI-RecurseUpload
python3 -m venv .
# Activate the VENV 
## Windows
.venv\scripts\activate.bat
## Unix
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 recuse-upload.py -h
```

## Help Text
```text
usage: recurse-upload.py [-h] [-t THREADS] [-f FILETYPES] [-r RETRIES] target_dir knowledge_base auth_token base_url

positional arguments:
  target_dir            The target directory to upload
  knowledge_base        The knowledge base to upload to
  auth_token            The auth token to use for the upload
  base_url              The base URL to use for upload. (http(s)://hostname(:port)

options:
  -h, --help            show this help message and exit
  -t THREADS, --threads THREADS
                        The number of threads to use.
  -f FILETYPES, --filetypes FILETYPES
                        The regular expression to use to determine the value of file types
  -r RETRIES, --retries RETRIES
                        The number of retries when a failure occurs.

```