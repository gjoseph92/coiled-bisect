# Bisecting a distributed deadlock with Coiled

We create a software environment with different dask and distributed versions, spin up a cluster, and run a test, all as a part of a `git bisect` script.

Note that this is driven from your local machine and may take a few hours, so don't let it [go to sleep](https://apps.apple.com/us/app/coca/id1000808993?mt=12), lose internet, run out of batteries, etc!

You'll need to have the [`dask/dask`](https://github.com/dask/dask) and[ `dask/distributed`](https://github.com/dask/distributed) repos cloned locally, in separate directories, and [poetry installed](https://python-poetry.org/docs/#installation).

# Setup

Install local dask & distributed forks in editable mode via pip within the poetry venv (since poetry doesn't support this [python-poetry/poetry#34](https://github.com/python-poetry/poetry/issues/34)).

```bash
$ gh repo fork --clone gjoseph92/coiled-bisect
$ cd coiled-bisect
$ poetry install
$ poetry shell
(coiled-bisect-HV2P9iVq-py3.9) $ pip install --no-deps -e <path-to-dask-fork>
(coiled-bisect-HV2P9iVq-py3.9) $ pip install --no-deps -e <path-to-distributed-fork>
```

Edit the script in [`coiled-bisect.py`](coiled-bisect.py) as necessary to actually trigger your error condition. You'll most want to modify `run_workload`, `launch_cluster`, and `make_software`, and the error-handling logic around the invoation of `run_workload`. The script needs to exit 0 when things work, and exit nonzero otherwise.

You'll also need to edit the `DISTRIBUTED` and `DASK` global variables to the paths of the distributed and dask forks on your local machine. And set the `SENV_PREFIX` as appropriate.

# Use

Make sure you still have this poetry environment activated, then go to your dask fork and start bisecting!

```shell
(coiled-bisect-HV2P9iVq-py3.9) $ cd <../distributed>
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect start
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect bad
(coiled-bisect-HV2P9iVq-py3.9) $ git checkout <good-tag-or-commit>
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect good
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect run python <../coiled-bisect/coiled-bisect.py>
running  'python' '../coiled-bisect/coiled-bisect.py'
Build senv florian-deadlock-0dab52 with:
* distributed: 0dab5262 Revert #5883 (#5961)
* dask: 02f388659 Reduce gpuci ``pytest`` parallelism (#8826)

Creating new software environment
[...]
Successfully saved software environment build
Launching cluster florian-deadlock-0dab52...
Connecting to florian-deadlock-0dab52...
👀 Dashboard: http://54.153.110.227:8787
Running workload on florian-deadlock-0dab52...
Iteration 0
  Simple complete
❌ 0dab52 is bad - timed out
Shutting down cluster florian-deadlock-0dab52...
Traceback (most recent call last):
    [...]
    raise exceptions.TimeoutError() from exc
asyncio.exceptions.TimeoutError

Bisecting: 51 revisions left to test after this (roughly 6 steps)
[94d622680710fc1913de7aa390cfd23d61b803d7] Do not run schedule jobs on forks (#5821)
running  'python' '../coiled-bisect/coiled-bisect.py'
Build senv florian-deadlock-94d622 with:
* distributed: 94d62268 Do not run schedule jobs on forks (#5821)
* dask: 47fa383c2 Fix upstream missing newline after `info()` call on empty DataFrame (#8727)

Found existing software environment build, returning
Launching cluster florian-deadlock-94d622...
Connecting to florian-deadlock-94d622...
👀 Dashboard: http://54.241.222.164:8787
Running workload on florian-deadlock-94d622...
Iteration 0
  Simple complete
  Merge complete
Iteration 1
  Simple complete
  Merge complete
Iteration 2
  Simple complete
  Merge complete
Iteration 3
  Simple complete
  Merge complete
✅ 94d622 is good - no timeout
Shutting down cluster florian-deadlock-94d622...

Bisecting: 25 revisions left to test after this (roughly 5 steps)
[fb8484ece6fd320a5c79d3ec0a07c72913905adb] Fix `distributed` pre-release's `distributed-impl` constraint (#5867)
running  'python' '../coiled-bisect/coiled-bisect.py'
Build senv florian-deadlock-fb8484 with:
* distributed: fb8484ec Fix `distributed` pre-release's `distributed-impl` constraint (#5867)
* dask: 217561b42 bump version to 2022.02.1
[...]
```
