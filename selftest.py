#---------------------------------------------------------------------------------------------------#
# File name: selftest.py                                                                            #
# Autor: Chrissi2802                                                                                #
# Created on: 22.04.2021                                                                            #
# Content: This file provides a class to check python files.                                        #
#---------------------------------------------------------------------------------------------------#
# Code from: https://github.com/Chrissi2802/Helpers/blob/main/selftest.py


import os
import platform


class Selftest():
    """This class is used to check python files.
    """
    
    def __init__(self, skip_file_list = []):
        """Initialisation of the class (constructor). Executes the checks.

        Args:
            skip_file_list (list, optional): Files to be skipped. Defaults to [].
        """
        
        self.return_value_io = 0
        self.return_value_nio = 1
        self.skip_file_list = skip_file_list
        self.skip_file_list_big = self.skip_file_list + ["main.py", str(__file__).split("\\")[-1]]
        self.__identify_operation_system()
        
        self.run()
        
    def __identify_operation_system(self):
        """This method identifies the operating system in use.
        """
        
        if platform.system().find("Windows") < 0:
            self.python_command_name = "python3"   # Linux or Mac
        else:
            self.python_command_name = "python"    # Windows
    
    def __create_file_list(self):
        """This method creates a list of all Python files in this folder.
        """
        
        self.file_list = [file for file in os.listdir() if file.endswith(".py")]
        i = 0
        
        # Run through all python files
        while i < len(self.file_list):
            
            delete_file = False
            
            # Run through all files that should be skipped
            for j in range(len(self.skip_file_list_temp)):
                
                if self.skip_file_list_temp[j] == self.file_list[i]:
                    delete_file = True
                
            if delete_file == True:
                del self.file_list[i]
            else:
                i += 1
                    
    def __run_through_file_list(self, function, skip_file_list_temp):
        """This method traverses the file list and executes the passed function on these files. Exceptions can be passed.

        Args:
            function (method): Check method to be executed
            skip_file_list_temp (list): Files to be skipped
        """
        
        self.skip_file_list_temp = skip_file_list_temp
        self.__create_file_list()
        
        # Run through all files
        for file in self.file_list:
            
            print(function.__name__, "checks", file)
            return_value = function(file)
            assert (return_value == self.return_value_io), "Error in: " + file
    
    def __check_pyflakes(self, file):
        """This method checks Python source files for errors.

        Args:
            file (string): File that will be checked

        Returns:
            return_value (integer): Return value, is 0 if everything is ok
        """
        
        return_value = os.system("pyflakes " + file)
        
        return return_value
    
    def __check_vulture(self, file):
        """This method finds unused code.

        Args:
            file (string): File that will be checked

        Returns:
            return_value (integer): Return value, is 0 if everything is ok
        """

        return_value = os.system("vulture " + file + " --min-confidence 80")
        
        return return_value
    
    def __check_file_imported_somewhere(self, file):
        """This method checks if the files were imported into one of the other files.

        Args:
            file (string): File that will be checked

        Returns:
            return_value (integer): Return value, is 0 if everything is ok
        """
        
        file_name, file_extension = os.path.splitext(file)
        return_value = self.return_value_nio

        # Run through all files
        for file_temp in self.file_list:
            
            with open(file_temp, "r") as current_file:   # Read file

                # Run through all rows
                for row in current_file:
                    
                    if ("import" in row) and (file_name in row):
                        return_value = self.return_value_io

        if return_value == self.return_value_nio:
            
            print(file, "was not imported anywhere")

        return return_value  

    def __check_asserts(self, file):
        """This method checks if asserts are present in the main block "if __name__ == "__main__":".

        Args:
            file (string): File that will be checked
        
        Returns:
            return_value (integer): Return value, is 0 if everything is ok
        """
        
        test_code = False
        return_value = self.return_value_nio
        
        with open(file, "r") as current_file:   # Read file

            # Run through all rows
            for row in current_file:
                
                if ("if" in row) and ("__name__" in row) and ("__main__" in row):
                    test_code = True
                    
                if (test_code == True) and ("assert" in row):
                    return_value = self.return_value_io
        
        if return_value == self.return_value_nio:
            
            if test_code == False:
                print("No test code found in", file)
            else:
                print("No asserts found in", file)
                
        return return_value

    def __check_main_block(self, file):
        """This method executes from the called file, the code that is written at "if __name__ == "__main__":".
        
        Args:
            file (string): File that will be checked

        Returns:
            return_value (integer): Return value, is 0 if everything is ok
        """
        
        return_value = os.system(self.python_command_name + " " + file)
    
        return return_value       
        
    def run(self):
        """This method executes the checks.
        """
        
        print("The check starts ...")
        
        self.__run_through_file_list(self.__check_pyflakes, self.skip_file_list)
        self.__run_through_file_list(self.__check_vulture, self.skip_file_list)
        self.__run_through_file_list(self.__check_file_imported_somewhere , self.skip_file_list_big)
        #self.__run_through_file_list(self.__check_asserts , self.skip_file_list_big)     
        #self.__run_through_file_list(self.__check_main_block, self.skip_file_list_big) 
        
        print("---------------------------------------------------")
        print("         All checks successfully executed!         ")
        print("---------------------------------------------------")
        

if __name__ == "__main__":

    Selftest()
    
    