import gpustat

def check():
    stats = gpustat.new_query()
    for gpu in stats.gpus:
        print(gpu.name)
        if 'nvidia' in gpu.name.lower():
            return True
    return False

if __name__ == "__main__":
    print(check())
