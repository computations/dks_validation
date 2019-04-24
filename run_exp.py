#!/usr/bin/env python3

import os
import shutil
import subprocess
import json
import csv
import argparse
import pathlib
import pickle

DKS_GIT = r"https://github.com/computations/dks"
RAXML_GIT = r"https://github.com/amkozlov/raxml-ng.git"
TEST_DATA_GIT = r"https://github.com/stamatak/test-Datasets.git"
GIT_COMMAND = r"git clone --recursive {}"

RAXML_COMMAND = r"{raxml_binary} --tree rand{tree_number} --msa {msa}"\
        " --model {model} --tip-inner {tip_inner} --site-repeats"\
        " {site_repeats} --simd {simd} --seed {seed} --force"

DKS_COMMAND = r"{dks_binary} --msa {msa} --states {states}"

EXP_PATH_TEMPLATE = "tipinner.{tip_inner}_siterepeats.{site_repeats}_simd.{simd}"

TEST_FILES = [
        r'DNA-Data/101/101.phy',
        r'DNA-Data/125/125.phy',
        r'DNA-Data/128/128.phy',
        r'DNA-Data/354/354.phy',
        r'DNA-Data/628/628.phy',
        r'DNA-Data/1604/1604.phy',
        r'DNA-Data/2000/2000.phy',
        r'DNA-Data/2308/2308.phy',
        r'DNA-Data/3782/3782.phy',
        r'Protein-Data/140/140.phy',
        r'Protein-Data/775/775.phy',
        ]


def build_dks():
    root_path = os.getcwd()
    os.chdir('dks')
    subprocess.run('cmake -Bbuild -H.'.split())
    os.chdir('build')
    subprocess.run('make'.split())
    os.chdir(root_path)

def build_raxml():
    root_path = os.getcwd()
    os.chdir('raxml-ng')
    subprocess.run('cmake -Bbuild -H.'.split())
    os.chdir('build')
    subprocess.run('make'.split())
    os.chdir(root_path)

def dl_repos():
    subprocess.run(GIT_COMMAND.format(DKS_GIT).split())
    subprocess.run(GIT_COMMAND.format(RAXML_GIT).split())
    subprocess.run(GIT_COMMAND.format(TEST_DATA_GIT).split())

def run_raxml(dst_dir, dst_file, msa_path):
    seed = get_seed(dst_dir)
    for ti in ['on', 'off']:
        for sr in ['on', 'off']:
            if ti == sr:
                continue
            for simd in ['avx', 'avx2']:
                exp_path = os.path.join(dst_dir,
                        EXP_PATH_TEMPLATE.format(tip_inner=ti, site_repeats=sr,
                            simd=simd))
                if check_done(exp_path):
                    continue
                shutil.rmtree(exp_path, ignore_errors=True)
                os.makedirs(exp_path)
                exp_data_path = os.path.join(exp_path, dst_file)
                os.symlink(msa_path, exp_data_path)
                subprocess.run(RAXML_COMMAND.format(simd=simd, tip_inner=ti,
                    site_repeats=sr, tree_number='{1}',
                    raxml_binary='raxml-ng/bin/raxml-ng',
                    msa=exp_data_path, model='gtr' if 'DNA' in msa_path else
                    'lg', seed=seed).split())
                make_done(exp_path)

def check_done(path):
    return os.path.exists(os.path.join(path, ".done"))

def make_done(path):
    pathlib.Path(os.path.join(path, ".done")).touch()

def get_seed(path):
    seed_path = os.path.join(path,'.seed')
    if not os.path.exists(seed_path):
        make_seed(path)
    with open(os.path.join(path, '.seed')) as seed_file:
        return int(seed_file.read())

def make_seed(path):
    with open('/dev/urandom', 'rb') as rand_file:
        seed = int.from_bytes(rand_file.read(4), 'big')
    with open(os.path.join(path, '.seed'), 'w') as seed_file:
        seed_file.write(str(seed))


def run_exp(msa_path):
    dst_dir = "experiments/exp_{}".format(os.path.splitext(os.path.split(msa_path)[1])[0])
    dst_file = os.path.split(msa_path)[1]
    if check_done(dst_dir):
        return
    try:
        os.makedirs(dst_dir)
    except:
        pass
    dks_file = os.path.join(dst_dir, 'dks_results')
    if not os.path.exists(dks_file):
        dks = subprocess.run(DKS_COMMAND.format(dks_binary='dks/build/raxml-dks',
            msa=msa_path, states='4' if 'DNA' in msa_path else
            '20').split(), stdout=subprocess.PIPE)
        with open(dks_file, 'w') as outfile:
            outfile.write(dks.stdout.decode('utf-8'))
    run_raxml(dst_dir, dst_file, os.path.abspath(msa_path))
    make_done(dst_dir)


def summarize_output(exp_dir):
    old_path = os.getcwd()
    os.chdir(exp_dir)
    times = []

    def make_attrib(line):
        ret = {}
        line = line.split('/')[1]
        parts = line.split('_')
        for part in parts:
            k,v = part.split('.')
            ret[k] = v
        return ret

    def compute_time(time_line):
        time_line = time_line[len('Elapsed time: '):]
        time_line = time_line[:-len(' Seconds')]
        try:
            return float(time_line)
        except:
            return float('inf')


    def get_time(filename):
        lines = []
        with open(filename) as infile:
            for line in infile:
                lines.append(line)
        time_line = lines[-2].strip()
        attr = make_attrib(filename)
        attr['time'] = compute_time(time_line)
        return attr

    for root, dirs, files in os.walk('.'):
        for f in files:
            if os.path.splitext(f)[1] == '.log':
                times.append(get_time(os.path.join(root, f)))

    with open('times.json', 'w') as outfile:
        outfile.write(json.dumps(times, indent=2))

    with open('times.csv', 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=times[0].keys())
        writer.writeheader()
        for time in times:
            writer.writerow(time)
    os.chdir(old_path)

def make_table():
    results = {}
    for d in os.listdir('experiments'):
        dataset = d.split('_')[1]
        with open(os.path.join('experiments', d, 'times.json')) as tjson:
            results[dataset] = json.load(tjson)

    with open('results.pkl', 'wb') as pickle_file:
        pickle.dump(results,pickle_file)
    with open('results.md', 'w') as results_file:
        table_cols = []
        for _, value in results.items():
            table_cols = list(value[0].keys())
        for d, times in results.items():
            results_file.write(d)
            results_file.write('\n')
            results_file.write('='*80)
            results_file.write('\n')
            results_file.write('\n')
            results_file.write((' '*4).join(table_cols))
            results_file.write('\n')
            for col in table_cols:
                results_file.write('-'*len(col))
                if col is not table_cols[-1]:
                    results_file.write(' '*4)
            results_file.write('\n')

            for t in times:
                for col in table_cols:
                    write_string = t[col];
                    if type(t[col]) == float:
                        write_string = str(write_string)
                    if col != table_cols[-1]:
                        write_string += ((len(col)+4) - len(t[col]))*' '
                    results_file.write(write_string)
                results_file.write('\n')
            results_file.write('\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-raxml', default=False, action='store_true')
    parser.add_argument('--build-dks', default=False, action='store_true')
    args = parser.parse_args()
    dl_repos()
    if args.build_dks:
        build_dks()
    if args.build_raxml:
        build_raxml()
    for msa_path in TEST_FILES:
        run_exp("test-Datasets/"+msa_path)
    for d in os.listdir('experiments'):
        summarize_output(os.path.join('experiments',d))
    make_table()
