from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
path = root / "lib/features/history/history_screen.dart"
source = path.read_text()
needle = "_setWell();WorkTaskStore.instance.addListener(_refreshHistory);"
assert source.count(needle) == 1, "Unexpected history screen layout"
source = source.replace(needle, "_setWell();_resolvedProblemsFuture=repo.resolvedProblems();WorkTaskStore.instance.addListener(_refreshHistory);", 1)
path.write_text(source)
print("History future initialized before first frame")
