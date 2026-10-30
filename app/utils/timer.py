import time


class Timer:
    def __init__(self, description="Operation"):
        self.description = description
        self.start = None
        self.end = None
        self.elapsed = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start
        print(f"{self.description} took {self.elapsed:.6f} seconds")

        # Optional: Re-raise exception if one occurred inside the block
        return not exc_type


"""
usage:
wtih Timer() as t:
    func()

execution_time = t.elapsed


    # origina version - can be removed anyway
    if exc_type:
        return False
    return True

"""
