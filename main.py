"""
*** Only tested on PYTHON V3.7 ***

This script analyses a python project and generates a 'requirements.txt' file in a 'pip freeze' format
containing the packages used in the project and versions of those packages.

***************************************************************
IMPORTANT: to get accurate results, this script MUST be run using the same interpreter or virtual environment
           as your project to be analysed.
***************************************************************

PROJECT DIRECTORY: the root folder of the python project you want to analyse.
DIRS_TO_SKIP: names of directories containing virtual environments and such should be added here. The script
              will then skip them when searching for packages you imported on python files.
VERBOSE: if set to False, the console will display all the required info to keep you informed.
         If set to True, additional info will be logged in the console.

*** Code by dcgolobart, OCT-2020 ***
"""


PROJECT_DIRECTORY = '/Users/Python'
DIRS_TO_SKIP = ['env', 'venv', 'conda']
VERBOSE = False


import os, re
from pip._internal.operations import freeze

print('Walking through "%s"...' % PROJECT_DIRECTORY)

num_dirs = 0
filepaths = []
for dirpath, dirnames, filenames in os.walk(PROJECT_DIRECTORY):
    num_dirs += 1
    skip_current_dir = False
    rel_dir = re.sub(PROJECT_DIRECTORY, '', dirpath)
    for dir_to_skip in DIRS_TO_SKIP:
        if re.search(r'[\w/]*/{dir}/?'.format(dir=dir_to_skip), rel_dir):
            skip_current_dir = True

    if VERBOSE:
        if skip_current_dir:
            print('\t## SKIPPING DIR ##')
        print('\tdirpath --> %s' % dirpath)
        print('\tdirnames --> %s' % dirnames)
        print('\tfilenames --> %s' % filenames)
        print('\t-------------------------------')

    if skip_current_dir:
        continue

    for filename in filenames:
        filepaths.append('/'.join([dirpath, filename]))

print('Found %s files in %s directories and subdirectories.' % (str(len(filepaths)), str(num_dirs)))
if VERBOSE:
    print('Listing all files in directory and subdirectories...')
    print(filepaths)

print('Analyzing imported packages into "*.py" files...')

num_py_files = 0
import_lines = []
for filepath in filepaths:
    if re.search(r'[^_].+\.py$', filepath):
        num_py_files += 1
        with open(filepath, 'r') as f:
            prev_line_broken = False
            for line in f:
                if prev_line_broken:
                    prev_line = re.sub(r'\\\n', '', import_lines[-1])
                    import_lines[-1] = ' '.join([prev_line, line])
                    prev_line_broken = False
                    continue
                if re.search(r'^\s*import\s+', line) or re.search(r'^\s*from\s+', line):
                    import_lines.append(line)
                    if re.search(r'\\\n$', line):
                        prev_line_broken = True

print('Found %s import line statements in %s python files.' % (str(len(import_lines)), str(num_py_files)))

packages = []
for line in import_lines:
    if re.search(r'^\s*import\s+', line):
        line = re.sub(r'import', '', line)
        line = re.sub(r'\s+as\s+[\w\.]+\s+', '', line)
        line = re.sub(r'\s', '', line)
        line_packages = line.split(',')
        for package in line_packages:
            if package.startswith('.') or package.startswith('_'):
                continue
            packages.append(package.split('.')[0])
    elif re.search(r'^\s*from[\s\.\w]+import', line):
        line = re.search(r'^\s*(from[\s\.\w]+)import', line).group(1)
        line = re.sub(r'from', '', line)
        line = re.sub(r'\s', '', line)
        if line.startswith('.') or line.startswith('_'):
            continue
        packages.append(line.split('.')[0])

imported_packages = list(set(packages))

# Clean up comments
for i in range(len(imported_packages)):
    if '#' in imported_packages[i]:
        imported_packages[i] = re.search(r'(.+)#.*', imported_packages[i]).group(1)

imported_packages.sort()

print('Found %s different imported packages in total.' % str(len(imported_packages)))
if VERBOSE:
    for package in imported_packages:
        print(''.join(['\t', package]))

print('\nLooking for installed package versions...')

installed_packages = []
for pkg in freeze.freeze():
    installed_packages.append(tuple(pkg.split('==')))

print('Found %s installed packages in total.' % str(len(installed_packages)))
if VERBOSE:
    max_len = 0
    for pkg, ver in installed_packages:
        if len(pkg) > max_len:
            max_len = len(pkg)
    max_len += 1
    print(''.join(['\t', 'PKG', ' ' * (max_len - len('PKG')), 'VER']))
    i = 0
    for pkg, ver in installed_packages:
        current_len = len(pkg)
        if i < 30 or i > len(installed_packages) - 5:
            print(''.join(['\t', pkg, ' ' * (max_len - current_len), ver]))
        elif i == len(installed_packages) - 5:
            print('\t...')
            print('\tskipped %s entries for brevity...' % str(i - 30))
            print('\t...')
        i += 1

used_packages = []
for pkg_imp_name in imported_packages:
    for pkg_inst_name, pkg_inst_ver in installed_packages:
        if pkg_imp_name.lower() == pkg_inst_name.lower():
            used_packages.append((pkg_inst_name, pkg_inst_ver))
            break

print('\nFound %s (non Python lib) used packages in total.' % str(len(used_packages)))
if VERBOSE:
    used_packages.insert(0, ('PKG', 'VER'))
    max_len = 0
    for package, version in used_packages:
        if len(package) > max_len:
            max_len = len(package)
    max_len += 1
    for package, version in used_packages:
        current_len = len(package)
        print('\t%s%s%s' % (package,' ' * (max_len - current_len),version))
    used_packages.remove(('PKG', 'VER'))

print('\nGenerating "requirements.txt"...')
filename = 'requirements.txt'
if not PROJECT_DIRECTORY.endswith('/'):
    filename = ''.join(['/', filename])

ans = ''
if os.path.exists(''.join([PROJECT_DIRECTORY, filename])):
    while ans not in ['y', 'Y', 'n', 'N']:
        ans = input(''.join(['"', PROJECT_DIRECTORY, filename, '" already exists.\nDo you want to overwrite? (Y/N): ']))
else:
    ans = 'Y'

if ans in ['y', 'Y']:
    with open(''.join([PROJECT_DIRECTORY, filename]), 'w') as f:
        for pkg, ver in used_packages:
            f.write(''.join([pkg, '==', ver, '\n']))
    print('"requirements.txt" generated successfully.')
else:
    print('"requirements.txt" has not been overwriten.')
