import torch

def get_device_info():
    if not torch.cuda.is_available():
        return {"device": "cpu", "name": "CPU", "vram_gb": None, "cuda_version": None}
    
    idx = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(idx)
    return {
        "device": "cuda",
        "name": props.name,
        "vram_gb": round(props.total_memory / 1e9, 1),
        "cuda_version": torch.version.cuda,
        "compute_capability": f"{props.major}.{props.minor}"
    }