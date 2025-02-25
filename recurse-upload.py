import concurrent.futures
import logging
from argparse import ArgumentParser
from datetime import datetime
from os.path import isdir

import enlighten
import requests
import os
import re
import time


parser = ArgumentParser()
parser.add_argument('target_dir', help='The target directory to upload')
parser.add_argument("knowledge_base", help="The knowledge base to upload to")
parser.add_argument("auth_token", help="The auth token to use for the upload")
parser.add_argument("base_url", help="The base URL to use for upload. (http(s)://hostname(:port)")
parser.add_argument('-t', '--threads', help="The number of threads to use.", default=2, type=int)
parser.add_argument('-f', '--filetypes', help="The regular expression to use to determine the value of file types", default="(?:\.pdf|\.txt|\.doc|\.docx|\.md|.xlsx)$")
parser.add_argument('-r','--retries', help="The number of retries when a failure occurs.", default=3, type=int)

args = parser.parse_args()
LOG_FORMAT = '%(asctime)s [%(levelname)s]: %(message)s '
file_regex = re.compile(args.filetypes)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
successful_uploads = 0
successful_associations = 0
start = datetime.now()
progress_manager = enlighten.get_manager()


def list_directory_recursive(path):
    """
    Recursively lists all files and directories under the given path.
    Converts the user-provided path to an absolute path to handle
    both relative and absolute inputs.

    :param path: The directory path to list (can be relative or absolute).
    :return: A list of absolute paths to all items under 'path'.
    """
    # Convert the provided path to an absolute path
    path = os.path.abspath(path)
    items = []
    logging.debug(f"The path is: {path}")
    try:
        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            if not file_regex.search(entry_path) and not isdir(entry_path):
                logging.debug(f"Skipping file {entry_path} due to invalid file type.")
                continue
            # Append the current entry's absolute path (directory or file)
            items.append(entry_path)

            # If this entry is a directory, recurse into it
            if os.path.isdir(entry_path):
                items.extend(list_directory_recursive(entry_path))

    except NotADirectoryError:
        # If 'path' is actually a file, return it in a list
        return [path]
    except PermissionError:
        # Skip directories/files with permission issues
        pass

    return items

def upload_file(file_path: str, retries=0):
    logging.info(f"Attempting the upload of the file: {file_path}")
    url = f'{args.base_url}/api/v1/files/'
    headers = {
        'Authorization': f'Bearer {args.auth_token}',
        'Accept': 'application/json'
    }
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, headers=headers, files=files)
    if response.status_code >= 499 and retries < args.retries:
        logging.error(f"Failed to upload the file: {file_path} (Reattempt after {retries} seconds)")
        time.sleep(retries)
        return upload_file(file_path, retries=retries + 1)
    return response

def associate_file_with_kb(file_id: str, retries=0):
    logging.info(f"Associating file {file_id} with KB {args.knowledge_base}")
    url = f'{args.base_url}/api/v1/knowledge/{args.knowledge_base}/file/add'
    headers = {
        'Authorization': f'Bearer {args.auth_token}',
        'Content-Type': 'application/json'
    }
    data = {'file_id': file_id}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code >= 399 and retries < args.retries:
        if " Duplicate content detected" in response.text:
            return response
        logging.error(f"Failed to associate the file: {file_id} (Reattempt after {retries} seconds)")
        time.sleep(retries)
        return associate_file_with_kb(file_id, retries=retries + 1)
    return response

target_files = list_directory_recursive(args.target_dir)
logging.info(f"Found {len(target_files)} files that will be uploaded to the knowledge base {args.knowledge_base}")
association_progress_bar = progress_manager.counter(total=len(target_files), desc="File Upload Progress", unit='files')
association_futures = []
with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as association_executor:
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(upload_file, path): path for path in target_files}
        for future in concurrent.futures.as_completed(futures):
            task_id = futures[future]
            try:
                result = future.result()
                if result.status_code == 200 or result.status_code >= 400:
                    try:
                        successful_uploads += 1
                        file_id = result.json().get('id')
                        if file_id:
                            logging.info(
                                f"Finished uploading a file. File will now be associated with KB {args.knowledge_base}")
                            aresponse = associate_file_with_kb(file_id, retries=0)
                            association_progress_bar.update()
                            if aresponse.status_code == int(200):
                                successful_associations += 1
                                logging.info(f"Successfully associated file {file_id} to KB {args.knowledge_base}")
                            else:
                                logging.error(f"Association failed (status code: {aresponse.status_code}): {aresponse.text}")
                    except Exception as e:
                        logging.error(e)
            except Exception as exc:
                print(f"Task {task_id} generated an exception: {exc}")
logging.info(f"\nFinished uploading {successful_uploads} files.")
logging.info(f"Finished associating {successful_associations} files.")
logging.info(f"Upload process took: {datetime.now() - start}")