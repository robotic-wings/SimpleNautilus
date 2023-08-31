

import builtin_commands
from predefined_errors import InvalidSyntax, NautilusException

def init():
    # initalize the states of Nautilus
    system_states = {
        "users": {"root"},
        "effective_user": "root",
        "root": builtin_commands.FileNode(name=None, mode=0b1111101, owner="root", parent=None)
    }
    # set the current directory to root
    system_states["pwd"] = system_states["root"]
    return system_states

def prompt(system_states):
    print(f"{system_states['effective_user']}:\
{builtin_commands.FilePath.from_node(system_states, system_states['pwd'])}$ ", end='')

def run(user_input: str, system_states: dict):
    ### Step 1: Simple parse & safety check
    # do nothing if the user gives zero input
    if len(user_input) == 0:
        return
    # divide user input into command name and its argument string
    cmd, argstr = (user_input + " ").split(" ", 1)
    router = builtin_commands.router.get(cmd)
    # check if the specified command exists in the router
    if cmd not in builtin_commands.router:
        print(cmd + ": Command not found")
        return
    # get the router
    router_method, router_params = router["method"], router["parameters"]
    try:
        ### Step 2: Sort the human-readable parameter form of the current command into a working form
        string_params = []
        option_params = {}
        required_params_checklist = []
        str_param_counter = 0
        # iterate every field in the parameter form (template)
        for param in router_params:
            # categorize parameters into string parameters and options
            if param["type"] == "option":
                # map the indicator of the option with the name of the option
                option_params[param["indicator"]] = param["name"]
            elif param["type"] == "string":
                # arrange the string parameters as per the position in the template
                string_params.append(param["name"])
                # add the string parameter in required parameter checklist if its mandatory
                if not "optional" in param:
                    required_params_checklist.append(param["name"])
        ### Step 3: Resolve the argument string
        def resolve(argument: str) -> tuple:
            # ALL POSSIBLE STATES:
            # ready - Not reading anything but ready to switch to other states
            # option - Reading an option
            # quoted_string - Reading a string that is surrounded by double quotes
            # string - Reading a string that is not surrounded by double quotes
            # expect_space - Must read one space character, or run into error
            # end - At the end of argument string without any error; No reading anymore
            # Initialise the finite state machine
            current_pos = 0
            start_pos = -1
            resolved_elements = []
            current_state = "ready"
            # Define a procedure that makes a transition from the current state to another state
            def shift_state(new_state: str, start_pos_offset: int = 0):
                nonlocal current_pos, start_pos, current_state, resolved_elements
                if start_pos >= 0:
                    resolved_elements.append(
                        (current_state, argument[start_pos + start_pos_offset: current_pos]))
                current_state = new_state
                start_pos = current_pos
            # Step 1: Traverse and parse the argument string from start to end
            while current_pos < len(argument):
                current_char = argument[current_pos]
                if current_state == "ready":
                    # start reading an option
                    if current_char == "-":
                        shift_state("option")
                    # start reading a quoted string
                    elif current_char == '"':
                        shift_state("quoted_string")
                    # allows user to insert more than one space between parameters
                    elif current_char == " ":
                        pass
                    # start reading a unquoted string
                    else:
                        shift_state("string")
                elif current_state == "option":
                    # stop reading the option
                    if current_char == " ":
                        shift_state("ready", 1)
                elif current_state == "string":
                    # stop reading the unquoted string
                    if current_char == " ":
                        shift_state("ready")
                        continue
                elif current_state == "quoted_string":
                    # stop reading the quoted string, and requires a space after the ending double quote character
                    if current_char == '"':
                        shift_state("expect_space", 1)
                elif current_state == "expect_space":
                    # return to ready state if the space occurs as expected
                    if current_char == " ":
                        shift_state("ready", 1)
                    else:
                        break
                current_pos += 1
            if current_state == "expect_space":
                # ERROR: Unexpected character after the quoted string
                raise InvalidSyntax
            elif current_state == "quoted_string":
                # ERROR: String literal is unterminated
                raise InvalidSyntax
            elif current_state == "option":
                # ending normally with stopping reading the option
                shift_state("end", 1)
            elif current_state == "string":
                # ending normally with stopping reading the unquoted string
                shift_state("end")
            elif current_state == "ready":
                # ending normally without stopping reading anything
                shift_state("end")
            return resolved_elements
        # elems is the parsed argument string
        elems: tuple = resolve(argstr)
        # args is a dict that maps argument values with argument names
        args: dict = {}
        for (state, capture) in elems:
            if state == "option":
                # check if the specified option is never registered in the router
                if capture in option_params:
                    # if yes, map the option name with True
                    param_name = option_params[capture]
                    args[param_name] = True
                else:
                    raise InvalidSyntax
            elif state == "quoted_string" or state == "string":
                if str_param_counter < len(string_params):
                    param_name = string_params[str_param_counter]
                    # map the parameter name with string value
                    args[param_name] = capture
                    str_param_counter += 1
                    # check the string parameter if it's mandatory
                    if param_name in required_params_checklist:
                        required_params_checklist.remove(param_name)
                else:
                    # raise invalid syntax if there are too many (string) arguments
                    raise InvalidSyntax
        # check if all mandatory string fields are filled
        if len(required_params_checklist) > 0:
            # ERROR: too few arguments
            raise InvalidSyntax
        ### Step 4: Execute the command
        router_method(args, system_states)
    except NautilusException as err:
        print(cmd + ": " + err.message)

def main():
    system_states = init()
    # Nautilus starts working
    while True:
        # display prompt message and ask for user input
        prompt(system_states)
        user_input = input().strip()
        run(user_input, system_states)

if __name__ == '__main__':
    main()
