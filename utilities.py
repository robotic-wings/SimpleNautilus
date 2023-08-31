'''
Name: Kefan Liu
UniKey: kliu9014
SID: 500135385
'''

def is_file_doable(perm_bit: str, file: object, system_states: dict) -> bool:
    """Check if the effective user can do a particular thing to a file.

    Args:
        perm_bit (str): "r" for read, "w" for write, "x" for execute
        node (FileNode): The node of specified file
        system_states (dict): The address of the set of system states
    """
    # the superuser can do anything she wants
    if system_states["effective_user"] == "root":
        return True
    if system_states["effective_user"] == file.owner:
        # return owner permission status
        return file.get_permission_status("u", perm_bit)
    else:
        # return otheruser permission status
        return file.get_permission_status("o", perm_bit)


def is_file_ancestors_doable(perm_bit: str, file: object, system_states: dict) -> bool:
    if system_states["effective_user"] == "root":
        return True
    for ancestor in file.ancestors:
        if not is_file_doable(perm_bit, ancestor, system_states):
            return False
    return True

def string_validity_check(text: str) -> bool:
    """Check the validity of a username, directory name or file name.

    Args:
        text (str): The name to check

    Returns:
        bool: True for valid, False for invalid.
    """
    for char in text:
        if not char.isalpha() and not char.isdigit() \
        and not char == " " and not char == "-" and not char == "." and not char == "_":
            return False
    return True
