"""CodeRip

Usage:

    $ coderip.py path/to/source/dir "<executable filter>"

code input:
---
- primary: section marker comments + filewatcher
- secondary: copy + paste
- secondary: `coderip select myfile.py 10-20` # stores to disk

thread/process to watch filesystem, maintain list of start/stop tags with labels
---

thread/process to monitor application output in stdout/stderr
---
- automatically identify the relevant processes
- display the available outputs by process to the user
- let the user select which ones to include (if any)
- orr simply copy and paste the output if it's not available via stdout/stderr

main thread
---
- read section markers and process output
- displaying them to the user
- allowing the user to select them (optionally using labels) for insertion into a prompt
- allow user to specify custom instructions

prompting
---
- prompt model such that it only generates valid code
- demarcated by the relevant labels associated with each section of code

output parsing
---
- get map of label -> code section
- multiple labeled sections demarcated by:
    #|open<:label>
    ```
    ...
    ```
    #|close<:label>
- if not properly formatted, iterate through secondary prompt to extract/reformat

code insertion
---
- insert code sections into their respective locations
- sections of code they are intending to replace should be commented out
- add special comments that indicate:
  - date/time each section was commented out
  - section version number (monotonically increasing)
  - hash and/or id corresponding to the prompt which generated this
  - model identifier (e.g. gpt-4-1106-preview)
  - ultimately it should be configurable whether to store all data in the comments for
    maximum portability, or make minimal changes to source code (e.g. #<hash>)
    and store data in coderip.db (SQLite, optionally sync to S3/Postgres/Github)

LLM API
---
- OpenAI GPT-4 preview
- add Cohere.ai for when GPT-4 goes down.

prompts
---
- jinja2 templates e.g. "my-prompt.j2"
- can be dynamically generated via model completions
  - e.g. prompt = DynamicPrompt(input="...", desired_output="...", additional_context="i want this prompt to do x/y using a/b")
    saves to template automatically for re-use / determinis

message types / data model
--
- source code
- feedback signal
    - runtime
    - user_prompt
    - coderip_prompt
    - API documentation
- meta
    - extract commands -> run commands
    - extract code -> reformat code

Issue API
---
Hook into Github Issues to automatically ingest and fix

modes
---
- (primary) compose loop: write code
- (secondary) issue loop: groom backlog
- (secondary) pr loop: review and merge pull requests
- (secondary) meta loop: view stats/history, undo/redo

compose loop
---
TODO

TODO
---
- optionally disable writes (caution: removes history)
- follow links to documentation

ideas
---
- keep track of TODOs
"""

import argparse
import threading
from typing import Dict, List
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import re
import subprocess
import psutil
import openai
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

@dataclass(frozen=True)
class File:
    path: str
    name: str

@dataclass(frozen=True)
class CodeSection:
    start_line: int
    end_line: int
    label: str

TagData = Dict[File, List[CodeSection]]

class TagFinder(FileSystemEventHandler):
    def __init__(self, tag_data: TagData, data_lock: threading.Lock):
        logger.info(f"Initializing TagFinder {tag_data=} {data_lock=}")
        super().__init__()
        self.tag_data = tag_data
        self.data_lock = data_lock

    def on_modified(self, event):
        logger.info(f"File modified {event=}")
        if not event.is_directory:
            self.update_tags(event.src_path)

    def update_tags(self, file_path: str):
        logger.info(f"Updating tags {file_path=}")
        if not os.path.exists(file_path) or file_path.endswith('.lock') or '.git' in file_path:
            return

        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            logger.warning(f"Skipping non-text file: {file_path}")
            return

        sections = []
        start_line = None
        start_label = None

        for i, line in enumerate(lines):
            open_tag_match = re.match(r'#\|open(?:\:(\w+))?', line)
            close_tag_match = re.match(r'#\|close(?:\:(\w+))?', line)

            if open_tag_match:
                start_line = i + 1  # Line numbers are 1-indexed
                start_label = open_tag_match.group(1)
            elif close_tag_match and start_line is not None and start_label == close_tag_match.group(1):
                sections.append(CodeSection(start_line, i + 1, start_label or ''))
                start_line = None
                start_label = None

        with self.data_lock:
            self.tag_data[File(path=file_path, name=os.path.basename(file_path))] = sections
            logger.info(f"Updated tag_data {self.tag_data=}")

def watch_directory(path: str, tag_data: TagData, data_lock: threading.Lock):
    logger.info(f"Watching directory {path=}")
    event_handler = TagFinder(tag_data, data_lock)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def monitor_output(executable_name: str):
    logger.info(f"Monitoring output {executable_name=}")
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == executable_name:
            try:
                process = psutil.Process(proc.info['pid'])
                stdout, stderr = process.communicate()
                logger.info(f"Captured output {stdout=} {stderr=}")
                print(f"STDOUT:\n{stdout.decode('utf-8')}")
                print(f"STDERR:\n{stderr.decode('utf-8')}")
            except Exception as e:
                logger.error(f"Error monitoring process {e=}")


def get_model_response(prompt: str, model: str = "gpt-4-1106-preview") -> str:
    logger.info(f"Getting model response {prompt=} {model=}")

    # Create an instance of the OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_API_KEY"))

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        model_response = response.choices[0].message.content
        logger.info(f"Model response {model_response=}")
        return model_response
    except Exception as e:
        logger.error(f"Error in getting model response: {e}")
        return "Error: Could not get response from model."

    return model_response


def execute_command(command: str):
    logger.info(f"Executing command {command=}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    logger.info(f"Command output {stdout=} {stderr=}")
    return stdout, stderr

def user_interaction_interface(tag_data: TagData, data_lock: threading.Lock):
    logger.info("Starting user interaction interface")
    while True:
        with data_lock:
            for file, sections in tag_data.items():
                print(f"{file.name} ({file.path}):")
                for section in sections:
                    print(f"  - Lines {section.start_line}-{section.end_line}, Label: {section.label}")

        user_input = input("\nSelect a section by typing the file name and line range, or type 'exit': ")
        logger.info(f"User input {user_input=}")
        if user_input.lower() == 'exit':
            break

        prompt = f"Generate a command based on the following code section:\n{user_input}"
        model_suggested_command = get_model_response(prompt)
        print(f"\nModel suggests the command: {model_suggested_command}")
        confirm = input("Confirm command (yes/no), provide feedback, or type 'exit': ")

        if confirm.lower() == 'yes':
            stdout, stderr = execute_command(model_suggested_command)
            print(f"Command output:\n{stdout}")
            if stderr:
                print(f"Error:\n{stderr}")
        elif confirm.lower() == 'exit':
            break
        else:
            feedback = input("Please provide your feedback: ")
            new_prompt = f"{prompt}\nFeedback: {feedback}\nAdjusted command:"
            new_command = get_model_response(new_prompt)
            print(f"New command based on feedback: {new_command}")

def main():
    logger.info("Starting main")
    parser = argparse.ArgumentParser()
    parser.add_argument('source_dir', type=str, help='Path to the source directory')
    parser.add_argument('--exec', type=str, help='Executable name for output monitoring', default='')
    args = parser.parse_args()

    if not os.path.isdir(args.source_dir):
        raise ValueError(f"The provided path '{args.source_dir}' is not a directory.")

    tag_data: TagData = {}
    data_lock = threading.Lock()

    watcher_thread = threading.Thread(target=watch_directory, args=(args.source_dir, tag_data, data_lock))
    watcher_thread.start()

    if args.exec:
        monitor_thread = threading.Thread(target=monitor_output, args=(args.exec,))
        monitor_thread.start()

    user_interaction_interface(tag_data, data_lock)

if __name__ == "__main__":
    main()
