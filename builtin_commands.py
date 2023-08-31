from file_system import FileNode, FilePath
import predefined_errors
from utilities import is_file_doable, is_file_ancestors_doable, string_validity_check


def cmd_exit(args: dict, system_states: dict):
    print(f"bye, {system_states['effective_user']}")
    exit()


def cmd_pwd(args: dict, system_states: dict):
    print(FilePath.from_node(system_states, system_states["pwd"]))


def cmd_cd(args: dict, system_states: dict):
    new_node_path = FilePath(system_states, args["dir"], semantical_check=True)
    # check name validity
    if not new_node_path.validity:
        raise predefined_errors.InvalidSyntax
    # check if the path is semantical
    if new_node_path.semantical_status != "success":
        raise predefined_errors.FileNotFound
    new_node = new_node_path.get_node(system_states)
    # check if the target is a directory
    if new_node.type == "file":
        raise predefined_errors.NautilusException("Destination is a file")
    # check if the effective user can EXECUTE the target directory
    if not is_file_doable("x", new_node, system_states):
        raise predefined_errors.PermissionDenied
    # change the working directory
    system_states["pwd"] = new_node

def cmd_mkdir(args: dict, system_states: dict):
    create_parents: bool = args.get("parents", False)
    file_path = FilePath(system_states, args["dir"])
    # check name validity
    if not file_path.validity:
        raise predefined_errors.InvalidSyntax
    # start from the parent
    current_node: FileNode = system_states["root"]
    # iterate each level of the file path
    for dir_name in file_path.levels:
        # find the corresponding node of the current level
        child_node: FileNode = current_node.children.get(dir_name)
        if child_node is not None:
            # point to the found file node
            current_node = child_node
        else:
            # corresponding node not found...
            if create_parents:
                # create the file node of the current level as per user instruction
                current_node = FileNode(dir_name, 0b1111101,
                               system_states["effective_user"], current_node)
            else:
                raise predefined_errors.NautilusException("Ancestor directory does not exist")
    # parent writable check
    if not is_file_doable("w", current_node, system_states):
        raise predefined_errors.PermissionDenied
    # ancestor executable check
    if not is_file_ancestors_doable("x", current_node, system_states):
        raise predefined_errors.PermissionDenied
    if file_path.get_node(system_states) is not None and not create_parents:
        raise predefined_errors.NautilusException("File exists")
    # create the required directory if all checks are passed
    if file_path.file_name is not None:
        FileNode(file_path.file_name, 0b1111101,
                system_states["effective_user"], current_node)
    else:
        raise predefined_errors.NautilusException("File exists")


def cmd_touch(args: dict, system_states: dict):
    # parse the path of the file to create
    file_path: FilePath = FilePath(system_states, args["file"])
    # check name validity
    if not file_path.validity:
        raise predefined_errors.InvalidSyntax
    # get the ancestor node of the file to create
    parent: FileNode = file_path.get_node(
        system_states, require_parent_node=True)
    # check if the ancestor node exists
    if parent is None:
        raise predefined_errors.NautilusException("Ancestor directory does not exist")
    # check if the user can WRITE and EXECUTE the parent directory
    # as well as EXECUTE all ancestor directories
    if not is_file_doable("w", parent, system_states) \
       or not is_file_doable("x", parent, system_states) \
       or not is_file_ancestors_doable("x", parent, system_states):
        raise predefined_errors.PermissionDenied
    # only do new file creation when the file to touch does not exist
    if file_path.get_node(system_states) is None:
        FileNode(file_path.file_name, 0b0110100,
                 system_states["effective_user"], parent)


def cmd_cp(args: dict, system_states: dict):
    src_path = FilePath(system_states, args["src"])
    dst_path = FilePath(system_states, args["dst"])
    # check name validity of both source path and destination path
    if not src_path.validity or not dst_path.validity:
        raise predefined_errors.InvalidSyntax
    dst_node = dst_path.get_node(system_states)
    # the destination node should not exist
    if dst_node is not None:
        if dst_node.type == "file":
            raise predefined_errors.NautilusException("File exists")
        elif dst_node.type == "directory":
            raise predefined_errors.NautilusException("Destination is a directory")
    # get the source file node by the path
    src_node = src_path.get_node(system_states)
    # source node should exist
    if src_node is None:
        raise predefined_errors.NautilusException("No such file")
    # source node should not be directory
    if src_node.type == "directory":
        raise predefined_errors.NautilusException("Source is a directory")
    # check if the effective user can READ the source node
    if not is_file_doable("r", src_node, system_states):
        raise predefined_errors.PermissionDenied
    # check if the effective user can EXECUTE the source node
    if not is_file_ancestors_doable("x", src_node, system_states):
        raise predefined_errors.PermissionDenied
    target_dir = dst_path.get_node(system_states, require_parent_node=True)
    if target_dir is None:
        raise predefined_errors.FileNotFound
    if target_dir.type != "directory":
        raise predefined_errors.FileNotFound
    # check if the user can WRITE the destination's parent node,
    # and EXECUTE the destination's ancestor nodes
    if not is_file_doable("w", target_dir, system_states) \
       or not is_file_doable("x", target_dir, system_states):
        raise predefined_errors.PermissionDenied
    if not is_file_ancestors_doable("x", target_dir, system_states):
        raise predefined_errors.PermissionDenied
    # create the copy at the specified destination path
    FileNode(dst_path.file_name, src_node.mode, src_node.owner, target_dir)


def cmd_mv(args: dict, system_states: dict):
    # mv is basically copy and then remove the source node
    cmd_cp(args, system_states)
    # source node should exist and writable
    src_path = FilePath(system_states, args["src"])
    src_node = src_path.get_node(system_states)
    # check if the source node exists
    if src_node is None:
        raise predefined_errors.NautilusException("No such file")
    # check if the source node is WRITABLE
    if not is_file_doable("w", src_node, system_states):
        raise predefined_errors.PermissionDenied
    # terminate the parent-child relationship between source node and its original parent
    src_node.parent = None


def cmd_rm(args: dict, system_states: dict):
    target_node_path = FilePath(system_states, args["path"])
    # check name validity
    if not target_node_path.validity:
        raise predefined_errors.InvalidSyntax
    target_node = target_node_path.get_node(system_states)
    # check if the target node exists
    if target_node is None:
        raise predefined_errors.NautilusException("No such file")
    # check if the target node is a file
    if target_node.type != "file":
        raise predefined_errors.NautilusException("Is a directory")
    if not is_file_doable("w", target_node, system_states) or \
       not is_file_ancestors_doable("x", target_node, system_states) or \
       not is_file_doable("w", target_node.parent, system_states):
        raise predefined_errors.PermissionDenied
    target_node.parent = None


def cmd_rmdir(args: dict, system_states: dict):
    target_dir_path = FilePath(system_states, args["dir"])
    if not target_dir_path.validity:
        raise predefined_errors.InvalidSyntax
    target_dir = target_dir_path.get_node(system_states)
    if target_dir is None:
        raise predefined_errors.FileNotFound
    if target_dir.type != "directory":
        raise predefined_errors.NautilusException("Not a directory")
    if not is_file_doable("w", target_dir.parent, system_states) or \
       not is_file_ancestors_doable("x", target_dir, system_states):
        raise predefined_errors.PermissionDenied
    if target_dir == system_states["pwd"]:
        raise predefined_errors.NautilusException("Cannot remove pwd")
    if len(target_dir.children.keys()) > 0:
        raise predefined_errors.NautilusException("Directory not empty")
    target_dir.parent = None


def cmd_chmod(args: dict, system_states: dict):
    use_recursion = args.get("recursion", False)
    # Get the target file. As a node is specified, file path is not mandatory
    target_file_path = FilePath(system_states, args["path"])
    if not target_file_path.validity:
        raise predefined_errors.InvalidSyntax
    target_file = target_file_path.get_node(system_states)
    mode_str = args["mode_string"]
    def chmod(target_file: FileNode, mode_str: str, use_recursion: bool):
        try:
            if target_file is None:
                raise predefined_errors.FileNotFound
            elif system_states["effective_user"] != "root" and system_states["effective_user"] != target_file.owner:
                raise predefined_errors.OperationNotPermitted
            elif not is_file_ancestors_doable("x", target_file, system_states):
                raise predefined_errors.PermissionDenied
            else:
                for_owner: bool = False
                for_others: bool = False
                mask = 0b0
                operator = None
                operators = ["-", "+", "="]
                uoa: list = []
                rwx: list = []
                for i, current in enumerate(mode_str):
                    if current in operators:
                        operator = current
                        uoa = list(mode_str[0:i])
                        rwx = list(mode_str[i+1:])
                        break
                # read the arguments
                if len(uoa) == 0:
                    raise predefined_errors.NautilusException("Invalid mode")
                for char in uoa:
                    if "u" == char:
                        for_owner = True
                    elif "o" == char:
                        for_others = True
                    elif "a" == char:
                        for_owner = for_others = True
                    else:
                        raise predefined_errors.NautilusException("Invalid mode")
                for char in rwx:
                    if "r" == char:
                        mask += 0b100
                    elif "w" == char:
                        mask += 0b010
                    elif "x" == char:
                        mask += 0b001
                    else:
                        raise predefined_errors.NautilusException("Invalid mode")
                # get the 6-bit permission of the target file
                perms = target_file.mode & 0b0111111
                # get the file type info by masking 6-bit permission in the mode bits
                masked_file_type = target_file.mode & 0b1000000
                if operator == "+":
                    # to add: as for a perm bit, if it's zero, it becomes one; if it's one, it remains the same
                    if for_owner:
                        perms = perms | (mask << 3)
                    if for_others:
                        perms = perms | mask
                if operator == "-":
                    # to remove: as for a perm bit, if it's one, it becomes zero; if it's zero, it remains the same
                    if for_owner:
                        perms = perms & ~(mask << 3)
                    if for_others:
                        perms = perms & ~mask
                if operator == "=":
                    # to set: set to new mask bits regardless of original bits
                    owner_perms = perms >> 3
                    others_perms = perms & 0b000111
                    if for_owner:
                        owner_perms = mask
                    if for_others:
                        others_perms = mask
                    perms = (owner_perms << 3) | others_perms
                # combine new perms with original file type back
                target_file.mode = masked_file_type | perms
        except predefined_errors.NautilusException as err:
            print("chmod: " + err.message)
        finally:
            if target_file is not None and use_recursion:
                for child_node in target_file.children.values():
                    chmod(child_node, mode_str, True)
    chmod(target_file, mode_str, use_recursion)


def cmd_adduser(args: dict, system_states: dict):
    if not string_validity_check(args["user"]):
        raise predefined_errors.InvalidSyntax
    if system_states["effective_user"] != "root":
        raise predefined_errors.OperationNotPermitted
    if args["user"] in system_states["users"]:
        raise predefined_errors.NautilusException("The user already exists")
    system_states["users"].add(args["user"])


def cmd_deluser(args: dict, system_states: dict):
    if not string_validity_check(args["user"]):
        raise predefined_errors.InvalidSyntax
    if system_states["effective_user"] != "root":
        raise predefined_errors.OperationNotPermitted
    if args["user"] not in system_states["users"]:
        raise predefined_errors.NautilusException("The user does not exist")
    if args["user"] == "root":
        print("""WARNING: You are just about to delete the root account
Usually this is never required as it may render the whole system unusable
If you really want this, call deluser with parameter --force
(but this `deluser` does not allow `--force`, haha)
Stopping now without having performed any action""")
        return
    system_states["users"].remove(args["user"])


def cmd_su(args: dict, system_states: dict):
    new_user = args.get("user", "root")
    if not string_validity_check(new_user):
        raise predefined_errors.InvalidSyntax
    if new_user in system_states["users"]:
        system_states["effective_user"] = new_user
    else:
        raise predefined_errors.NautilusException("Invalid user")


def cmd_chown(args: dict, system_states: dict):
    if system_states["effective_user"] != "root":
        raise predefined_errors.OperationNotPermitted
    if args["user"] not in system_states["users"]:
        raise predefined_errors.NautilusException("Invalid user")
    target_file_path = FilePath(system_states, args["path"])
    if not target_file_path.validity:
        raise predefined_errors.InvalidSyntax
    target_file = target_file_path.get_node(system_states)
    if target_file is None:
        raise predefined_errors.FileNotFound
    use_recursion = args.get("recursion", False)
    def chown(target_file: FileNode, new_user: str, recursion: bool):
        target_file.owner = new_user
        if recursion:
            for child_node in target_file.children.values():
                chown(child_node, new_user, True)
    chown(target_file, args["user"], use_recursion)


def cmd_ls(args: dict, system_states: dict):
    ls_requests = {}
    list_all = args.get("all", False)
    long_format = args.get("long", False)
    list_dir_itself = args.get("list_dir", False)
    path = args.get("path", ".")
    target_file: FileNode = None
    parent: FileNode = None
    if path == ".":
        target_file = system_states["pwd"]
    else:
        target_file_path = FilePath(system_states, path)
        if not target_file_path.validity:
            raise predefined_errors.InvalidSyntax
        target_file = target_file_path.get_node(system_states)
        if target_file is None:
            raise predefined_errors.FileNotFound
    if target_file.parent is not None:
        parent = target_file.parent
    else:
        parent = target_file
    if not is_file_ancestors_doable("x", target_file, system_states):
        raise predefined_errors.PermissionDenied
    if target_file.type == "directory":
        if not is_file_doable("r", target_file, system_states):
            raise predefined_errors.PermissionDenied
        if list_dir_itself:
            if not is_file_doable("r", parent, system_states):
                raise predefined_errors.PermissionDenied
            if list_all or path[0] != ".":
                ls_requests[path] = target_file
        else:
            if list_all:
                ls_requests["."] = target_file
                ls_requests[".."] = parent
            for child_name, child_node in target_file.children.items():
                if not list_all and child_name[0] == ".":
                    continue
                ls_requests[child_name] = child_node
    elif target_file.type == "file":
        if not is_file_doable("r", parent, system_states):
            raise predefined_errors.PermissionDenied
        if list_all or path[0] != ".":
            ls_requests[path] = target_file
    for name, obj in sorted(ls_requests.items()):
        char_set = ["x", "w", "r", "x", "w", "r", "d"]
        if long_format:
            for i in range(6, -1, -1):
                if (obj.mode & 1 << i) >> i:
                    print(char_set[i], end='')
                else:
                    print("-", end='')
            print(" " + obj.owner + " " + name)
        else:
            print(name)


router = {
    "exit": {
        "method": cmd_exit,
        "parameters": []
    },
    "pwd": {
        "method": cmd_pwd,
        "parameters": [],
    },
    "cd": {
        "method": cmd_cd,
        "parameters": [{
            "name": "dir",
            "type": "string"
        }],
    },
    "mkdir": {
        "method": cmd_mkdir,
        "parameters": [{
            "name": "parents",
            "type": "option",
            "indicator": "p"
        }, {
            "name": "dir",
            "type": "string",
        }]
    },
    "touch": {
        "method": cmd_touch,
        "parameters": [{
            "name": "file", "type": "string"
        }]
    },
    "cp": {
        "method": cmd_cp,
        "parameters": [{
            "name": "src", "type": "string"
        }, {
            "name": "dst", "type": "string"
        }]
    },
    "mv": {
        "method": cmd_mv,
        "parameters": [{
            "name": "src", "type": "string"
        }, {
            "name": "dst", "type": "string"
        }]
    },
    "rm": {
        "method": cmd_rm,
        "parameters": [{
            "name": "path", "type": "string"
        }]
    },
    "rmdir": {
        "method": cmd_rmdir,
        "parameters": [{
            "name": "dir", "type": "string"
        }]
    },
    "chmod": {
        "method": cmd_chmod,
        "parameters": [{
            "name": "recursion", "type": "option", "indicator": "r"
        }, {
            "name": "mode_string", "type": "string"
        }, {
            "name": "path", "type": "string"
        }]
    },
    "chown": {
        "method": cmd_chown,
        "parameters": [{
            "name": "recursion", "type": "option", "indicator": "r"
        }, {
            "name": "user", "type": "string"
        }, {
            "name": "path", "type": "string"
        }]
    },
    "adduser": {
        "method": cmd_adduser,
        "parameters": [{
            "name": "user", "type": "string"
        }]
    },
    "deluser": {
        "method": cmd_deluser,
        "parameters": [{
            "name": "user", "type": "string"
        }]
    },
    "su": {
        "method": cmd_su,
        "parameters": [{
            "name": "user", "type": "string", "optional": True
        }]
    },
    "ls": {
        "method": cmd_ls,
        "parameters": [{
            "name": "all", "type": "option", "indicator": "a"
        }, {
            "name": "list_dir", "type": "option", "indicator": "d"
        }, {
            "name": "long", "type": "option", "indicator": "l"
        }, {
            "name": "path", "type": "string", "optional": True
        }]
    }
}
