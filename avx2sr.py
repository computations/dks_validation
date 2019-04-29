#!/usr/bin/env python3

import pickle

with open('results.pkl', 'rb') as pkl:
    results = pickle.load(pkl)

best_times = []
avx2sr_times = []
ratios = []

for dataset, times in results.items():
    best_time = float('inf')
    avx2sr_time = 0.0
    for t in times:
        if t['time'] < best_time:
            best_time = t['time']
        if t['siterepeats'] == 'on' and t['simd'] == 'avx2':
            avx2sr_time = t['time']
    best_times.append(best_time)
    avx2sr_times.append(avx2sr_time)
    ratios.append(avx2sr_time/best_time)
    print(dataset, "\t", avx2sr_time/best_time)

print(ratios)
