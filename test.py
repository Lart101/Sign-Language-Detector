import torch

print("CUDA available:", torch.cuda.is_available())
print("CUDA version (PyTorch):", torch.version.cuda)
print("Device count:", torch.cuda.device_count())
