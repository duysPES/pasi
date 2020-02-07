"""
scans every file in pysrc and collects lines that have TODO: to show the todo list.
"""
from pathlib import Path
from colorama import Fore

if __name__ == "__main__":
    p = Path("pysrc")
    for i in p.glob("**/*.py"):
        with open(i, "r") as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if "TODO" in line:
                    print(
                        f"{Fore.GREEN}{i}:{Fore.YELLOW}{ln}{Fore.RESET}> {Fore.CYAN}{line}"
                    )
