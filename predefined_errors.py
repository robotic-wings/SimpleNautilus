'''
Name: Kefan Liu
UniKey: kliu9014
SID: 500135385
'''

class NautilusException(Exception):
    def __init__(self, err_description: str):
        self.message = err_description
        super().__init__(self.message)

class InvalidSyntax(NautilusException):
    def __init__(self):
        super().__init__("Invalid syntax")

class FileNotFound(NautilusException):
    def __init__(self):
        super().__init__("No such file or directory")

class OperationNotPermitted(NautilusException):
    def __init__(self):
        super().__init__("Operation not permitted")

class PermissionDenied(NautilusException):
    def __init__(self):
        super().__init__("Permission denied")


