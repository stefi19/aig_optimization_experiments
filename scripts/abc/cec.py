import shutil
import subprocess
import tempfile
from pathlib import Path


def staged_cec(abc_path, left, right, timeout=30):
    if abc_path is None or not Path(abc_path).is_file():
        return "abc_unavailable", ""
    try:
        with tempfile.TemporaryDirectory() as staging:
            shutil.copyfile(left, Path(staging)/"left.blif")
            shutil.copyfile(right, Path(staging)/"right.blif")
            proc=subprocess.run([str(Path(abc_path).resolve()),"-q","cec left.blif right.blif"],cwd=staging,
                                text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    except subprocess.TimeoutExpired:
        return "timeout", "ABC timeout"
    text=proc.stdout
    if "not equivalent" in text.lower():
        return "disproved",text
    if proc.returncode==0 and "Networks are equivalent" in text:
        return "equivalent",text
    return "unknown",text
