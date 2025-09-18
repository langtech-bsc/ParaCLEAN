import subprocess

def run(input_tsv, output_tsv, l1, l2, flags=None):
	"""
	Optional Bifixer step.
	flags: list of strings for Bifixer CLI options
	"""
	flags = flags or []
	cols = ["--scol", "1", "--tcol", "2"]
	try:
		cmd = ["bifixer", input_tsv, output_tsv, l1, l2] + cols + flags
		print(f"[bifixer] Running: {' '.join(cmd)}")
		subprocess.run(cmd, check=True)
	except FileNotFoundError:
		print("[bifixer] Bifixer not installed. Skipping step.")
	except subprocess.CalledProcessError as e:
		print(f"[bifixer] Bifixer failed: {e}")