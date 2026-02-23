"""Test ML environment setup."""

import sys
print(f"Python: {sys.version}\n")

# Test imports
packages = [
    ('torch', 'PyTorch'),
    ('torchvision', 'TorchVision'),
    ('cv2', 'OpenCV'),
    ('numpy', 'NumPy'),
    ('pandas', 'Pandas'),
    ('matplotlib', 'Matplotlib'),
    ('sklearn', 'Scikit-learn'),
]

all_good = True
for module, name in packages:
    try:
        pkg = __import__(module)
        version = getattr(pkg, '__version__', 'unknown')
        print(f"✅ {name}: {version}")
    except ImportError:
        print(f"❌ {name}: NOT INSTALLED")
        all_good = False

# Test PyTorch device
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"\n{'✅' if torch.cuda.is_available() else '⚠️'} PyTorch device: {device}")
if torch.cuda.is_available():
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
else:
    print("   (CPU mode - fine for development)")

if all_good:
    print("\n🎉 Environment setup complete!")
else:
    print("\n⚠️ Some packages missing - check errors above")