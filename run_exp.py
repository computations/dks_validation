#!/usr/bin/env python3

import os
import shutil
import subprocess

DKS_GIT = r"https://github.com/computations/dks"
RAXML_GIT = r"https://github.com/amkozlov/raxml-ng.git"
TEST_DATA_GIT = r"https://github.com/stamatak/test-Datasets.git"
GIT_COMMAND = r"git clone --recursive {}"

RAXML_COMMAND = r"{raxml_binary} --tree rand{tree_number} --msa {msa}"\
        " --model {model} --tip-inner {tip_inner} --site-repeats"\
        " {site_repeats} --simd {simd} --force"

EXP_PATH_TEMPLATE = "tipinner.{tip_inner}_siterepeats.{site_repeats}_simd.{simd}"

TEST_FILES = [
        r'DNA-Data/125/125.phy',
        #r'DNA-Data/354/354.phy',
        #r'Protein-Data/140/140.phy',
        #r'Protein-Data/775/775.phy',
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

def run_exp(msa_path):
    dst_dir = "experiments/exp_{}".format(os.path.splitext(os.path.split(msa_path)[1])[0])
    dst_file = os.path.split(msa_path)[1]
    try:
        os.makedirs(dst_dir)
    except:
        pass
    for ti in ['on', 'off']:
        for sr in ['on', 'off']:
            if ti == sr:
                continue
            for simd in ['none', 'sse', 'avx', 'avx2']:
                exp_path = os.path.join(dst_dir,
                        EXP_PATH_TEMPLATE.format(tip_inner=ti, site_repeats=sr,
                            simd=simd))
                shutil.rmtree(exp_path, ignore_errors=True)
                os.makedirs(exp_path)
                exp_data_path = os.path.join(exp_path, dst_file)
                shutil.copyfile(msa_path, exp_data_path)
                subprocess.run(RAXML_COMMAND.format(simd=simd, tip_inner=ti,
                    site_repeats=sr, tree_number='{1}',
                    raxml_binary='raxml-ng/bin/raxml-ng',
                    msa=exp_data_path, model='gtr' if 'DNA' in msa_path else
                    'lg').split())

if __name__ == "__main__":
    dl_repos()
    build_dks()
    build_raxml()
    for msa_path in TEST_FILES:
        run_exp("test-Datasets/"+msa_path)
