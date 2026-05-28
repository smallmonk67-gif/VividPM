import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vivid_gui.backends import apt_backend

print("APT Available:", apt_backend.is_available())
if apt_backend.is_available():
    import time
    start = time.time()
    results = apt_backend.search("python3")
    end = time.time()
    print(f"Search took {end - start:.4f} seconds")
    print(f"Found {len(results)} results")
    if results:
         print("First result:", results[0])
    
    # Try searching again to test caching
    start2 = time.time()
    results2 = apt_backend.search("curl")
    end2 = time.time()
    print(f"Cached search took {end2 - start2:.4f} seconds")
    print(f"Found {len(results2)} results")
