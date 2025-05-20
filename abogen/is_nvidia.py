import gpustat

def check():
    try:
        stats = gpustat.new_query()
    except Exception:
        return False

    for gpu in stats.gpus:
        print(gpu.name)
        if 'nvidia' in gpu.name.lower():
            return True
    return False

if __name__ == "__main__":
    print(check())