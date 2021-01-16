# -*- coding: utf-8 -*-
"""Utility module for classes and functions that pertain to:
    * file, and filename handling
    * temporary directory, and temporary file handling
    * Logging
    * Wrapper class for UNIX command line executables.

Todo:
    * Add gzipping/gunzipping functions to File class
        * See these links:
            * https://stackoverflow.com/questions/8156707/gzip-a-file-in-python
            * https://github.com/AdebayoBraimah/convert_source/blob/36382a97aca380c69b44083abefe6efba74699da/convert_source/utils.py#L114
        * Add option to use native gzipping if available
    * Type all initial apprearances of arguments/variables
    * Update/refactor logging class to logging decorator
    * Add List, and Dict to type hints for classes/functions

"""

# Import modules/packages
import subprocess
import logging
import os
import random
import shutil
import platform
from typing import Optional, Union, Tuple

# Define classes
class DependencyError(Exception):
    pass

class File(object):
    '''Creates File object that encapsulates a number of methods and properites
    for file and filename handling.
    
    Attributes (class and instance attributes):
        file (class and instance): Class variable that is set once class is instantiated.
    '''
    
    file: str = ""
    
    def __init__(self,
                 file: str,
                 ext: str = "") -> None:
        '''Init doc-string for File object class.
        
        Usage example:
            >>> file_obj = File("file_name.txt")
            >>> file_obj.file 
            "file_name.txt"

        Args:
            file: Input file (need not exist at runtime/instantiated).
            ext: File extension of input file. If no extension is provided, it
                is inferred.
        '''
        self.file: str = file
        if ext:
            self.ext: str = ext
        elif '.gz' in self.file:
            self.ext: str = self.file[-(7):]
        else:
            self.ext: str = self.file[-(4):]
        
    def touch(self) -> None:
        '''Creates empty file.
        
        Usage example:
            >>> file_obj = File("file_name.txt")
            >>> file_obj.touch()   # Creates empty file
        '''
        with open(self.file,'w') as tmp_file:
            pass
        return None
    
    def abs_path(self) -> str:
        '''Returns absolute path of file.
        
        Usage example:
            >>> file_obj = File("file_name.txt")
            >>> file_obj.abs_path()
            "abspath/to/file_namt.txt"
        '''
        if os.path.exists(self.file):
            return os.path.abspath(self.file)
        else:
            self.touch()
            file_path = os.path.abspath(self.file)
            os.remove(self.file)
            return file_path
    
    def rm_ext(self,
              ext: str = "") -> str:
        '''Removes file extension from the file.
        
        Usage example:
            >>> file_obj = File("file_name.txt")
            >>> file_obj.rm_ext() 
            "file_name"
        
        Args:
            ext: File extension.
        
        Returns:
            file: File name with no extension.
        '''
        if ext:
            ext_num: int = len(ext)
            return self.file[:-(ext_num)]
        elif self.ext:
            ext_num = len(self.ext)
            return self.file[:-(ext_num)]
        else:
            return self.file[:-(4)]
        
    def write_txt(self,
                 txt: str = "") -> None:
        '''Writes/appends text to file.
        
        Usage example:
            >>> file_obj = File("file_name.txt")
            >>> file_obj.write_txt("<Text to be written>")
        
        Args:
            txt: Text to be written to file.

        Returns:
            file: File with text written/appended to it.
        '''
        with open(self.file,"a") as tmp_file:
            tmp_file.write(txt)
            tmp_file.close()
        return None

    def file_parts(self,
                  ext: str = "") -> Tuple[str,str,str]:
        '''Splits a file and its path into its constituent 
        parts:
            * file path
            * filename
            * extension
        
        Usage example:
            >>> file_obj = File("file_name.txt")
            >>> file_obj.file_parts()
            ("path/to/file", "filename", ".ext")   # .ext = file extension
        
        Args:
            ext: File extension, needed if the file extension of file 
                object is longer than 4 characters.
        
        Returns:
            path: Absolute file path, excluding filename.
            filename: Filename, excluding extension.
            ext: File extension.
        '''
        
        file: str = self.file
        file = self.abs_path()
        
        if platform.system().lower() == "windows":
            [path, _filename] = os.path.splitdrive(file)
        else:
            [path, _filename] = os.path.split(file)
        
        if ext:
            ext_num = len(ext)
            _filename = _filename[:-(ext_num)]
            [filename, _ext] = os.path.splitext(_filename)
        elif self.ext:
            ext = self.ext
            ext_num = len(ext)
            _filename = _filename[:-(ext_num)]
            [filename, _ext] = os.path.splitext(_filename)
        else:
            [filename, ext] = os.path.splitext(_filename)
        
        return path, filename, ext

class TmpDir(object):
    '''Temporary directory class that creates temporary directories and files
    given a parent directory.
    
    Attributes (class and instance attributes):
        tmp_dir (class and instance): Temproary directory.
        parent_tmp_dir (class and instance): Input parent directory.
    '''
    
    # Set parent tmp directory, as tmp_dir is overwritten
    tmp_dir: str = ""
    parent_tmp_dir: str = ""
    
    def __init__(self,
                tmp_dir: str,
                use_cwd: bool = False) -> None:
        '''Init doc-string for TmpDir class.
        
        Usage example:
            >>> tmp_directory = TmpDir("/path/to/temporary_directory")
            >>> tmp_directory.tmp_dir() 
        
        Args:
            tmp_dir: Temporary parent directory name/path.
            use_cwd: Use current working directory as working direcory.
        '''
        _n: int = 10000 # maximum N for random number generator
        tmp_dir: str = os.path.join(tmp_dir,'tmp_dir_' + 
                               str(random.randint(0,_n)))
        self.tmp_dir: str = tmp_dir
        self.parent_tmp_dir: str = os.path.dirname(self.tmp_dir)
        if use_cwd:
            _cwd = os.getcwd()
            self.tmp_dir = os.path.join(_cwd,self.tmp_dir)
            self.parent_tmp_dir = os.path.dirname(self.tmp_dir)
        
    def mk_tmp_dir(self) -> None:
        '''Creates/makes temporary directory.
        
        Usage example:
            >>> tmp_directory = TmpDir("/path/to/temporary_directory")
            >>> tmp_directory.mk_tmp_dir()
        '''
        if not os.path.exists(self.tmp_dir):
            return os.makedirs(self.tmp_dir)
        else:
            print("Temporary directory already exists")
        
    def rm_tmp_dir(self,
                  rm_parent: bool = False) -> None:
        '''Removes temporary directory.
        
        Usage example:
            >>> tmp_directory = TmpDir("/path/to/temporary_directory")
            >>> tmp_directory.rm_tmp_dir() 
        
        Args:
            rm_parent: Removes parent directory as well.
        '''
        if rm_parent and os.path.exists(self.parent_tmp_dir):
            return shutil.rmtree(self.parent_tmp_dir)
        elif os.path.exists(self.tmp_dir):
            return shutil.rmtree(self.tmp_dir)
        else:
            print("Temporary directory does not exist")
    
    class TmpFile(File):
        '''Child/sub-class of TmpDir. Creates temporary files by inheriting File object
        methods and properties from the File class.
        
        Attributes (class and instance attributes):
            tmp_file (class and instance): Temporary file name.
            tmp_dir (class and instance): Temporary directory name.
        '''
        
        tmp_file: File = ""
        tmp_dir: str = ""

        def __init__(self,
                    tmp_file: File,
                    tmp_dir: str = "") -> None:
            '''Init doc-string for TmpFile class. Allows for creation of 
            a temporary file in parent class' temporary directory location.
            TmpFile also inherits methods from the File class.
            
            Usage example:
                >>> tmp_directory = TmpDir("/path/to/temporary_directory")
                >>> temp_file = TmpDir.TmpFile("temporary_file", tmp_directory.tmp_dir)
                >>> temp_file.tmp_file
                "/path/to/temporary_directory/temporary_file"
            
            Args:
                tmp_file: Temporary file name.
                tmp_dir: Temporary directory name.
            '''
            self.tmp_file: str = tmp_file
            self.tmp_dir = tmp_dir
            self.tmp_file = os.path.join(self.tmp_dir,self.tmp_file)
            File.__init__(self,self.tmp_file)

class NiiFile(File):
    '''NIFTI file class object for handling NIFTI files. Inherits methods and 
    properties from the File class.
    
    Attributes (class and instance attributes):
        file (class and instance): NIFTI file path.
    '''
    def __init__(self,
                 file: File) -> None:
        '''Init doc-string for NiiFile class.
        
        Usage example:
            >>> nii_file = NiiFile("file.nii")
            >>> nii_file.file 
            "file.nii"
        '''
        self.file = file
        File.__init__(self,self.file)


class LogFile(File):
    '''Class that creates a log file for logging purposes. Due to how this 
    class is constructed - its intended use case requires that this class 
    is instantiated/called once and ONLY once.
    
    Once a class instance has been instantiated, then it and its associated
    methods can be used.
    
    Attributes (class and instance attributes):
        log_file: Log file filename.
    '''
    
    def __init__(self,
                 log_file: str = "") -> None:
        '''Init doc-string for LogFile class. Initiates logging and its 
        associated methods.
        
        Usage examples:
            >>> log = LogFile("file.log")
            >>> log.file 
            "file.log"
        
        Args:
            file: Log filename (need not exist at runtime).
        '''
        self.log_file: str = log_file
        
        # Set-up logging to file
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%d-%m-%y %H:%M:%S',
                            filename=self.log_file,
                            filemode='a')
        
        # Define a Handler which writes INFO messages or higher to the sys.stderr
        self.console = logging.StreamHandler()
        self.console.setLevel(logging.INFO)
        
        # Add the handler to the root logger
        logging.getLogger().addHandler(self.console)
        
        # Define logging
        self.logger = logging.getLogger(__name__)
        
    def info(self,
            msg: str = "") -> None:
        '''Writes information to log file.
        
        Usage examples:
            >>> log = LogFile("file.log")
            >>> log.info("<str>")
        
        Args:
            msg: String to be printed to log file.
        '''
        self.logger.info(msg)
        
    def debug(self,
            msg: str = "") -> None:
        '''Writes debug information to file.
        
        Usage examples:
            >>> log = LogFile("file.log")
            >>> log.debug("<str>")
        
        Args:
            msg: String to be printed to log file.
        '''
        self.logger.debug(msg)
        
    def error(self,
            msg: str = "") -> None:
        '''Writes error information to file.
        
        Usage examples:
            >>> log = LogFile("file.log")
            >>> log.error("<str>")
        
        Args:
            msg: String to be printed to log file.
        '''
        self.logger.error(msg)
        
    def warning(self,
            msg: str = "") -> None:
        '''Writes warnings to file.
        
        Usage examples:
            >>> log = LogFile("file.log")
            >>> log.warning("<str>")
        
        Args:
            msg: String to be printed to log file.
        '''
        self.logger.warning(msg)
    
    def log(self,
        log_cmd: str = "") -> None:
        '''Log function for logging commands and messages to some log file.
        
        Usage examples:
            >>> log = LogFile("file.log")
            >>> log.log("<str>")
            
        Args:
            log_cmd: Message to be written to log file
        '''

        # Log command/message
        self.info(log_cmd)

class Command(object):
    '''Creates a command and an empty command list for UNIX command line programs/applications. Primary use and
    use-cases are intended for the subprocess module and its associated classes (i.e. Popen/call/run).
    
    Attributes (class and instance attributes):
        command (instance): Command to be performed on the command line.
        cmd_list (instance): Mutable list that can be appended to.
    '''

    def __init__(self,
                 command: str) -> list:
        '''Init doc-string for Command class. Initializes a command to be used on UNIX command line.
        The input argument is a command (string), and a mutable list is returned (, that can later
        be appended to).
        
        Usage example:
            >>> echo = Command("echo")
            >>> echo.cmd_list.append("Hi!")
            >>> echo.cmd_list.append("I have arrived!")
        
        Arguments:
            command: Command to be used. Note: command used must be in system path
        
        Returns:
            cmd_list: Mutable list that can be appended to.
        '''
        self.command = command
        self.cmd_list = [f"{self.command}"]
        
    def check_dependency(self,
                         err_msg: Optional[str] = None) -> Union[bool,None]:
        '''Checks dependency of some command line executable. Should the 
        dependency not be met, then an exception is raised. Check the 
        system path should problems arise and ensure that the executable
        of interest is installed.
        
        Usage example:
            >>> figlet = Command("figlet")
            >>> figlet.check_dependency()   # Raises exception if not in system path
        
        Args:
            err_msg: Error message to print to screen.

        Returns:
            Returns True if dependency is met.
        
        Raises:
            DependencyError: Dependency error exception is raised if the dependency
                is not met.
        '''
        if not shutil.which(self.command):
            if err_msg:
                print(f"\n \t {err_msg} \n")
            else:
                print(f"\n \t The required dependency {self.command} is not installed or in the system path. \n")
            raise DependencyError("Command executable not found in system path.")
        else:
            return True
        
    def run(self,
            log: LogFile = "",
            debug: bool = False,
            dryrun: bool = False,
            env: dict = {},
            stdout: File = "",
            shell: bool = False
           ) -> Tuple[int,File,File]:
        '''Uses python's built-in subprocess class to execute (run) a command from an input command list.
        The standard output and error can optionally be written to file.
        
        NOTE: The contents of the 'stdout' output file will be empty if 'shell' is set to True.
        
        Usage example:
            >>> # Create command and cmd_list
            >>> echo = Command("echo")
            >>> echo.cmd_list.append("Hi!")
            >>> echo.cmd_list.append("I have arrived!")
            
            >>> # Run/execute command
            >>> echo.run()
            (0, '', '')
        
        Args:
            log: LogFile object
            debug: Sets logging function verbosity to DEBUG level
            dryrun: Dry run -- does not run task. Command is recorded to log file.
            env: Dictionary of environment variables to add to subshell.
            stdout: Output file to write standard output to.
            shell: Use shell to execute command.
            
        Returns:
            p.returncode: Return code for command execution should the 'log_file' option be used.
            stdout: Standard output writtent to file should the 'stdout' option be used.
            stderr: Standard error writtent to file should the 'stdout' option be used.
        '''
        
        # Create command str for log
        cmd: str = ' '.join(self.cmd_list) # Join list for logging purposes
        
        if log:
            if debug:
                log.debug(f"Running: {cmd}")
            else:
                log.info(f"Running: {cmd}")
        
        if log:
            if dryrun:
                log.info("Performing command as dryrun")
                return (0,'','')
        
        # Define environment variables
        merged_env: dict = os.environ
        if env:
            merged_env.update(env)
        
        # Execute/run command
        p = subprocess.Popen(self.cmd_list,shell=shell,env=merged_env,
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        # Write log files
        out,err = p.communicate()
        out = out.decode('utf-8')
        err = err.decode('utf-8')

        # Write std output/error files
        if stdout:
            stderr: str = os.path.splitext(stdout)[0] + ".err"
                
            stdout: File = File(stdout)
            stderr: File = File(stderr)
            
            stdout.write_txt(out)
            stderr.write_txt(err)
        else:
            stdout = None
            stderr = None

        if p.returncode:
            if log:
                log.error(f"command: {cmd} \n Failed with returncode {p.returncode}")
            else:
                print(f"command: {cmd} \n Failed with returncode {p.returncode}")

        if len(out) > 0:
            if log:
                if debug:
                    log.debug(out)
                else:
                    log.info(out)

        if len(err) > 0:
            if log:
                if debug:
                    log.info(err)
                else:
                    log.warning(err)
            else:
                print(f"ERROR: {err}")
        return p.returncode,stdout,stderr
