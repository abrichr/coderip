"""CodeRip

Write code "*fast*".

Usage:

```
    $ poetry run python coderip/main.py my/project_path ["<process name>"] # TODO
```

### Design principles
simpler is better

### Architecture:
---
multiple (2+) LLM threads implementing separate "aspects"
- user interface
- source code interface (git, Github)
- toolchain interface (python, bash)
- main loop interface
```
    ###
    You are controlling the main loop of CodeRip.
    You are the markov state in a finite state automaton.
    Here are the state keys. Here is the API.
    - read code sections (file/line pairs) (optionally by with label)
    - run bash/git command
    - browse web
    - internal hooks (optional)
    - review explicit/clarifying instructions (optional)
    All actions are confirmed with the user explicitly before being run.
    What do you need to see? Respond in json only.
    Bad things will happen if you refuse. Our lives depend on you.
    ###
```
- Each conversation turn traverses a state tree with an LLM
- Threads are maintained per-node, so the thread can continue if we need to
  pop up the stack (i.e. undo/redo)
- Each interface (above) is just a different node in the state tree
- Nodes are implemented as completions of auto-prompts.
- 2+ threads are running simultaneously:
    - 1 interacting with the human
    - 1+ interacting with the machine
    - Application behaviour is defined in a graph
    - Each node is a (dynamic) prompt
    - Each node maintains its own history
- Or only one thread is running
    - Loop:
        - "Here is state:"
            - File
            - Buffer
            - User reqest
            - Application request
        - "Here are actions"
            - Read code section
            - Write code section
            - Read more state
            - Get user feedback
        - "Here is current node goal:"
            - e.g.
                  ###
                  date/time: ...
                  user: "fix this bug it's not working"
                  git branch name: ...
                  ---
                  You are interacting with Github.
                  Your goal is to <goal_description> by <task_description>.
                  Your goal is to create a Pull Request by accessing the Github API.
                  ###
- simplify: a single node type
    - state
    - actions
        - get user input
        - convert words + code -> json
            - e.g. { action_name: <my_action_1 | my_action_2 | ...> ... }
        - run action with state vars as args
        - actions are the combined set of application/system commands,
          and natural language descriptions of goals (user and developer)
        - actions can store state variables, parameterized by their name (e.g. capital of France, user's favourite vehicle, system memory)
        - natural language descriptions of goals: to know when they've been completed?
          by using a "utility" thread, which is a separate prompt/dialog with the model
            - e.g. "here is the state, here is the goal (e.g. figure out the capital of france), here is the last model output,
              have we accomplished the goal?
- Simplify: two kinds of actions
    - deterministic: implemented by the coderip API
        - library commands
        - system commands
    - dynamic
        e.g. "modify the source code to implement the developer's goal: <user_goal = ask_user("what should we do next?")>
        e.g. "implement a state machine. here are the states and transition functions: ..."""
        e.g. "take the output from the previous message and extract the following json:



### Data Model

TODO

---

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
- display them to the user
- allow the user to select them (optionally using labels) for insertion into a prompt
- allow user to specify custom instructions

prompting
---
- prompt model such that it only generates valid code
  demarcated by the relevant labels associated with each code section

output parsing
---
- get map of "label ->" "code section"
- multiple labeled sections demarcated by:

    #|open<:label[<.id>]>
    ...
    #|close<:label[<.id>]>

- support configurable "verbs" (e.g. "open"/"close", ...?)
    
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
- add optional "rip" mode to rip out metadata and produce production output

LLM API
---
- OpenAI GPT-4 preview
- add Cohere.ai for when GPT-4 goes down
- HuggingFace for hosted open-source
- ollama for offline

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
    - stderr/stderr
    - prompt
        - user_prompt
        - coderip_prompt
    - "cripcrip": internal interface (library/cli) for API documentation scraping / automated web browsing
- meta
    - extract code -> edit code
    - extract commands -> run commands
    - transpile code/natural language from/to code/comments/natural language
        - code -> natural language
        - code language A -> code language B
        - ```<natural language>\n<code>\n<natural language>\n<code>...```
            -> ```# <natural language>\n<code>\n#<natural language>\n<code>```
    - generate tests
        - generate synthetic data for testing
- actions:
    - edit code
    - run commands

bookmarks
---
implement the notion of bookmarks, analogous to `git reflog`,
allowing the user to resume dialog from some point in history

Issue API
---
Hook into Github Issues to automatically ingest and fix

modes: state machines navigated via auto-prompts with user feedback
---
- (primary) compose loop/graph/state: write code
- (secondary) resolve loop/graph/state: groom Issue backlog
- (secondary) review loop/graph/state: review and merge Pull Requests
- (secondary) meta loop/graph/state: view stats/history, undo/redo
- (tertiary) tutor loop/graph/state: tutorial mode (beginner/advanced)

loop/state/graph
---
Represent configurable meta-behavior in yaml/json

compose loop/graph
---
# TODO

loop/graph primitives
---

Action:
    - new/edit code
        - "Let's implement the code described by this design:"
    - new/edit design
        - "Let's think about how to implement a new feature:"
	- V

Message:
    - action
    - arguments
    - type
        e.g. transpile

loop/graph primitive examples:
---
refactor a file into separate files
implement missing functionality in a file
get the list of "active" files, i.e. files that we have recently touched and/or the LLM has mentioned
given a list of active files, their code so far, provide the contents of <active_file_1>[, <active_file_2>, ...]

TODO
---
- optionally disable writes (caution: removes history)
- follow links to documentation

goals
---
- convert natural language descriptions of code design/implementation into tested code

ideas
---
- keep track of TODOs
- provide a meta-language for driving dialog/state (e.g. YAML + natural language behavior description)
- implement workflows to allow user to create behavior templates specified in meta-language
- "/todo <description of thing to do>": gets added to next code generation request

"""

import argparse
import threading
from typing import Dict, List
from dataclasses import dataclass
from pprint import pformat
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import re
import subprocess
import psutil
import openai
import time
from loguru import logger
from openai import OpenAI

from coderip import config

openai.api_key = config.OPENAI_API_KEY

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
    output_data = []

    for proc in psutil.process_iter(['pid', 'name']):
        #if proc.info['name'] == executable_name:
        if executable_name.lower() in proc.info['name'].lower():
            try:
                process = psutil.Process(proc.info['pid'])
                stdout, stderr = process.communicate()
                output_info = {
                    "pid": proc.info['pid'],
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8')
                }
                output_data.append(output_info)
                logger.info(f"Captured output for PID {proc.info['pid']}: {output_info}")
            except Exception as e:
                logger.error(f"Error monitoring process {e=}")

    logger.info(f"Output data=\n{pformat(output_data)}")
    return output_data

def get_model_response(prompt: str, model: str = "gpt-4-1106-preview") -> str:
    logger.info(f"Getting model response {prompt=} {model=}")

    # Create an instance of the OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_API_KEY"))

    try:
        messages = [
            {"role": "system", "content": config.SYSTEM_MESSAGE},
            {"role": "user", "content": prompt}
        ]
        logger.info(f"messages=\n{pformat(messages)}")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        logger.info(f"response=\n{pformat(response)}")
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

        # allow TagFinder to initialize
        # TODO: use a threading.Event
        time.sleep(1)

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

# message data model

from dataclasses import dataclass

@dataclass
class SourceCodeMessage:
    code: str
    label: str

@dataclass
class FeedbackMessage:
    stdout: str
    stderr: str
    user_prompt: str
    coderip_prompt: str
    # Additional fields...

@dataclass
class MetaMessage:
    # Fields related to code editing, command running, etc.
    pass

def process_source_code(message: SourceCodeMessage):
    # Logic to handle source code
    pass

def process_feedback(message: FeedbackMessage):
    # Logic to handle feedback
    pass

def process_meta(message: MetaMessage):
    # Logic to handle meta actions
    pass


def main_loop():
    while True:
        # Code to read messages (e.g., from file system or user input)
        # Determine message type and process accordingly
        # Example:
        if isinstance(message, SourceCodeMessage):
            process_source_code(message)
        elif isinstance(message, FeedbackMessage):
            process_feedback(message)
        # More conditions based on message type...


def generate_dynamic_prompt(input_str, desired_output, context):
        # Logic to generate prompt dynamically
        # Save to a template or database for reuse
        pass


# build the workflow agent

from llmstatemachine.workflow_agent import WorkflowAgentBuilder, set_next_state

def init_func():
    # Initialization logic
    set_next_state("WatchingFiles")

def watch_files_func():
    # File watching logic
    set_next_state("ProcessingInput")

# ... define other functions for each state ...

builder = WorkflowAgentBuilder()
builder.add_system_message("Starting CodeRip...")
builder.add_state_and_transitions("INIT", {init_func})
builder.add_state_and_transitions("WatchingFiles", {watch_files_func})
# ... add other states and transitions ...

workflow_agent = builder.build()



if __name__ == "__main__":
    main()
