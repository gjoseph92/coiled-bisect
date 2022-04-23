"""
Clean up software environments created by `coiled-bisect.py`, aka all environments that start with a given prefix.
"""
import asyncio
import sys
import coiled

ACCOUNT = "dask-engineering"


async def delete_senvs(prefix: str):
    async with coiled.Cloud(asynchronous=True) as client:
        senvs = await client.list_software_environments(ACCOUNT)
        matches = [s for s in senvs if s.split("/")[1].startswith(prefix)]
        input(f"Going to delete {matches}. Press enter to confirm, Ctrl-C to exit: ")

        await asyncio.gather(
            *(
                client.delete_software_environment(senv, account=ACCOUNT)
                for senv in matches
            )
        )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Pass the software environment prefix as the only CLI argument, like `python cleanup.py senv-foo`"
        )
        sys.exit(1)

    asyncio.run(delete_senvs(sys.argv[1]))
