# llm/batch_runner.py

from concurrent.futures import ThreadPoolExecutor, as_completed

def run_batch(tasks, max_workers=1):
    """
    tasks: list of functions (callables with no args)
    """

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(task) for task in tasks]

        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print("[BatchRunner] Error:", str(e))

    return results