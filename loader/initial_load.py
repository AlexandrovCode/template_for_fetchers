import os


class Loader:
    def __init__(self, projectName):
        self.defaultProjectName = 'source_name'
        self.projectName = projectName

    def  __renameFiles(self):
        old_names = [f'./{self.defaultProjectName}.py', f'./__{self.defaultProjectName}.py']
        new_names = [f'./{self.projectName}.py', f'./__{self.projectName}.py']

        for old, new in zip(old_names, new_names):
            os.rename(old, new)

    def __updateImport(self):
        with open(f'./__{self.projectName}.py', 'r') as f:
            filedata = f.read()

        filedata = filedata.replace(f'{self.defaultProjectName}', f'{self.defaultProjectName}')

        with open(f'./__{self.projectName}.py', 'w') as f:
            f.write(filedata)

    def loaderUpdateFiles(self):
        self.__renameFiles()
        self.__updateImport()

loader = Loader(input('Enter new project name: '))

loader.loaderUpdateFiles()
