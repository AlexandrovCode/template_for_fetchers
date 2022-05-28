import shutil
import os
from initial_load import loader
from distutils.dir_util import copy_tree


projectName = loader.projectName
base_dir = os.path.join(loader.currentPath, '..')
current_version = 1.0
path = os.path.join(loader.currentPath, '..', projectName + f'_v{current_version}')



def copy_required_files(targetPath):
    base_path = os.path.join(loader.currentPath, '..', 'src')
    targetPath1 = os.path.join('..', targetPath, 'src')
    copy_tree(base_path, targetPath1)

    base_path = os.path.join(loader.currentPath, '..', f'{projectName}.py')
    shutil.copy(base_path, f'{targetPath}')
    base_path = os.path.join(loader.currentPath, '..', f'__{projectName}.py')
    shutil.copy(base_path, f'{targetPath}')

def make_zip(path, version):
    outputFileName = projectName + f'_{version}'
    out = os.path.join(base_dir, outputFileName, '..', outputFileName)
    shutil.make_archive(out, 'zip', path)

def check_path(path, version):
    if not os.path.exists(path):
        os.mkdir(path)
        copy_required_files(path)
        make_zip(path, version)
        return
    else:
        current_version = float(path.split('_v')[-1])
        current_version += 0.1
        path = path[:-3] + str(current_version)[:3]
        check_path(path, str(current_version)[:3])


check_path(path, current_version)

