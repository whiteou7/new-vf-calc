"""python generate.py --start 1 --end 3000 --workers 4"""

import argparse

from lib import generate_b50_image, prefetch_jackets

__all__ = ["generate_b50_image", "prefetch_jackets"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prefetch SDVX jackets")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=3000)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    print(f"Prefetching jackets {args.start} -> {args.end} with {args.workers} workers...")
    prefetch_jackets(args.start, args.end, args.workers)
    print("Done.")
