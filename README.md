# CodeRip

Write code *fast*.

```
User -> CodeRip -> LLM
          |-- APIs:
          |---- OpenAI / HuggingFace / llama.cpp
          |-- Data:
          |---- source code on disk
          |---- Github Issues/PRs
          |---- automatic git integration (user-gated writes)
          |-- Modes:
          |---- composition
          |---- Issue Review (backlog grooming)
          |---- PR Review (merging)
```
(Unstable.)

See top of `coderip/main.py` for more.

<img width="1510" alt="image" src="https://github.com/abrichr/coderip/assets/774615/7b7deedc-72f2-4f65-915c-c49de86a695f">

## Clone

```
git clone [https://<TODO>](https://github.com/abrichr/coderip.git)
```


## Install

```
cd coderip && poetry install
```

## Run

Set `OPENAI_API_KEY` in `.env`, then:

```
poetry run python coderip/main.py my/project_path [my_process_name]  # TODO: hook into stdin/stderr
```

## Usage

TODO
