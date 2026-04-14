import subprocess

def get_device_info():
    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            encoding="utf-8"
        )
        name, vram = result.strip().split(", ")
        return {
            "device": "cuda",
            "name": name,
            "vram_gb": round(float(vram) / 1024, 1),
            "cuda_version": "N/A (API Mode)", 
            "compute_capability": "N/A"
        }
    except Exception:
        return {"device": "cpu", "name": "CPU", "vram_gb": None, "cuda_version": None}