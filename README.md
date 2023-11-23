# CodeRip

Write code *fast*.

> it seems a really interesting and impactful research direction is: what is a really general and long-context retrieval-based method that does not require retraining foundation models from scratch
> 
> especially for the purpose of code generation

```
User -> CodeRip -> LLM
          |-- APIs:
          |---- hosted (OpenAI / HuggingFace) & offline (llama.cpp)
          |-- data model:
          |---- source: source code on disk
          |---- issue/pr: Github Issues/PRs
          |---- automatic git integration (user-gated writes)
          |-- user interaction modes:
          |---- compose / build mode
          |---- review mode
          |------ Issue (backlog grooming)
          |------ PR (merging)
          |-- "crip" CLI tool (python-fire)
```

(Unstable.)

See top of `coderip/main.py` for more.

<img width="1296" alt="image" src="https://github.com/abrichr/coderip/assets/774615/3d5114fe-884b-45ef-ae1b-fe96297b669c">


## Clone

```
git clone https://github.com/abrichr/coderip.git
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
