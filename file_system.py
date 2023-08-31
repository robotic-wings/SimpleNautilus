
from utilities import string_validity_check

class FileNode:
    name: str
    mode: int
    owner: str
    _parent: object
    children: dict[object]
    def __init__(self, name: str, mode: int, owner: str, parent: object):
        """Return a new node of file.
        Args:
            name (str): The name of the file.
            type (str): The identifier of the file type. It's "d" if the file is a directory;
                        it is "-" if the file is a non-directory.
            mode (int): The mode of the file, which is represented by a 7-bit binary number.
            parent: The parent node of the file, which is also an instance of the class File.
        """
        self.name = name
        self.mode = mode
        self.owner = owner
        self._parent = parent
        self.children = dict()
        if parent is not None:
            parent.children[name] = self

    @property
    def parent(self) -> object:
        return self._parent

    @parent.setter
    def parent(self, new_parent: object):
        """Specify a new parent for the file node.

        Args:
            new_parent (object): a file node, which is expected to be a directory
        """
        if self._parent is not None:
            # the original parent doesn't claim the child anymore if the node has an original parent
            self._parent.children.pop(self.name)
        if new_parent is not None:
            # establish the new parent-child relationship with the new parent
            self._parent = new_parent
            self._parent.children[self.name] = self

    @property
    def ancestors(self) -> list[object]:
        # traverse ancestors from the instant parent to root
        current_ancestor: FileNode = self._parent
        ancestors = []
        while current_ancestor is not None:
            ancestors.append(current_ancestor)
            current_ancestor = current_ancestor.parent
        return ancestors

    @property
    def type(self) -> str:
        """Get the type of the file node.

        Returns:
            str: "directory" if the file is a directory; "file" if the file is a non-directory.
        """
        # check the first bit of file mode
        is_dir = self.mode >> 6
        if is_dir:
            return "directory"
        else:
            return "file"

    @property
    def is_root(self) -> bool:
        """See if the node is a root node, for treating the root node specifically

        Returns:
            bool: True for the node is a parent
        """
        return self.name is None and self._parent is None

    def get_permission_status(self, identity: str, column: str) -> bool:
        """Get the status of a particular permission

        Args:
            identity (str): "u" for the file owner; "o" for other users.
            column (str): "r" for if readable, "w" for if writable, "x" for if executable.

        Returns:
            bool: The permission status (True if allowed; False if disallowed)
        """
        rwx_offsets = {"r": 2, "w": 1, "x": 0}
        uo_offsets = {"u": 3, "o": 0}
        offset = rwx_offsets[column] + uo_offsets[identity]
        return (self.mode & 1 << offset) != 0

class FilePath:
    levels: list[str]
    file_name: str
    semantical_status: str
    validity: bool
    def __init__(self, system_states: dict, path: str = None, semantical_check=False):
        if path is None:
            self.is_root = True
            return
        ### Step 1: Translate the user input path to an absolute path
        path_all_levels = None
        if path.startswith("/"):
            path_all_levels = path[1:].split("/")
        else:
            # translate relative path to the absolute one (but with . and ..)
            path_all_levels = path.split("/")
            pwd_path = FilePath.from_node(system_states, system_states["pwd"])
            if not pwd_path.is_root:
                path_all_levels = pwd_path.levels + \
                    [pwd_path.file_name] + path_all_levels[:]
        ### Step 2: Level names validity check (Will not force stop if invalid)
        self.validity = True
        for level in path_all_levels:
            if not string_validity_check(level):
                self.validity = False
        ### Step 3: Resolve all . and .. in the path and parse the path into FilePath object
        if not semantical_check:
            ### Step 3.1: Use "list operation approach" if semantical check is not enabled
            self.semantical_status = "unknown"
            path_all_levels_no_dot = []
            for level in path_all_levels:
                if level == "..":
                    # remove the last level if .. is found and there is any level
                    if len(path_all_levels_no_dot) > 0:
                        path_all_levels_no_dot.pop()
                elif level == "." or level == "":
                    # remain at the same level if . or empty is found
                    pass
                else:
                    # add the next level
                    path_all_levels_no_dot.append(level)
            if len(path_all_levels_no_dot) > 0:
                self.levels = path_all_levels_no_dot[0:-1]
                self.file_name = path_all_levels_no_dot[-1]
            else:
                self.is_root = True
        else:
            ### Step 3.2: Use "tree traversal" approach if semantical check is enabled
            self.semantical_status = "pending"
            current_node = system_states["root"]
            for level in path_all_levels:
                if level == "..":
                    # jump back to parent node if .. is found and current node is not root
                    if not current_node.is_root:
                        current_node = current_node.parent
                elif level == "." or level == "":
                    # remain at the same node if . or empty is found
                    pass
                elif level in current_node.children:
                    # jump to the child node if the level name is a child name of the current node
                    current_node = current_node.children[level]
                else:
                    # ERROR: the current level name cannot be found
                    # (i.e. what the path refers to doesn't exist)
                    self.semantical_status = "error"
                    break
            if self.semantical_status == "pending":
                # set semantical status to success if there is no error
                self.semantical_status = "success"
                if current_node.is_root:
                    self.is_root = True
                else:
                    self.levels = []
                    for ancestor in current_node.ancestors:
                        if not ancestor.is_root:
                            self.levels.append(ancestor.name)
                    self.levels.reverse()
                    self.file_name = current_node.name

    @classmethod
    def from_node(cls, system_states: dict, node: FileNode):
        # treat root node specifically
        if node.is_root:
            return cls(system_states)
        # get all levels of path by traversing ancestors from parent to root
        current_node: FileNode = node
        path_all_levels: list[str] = []
        while current_node.parent is not None:
            path_all_levels.append(current_node.name)
            current_node = current_node.parent
        # do the reverse because a path begins from root
        path_all_levels.reverse()
        # separate ancestor names and file name
        path_obj = cls(system_states)
        path_obj.levels = path_all_levels.copy()[0:-1]
        path_obj.file_name = path_all_levels[-1]
        # as what the path refers to can absolutely be found, semantical status is set to success
        path_obj.semantical_status = "success"
        return path_obj

    def get_node(self, system_states: dict, require_parent_node=False) -> FileNode:
        """Get a file node by its path.

        Returns:
            FileNode: returns the node object of the target file. If the target file is not found, returns None instead. 
        """
        current_node: FileNode = system_states["root"]
        if self.is_root:
            return system_states["root"]
        for dir_name in self.levels:
            if dir_name in current_node.children.keys():
                current_node = current_node.children[dir_name]
            else:
                return None
        if require_parent_node:
            return current_node
        else:
            return current_node.children.get(self.file_name)

    def __str__(self):
        if self.is_root:
            return "/"
        else:
            if len(self.levels) > 0:
                return "/" + "/".join(self.levels) + "/" + self.file_name
            else:
                return "/" + self.file_name

    @property
    def is_root(self):
        return len(self.levels) == 0 and self.file_name is None

    @is_root.setter
    def is_root(self, val):
        if val:
            self.levels = []
            self.file_name = None
