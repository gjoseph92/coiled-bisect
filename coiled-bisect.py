import subprocess
from pathlib import Path
import os

import coiled
import coiled.v2
import rich
import distributed
import dask
import dask.datasets

SENV_PREFIX = "florian-deadlock"
DISTRIBUTED = Path("/Users/gabe/dev/distributed")
DASK = Path("/Users/gabe/dev/dask")
BISECT = Path(__file__).parent


def run(cmd: str, **kwargs) -> str:
    return subprocess.run(
        cmd, shell=True, check=True, capture_output=True, text=True, **kwargs
    ).stdout.strip()


def run_in(path: Path, cmd: str, **kwargs) -> str:
    cwd = Path.cwd()
    try:
        os.chdir(path)
        return run(cmd, **kwargs)
    finally:
        os.chdir(cwd)


def make_software(name: str, dask_sha: str, distributed_sha: str):
    reqs = run_in(BISECT, "poetry export --without-hashes").splitlines()

    coiled.create_software_environment(
        name=name,
        account="dask-engineering",
        pip=reqs + ["urllib3"],
        # ^ cannot figure out why poetry thinks this isn't a distributed dep
        post_build=[
            # Install post-build so we can keep the main dependencies cached in a separate docker layer
            f'pip install --no-deps "git+https://github.com/dask/dask.git@{dask_sha}"',
            f'pip install --no-deps "git+https://github.com/dask/distributed.git@{distributed_sha}"',
        ],
    )


def launch_cluster(senv: str, **kwargs):
    return coiled.v2.Cluster(
        name=senv,
        account="dask-engineering",
        software=senv,
        n_workers=20,
        worker_vm_types=["t3.medium"],
        # worker_options={"data": dict()},
        environ=dict(
            DASK_LOGGING__DISTRIBUTED="debug",
            DASK_DISTRIBUTED__ADMIN__LOG_LENGTH="1000000",
            # DASK_DISTRIBUTED__SCHEDULER__WORKER_TTL="120s",
        ),
        backend_options=dict(region_name="us-west-1", keypair_name="gabe"),
    )


def run_workload(client: distributed.Client):
    ddf = dask.datasets.timeseries(
        "2020",
        "2025",
        partition_freq="2w",
    )
    ddf2 = dask.datasets.timeseries(
        "2020",
        "2023",
        partition_freq="2w",
    )

    def slowident(df):
        import random
        import time

        time.sleep(random.randint(1, 5))
        return df

    for i in range(4):
        print(f"Iteration {i}")
        client.restart()
        demo1 = ddf.map_partitions(slowident)
        fs = client.compute((demo1.x + demo1.y).mean())
        distributed.wait(fs, timeout=2 * 60)
        del fs
        print("  Simple complete")

        demo2 = ddf.merge(ddf2)
        demo2 = demo2.map_partitions(slowident)
        fs = client.compute((demo2.x + demo2.y).mean())
        distributed.wait(fs, timeout=5 * 60)
        print("  Merge complete")
        del fs


if __name__ == "__main__":
    if "site-packages" in distributed.__file__:
        raise RuntimeError(
            f"Make sure `distributed` is installed in editable mode. Current installation path: {distributed.__file__}"
        )
    if "site-packages" in dask.__file__:
        raise RuntimeError(
            f"Make sure `dask` is installed in editable mode. Current installation path: {dask.__file__}"
        )

    # Get current distributed commit
    distributed_sha = run_in(DISTRIBUTED, "git rev-parse HEAD")
    distributed_msg = run_in(DISTRIBUTED, "git log --oneline -n 1 HEAD")
    distributed_timestamp = run_in(
        DISTRIBUTED, f"git show -s --format=%ci {distributed_sha!r}"
    )
    # Figure out what dask `main` was for this distributed commit, by comparing timestamps
    dask_sha = run_in(
        DASK, f"git log -n 1 --format=format:%H --before {distributed_timestamp!r}"
    )
    dask_msg = run_in(DASK, "git log --oneline -n 1 HEAD")
    run_in(DASK, f"git checkout {dask_sha}")

    # Build senv for these commits
    senv = f"{SENV_PREFIX}-{distributed_sha[:6]}"
    rich.print(
        (
            f"[bold yellow]Build senv {senv} with:[/]\n"
            f"* distributed: {distributed_msg}\n"
            f"* dask: {dask_msg}\n"
        )
    )

    make_software(senv, dask_sha, distributed_sha)

    rich.print(f"[bold yellow]Launching cluster {senv}...[/]")
    with launch_cluster(senv) as cluster:

        rich.print(f"[bold yellow]Connecting to {senv}...[/]")
        with distributed.Client(cluster) as client:
            rich.print(f"👀 Dashboard: {client.dashboard_link}")

            rich.print(f"[bold yellow]Running workload on {senv}...[/]")
            try:
                run_workload(client)
            except distributed.TimeoutError:
                rich.print(f"❌ [bold red]{distributed_sha[:6]} is bad - timed out[/]")
                raise
            else:
                rich.print(
                    f"✅ [bold green]{distributed_sha[:6]} is good - no timeout[/]"
                )
            finally:
                rich.print(f"[bold yellow]Shutting down cluster {senv}...[/]")
