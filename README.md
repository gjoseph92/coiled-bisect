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

Edit the script in [`coiled-bisect.py`](blob/main/coiled-bisect.py) as necessary to actually trigger your error condition. You'll most want to modify `run_workload`, `launch_cluster`, and `make_software`, and the error-handling logic around the invoation of `run_workload`. The script needs to exit 0 when things work, and exit nonzero otherwise.

# Use

Make sure you still have this poetry environment activated, then go to your dask fork and start bisecting!

```
(coiled-bisect-HV2P9iVq-py3.9) $ cd <../distributed>
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect start
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect bad
(coiled-bisect-HV2P9iVq-py3.9) $ git checkout <good-tag-or-commit>
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect good
(coiled-bisect-HV2P9iVq-py3.9) $ git bisect run python <../coiled-bisect/coiled-bisect.py>
```
