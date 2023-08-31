# Bash Simulator in Python

## Overview

This Bash Simulator is a Python-based application that mimics the functionalities of a Unix/Linux shell. It provides a wide range of built-in commands for file and directory manipulation, user management, and system information queries. The simulator is designed to be comprehensive and includes permission handling features.

## Features

- **File and Directory Operations**: Create (`mkdir`, `touch`), copy (`cp`), move (`mv`), and delete (`rm`, `rmdir`) files and directories.
  
- **User Management**: Add (`adduser`), delete (`deluser`), and switch (`su`) users.

- **System Information**: Display the current working directory (`pwd`) and list directory contents (`ls`).

- **Permission Handling**: Change file permissions (`chmod`) and ownership (`chown`).

## Requirements

- Python 3.x

## Installation

1. Clone the repository
   ```
   git clone https://github.com/your-repo/Bash-Simulator-in-Python.git
   ```
2. Navigate to the project directory
   ```
   cd Bash-Simulator-in-Python
   ```
3. Run the program
   ```
   python main.py
   ```

## Usage

Here are some example usages of the built-in commands:

- To change the current directory:
  ```
  cd /path/to/directory
  ```
  
- To create a new directory:
  ```
  mkdir new_directory
  ```
  
- To create a new file:
  ```
  touch new_file.txt
  ```
  
- To copy a file:
  ```
  cp source_file.txt destination_file.txt
  ```
  
- To move a file:
  ```
  mv old_location.txt new_location.txt
  ```
  
- To remove a file:
  ```
  rm file_to_remove.txt
  ```
  
- To list the contents of a directory:
  ```
  ls
  ```
  
- To add a new user:
  ```
  adduser username
  ```
  
- To switch to another user:
  ```
  su username
  ```

## Contributing

If you'd like to contribute, please fork the repository and make changes as you'd like. Pull requests are warmly welcome.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
