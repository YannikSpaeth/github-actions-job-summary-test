# GitHub Actions PR Test Summary Demo

This repository is a small C++/CTest demo used to prototype a GitHub Actions setup that:

- runs tests on multiple jobs,
- uploads raw JUnit XML artifacts,
- merges all results in one reporting job,
- writes a GitHub Actions job summary, and
- posts or updates a single pull request comment.

The current setup is intentionally simple so it can be copied into another repository such as eCAL.

## What the comment looks like

The PR comment shows:

- one summary row per platform/job,
- a green checkmark for jobs with no failed tests,
- a red cross for jobs with failures,
- one collapsible entry per failing test, and
- clickable source links to the failing file and line.

## Repository layout

```text
.
├── .github/workflows/
│   ├── ci.yml
│   ├── build-ubuntu.yml
│   ├── build-windows.yml
│   └── collect-and-report.yml
├── scripts/
│   ├── merge_and_post.py
│   └── comment_template.md.j2
├── docs/
│   └── README.md
├── src/
├── include/
├── tests/
└── CMakeLists.txt
```

## Workflow overview

The flow is:

```text
pull_request / push
          │
          ├── ci.yml
          │     ├── build-ubuntu.yml
          │     ├── build-windows.yml
          │     └── collect-and-report.yml
          │
          ├── each build job runs CMake + CTest
          ├── each build job uploads test-results-<platform>
          └── report job downloads all XML files and posts one PR comment
```

### Workflow files

- [ci.yml](.github/workflows/ci.yml): main entry point triggered by `push` and `pull_request`
- [build-ubuntu.yml](.github/workflows/build-ubuntu.yml): reusable build workflow for Ubuntu
- [build-windows.yml](.github/workflows/build-windows.yml): second reusable workflow used to simulate a multi-job summary
- [collect-and-report.yml](.github/workflows/collect-and-report.yml): downloads artifacts, installs Python dependencies, and runs the merge script

## Script overview

- [merge_and_post.py](scripts/merge_and_post.py): parses all XML files, renders markdown from a Jinja template, writes the job summary, and posts/updates the PR comment
- [comment_template.md.j2](scripts/comment_template.md.j2): controls the layout of the PR comment

The script uses the automatic `GITHUB_TOKEN`, so no personal access token is required.

## Build and run locally

### Configure and build

```bash
cmake -B build
cmake --build build
```

### Run the demo app

```bash
./build/demo_app
```

### Run tests

```bash
ctest -V --test-dir build --output-junit test-results/test-results.xml
```

Because `--test-dir build` is used, the XML is written to:

```text
build/test-results/test-results.xml
```

Some tests are intentionally failing so the workflow has realistic output to aggregate.

## How to adapt this to eCAL

To try this in an eCAL fork, copy these pieces:

- [.github/workflows/ci.yml](.github/workflows/ci.yml)
- [.github/workflows/build-ubuntu.yml](.github/workflows/build-ubuntu.yml)
- [.github/workflows/build-windows.yml](.github/workflows/build-windows.yml)
- [.github/workflows/collect-and-report.yml](.github/workflows/collect-and-report.yml)
- [scripts/merge_and_post.py](scripts/merge_and_post.py)
- [scripts/comment_template.md.j2](scripts/comment_template.md.j2)

Then change only the build workflows:

1. Replace the demo CMake commands with eCAL's real build/test commands.
2. Keep the JUnit output path in a dedicated subfolder, for example:

    ```bash
    ctest -V --test-dir build --output-junit test-results/test-results.xml
    ```

3. Keep the artifact upload step and artifact naming pattern:

    ```yaml
    name: test-results-ubuntu
    path: build/test-results/test-results.xml
    ```

4. Add more platform workflows as needed and call them from [ci.yml](.github/workflows/ci.yml).

## Permissions

The reporting workflow needs:

```yaml
permissions:
  contents: read
  pull-requests: write
```

The repository also needs GitHub Actions to have write-enabled workflow permissions if PR comments should be posted.

## Notes

- `build-windows.yml` currently uses `ubuntu-latest` to simulate a second platform.
- The template can be changed without touching Python logic.
- The same PR comment is updated on reruns, not duplicated.

## More documentation

See [docs/README.md](docs/README.md) for integration notes and a migration checklist for eCAL.
