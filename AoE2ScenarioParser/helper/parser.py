import time
from typing import Any, List, TYPE_CHECKING

from AoE2ScenarioParser.helper.bytes_to_x import *
from AoE2ScenarioParser.helper.generator import repeat_generator
from AoE2ScenarioParser.helper.retriever import Retriever, get_retriever_by_name
from AoE2ScenarioParser.helper.retriever_dependency import DependencyAction

if TYPE_CHECKING:
    from AoE2ScenarioParser.pieces.structs.aoe2_struct import AoE2Struct

types = [
    "s",  # Signed int
    "u",  # Unsigned int
    "f",  # FloatingPoint
    "c",  # Character string
    "str",  # Variable length string
    "data",  # Data (Can be changed by used using bytes_to_x functions)
]
attributes = ['on_refresh', 'on_construct', 'on_commit']


def vorl(var: Any, retriever: Retriever = None):
    """vorl stands for "Variable or List". This function returns the value if the list is a size of 1"""
    if Retriever is not None and retriever.possibly_list:
        dependencies = []
        for attribute in attributes:
            if hasattr(retriever, attribute):
                dependencies += listify(getattr(retriever, attribute))
                if retriever.datatype.repeat != 1 or \
                        DependencyAction.SET_REPEAT in [x.dependency_type for x in dependencies]:
                    return listify(var)
    if type(var) is list:
        if len(var) == 1:
            return var[0]
    return var


def listify(var) -> list:
    """Always return item as list"""
    if type(var) is list:
        return var
    else:
        return [var]


def retrieve_value(generator, retriever, retrievers=None, pieces=None) -> Any:
    var_type, var_len = datatype_to_type_length(retriever.datatype.var)
    result = list()
    length = 0

    if hasattr(retriever, 'on_construct'):
        handle_retriever_dependency(retriever, retrievers, "construct", pieces)

    try:
        for i in range(0, retriever.datatype.repeat):
            length += var_len

            if var_type == "struct":
                # Todo: Find a way to store structs (different json file?) and find a way to instantiate them somewhere
                val: AoE2Struct = retriever.datatype.var()
                result.append(val)
                length += val.set_data_from_generator(generator, pieces)
                continue
            if var_type == "u" or var_type == "s":
                val = bytes_to_int(repeat_generator(generator, var_len), signed=(var_type == "s"))
            elif var_type == "f":
                if var_len == 4:  # Float value
                    val = bytes_to_float(repeat_generator(generator, var_len))
                else:  # only 'else' is the trigger version. Which is a double (8 bytes)
                    val = bytes_to_double(repeat_generator(generator, var_len))
            elif var_type == "c":
                val = bytes_to_fixed_chars(repeat_generator(generator, var_len))
            elif var_type == "data":
                val = repeat_generator(
                    generator, var_len,
                    intended_stop_iteration=(retriever.name == "__END_OF_FILE_MARK__")
                )
            elif var_type == "str":
                string_length = bytes_to_int(repeat_generator(generator, var_len), endian="little", signed=True)
                try:
                    data = repeat_generator(generator, string_length)
                    val = bytes_to_str(data)
                    length += string_length
                except StopIteration as e:
                    print(f"\n[StopIteration] Parser.retrieve_value: \n"
                          f"\tRetriever: {retriever}\n"
                          f"\tString length: {string_length}\n")
                    raise e
            else:
                break
            result.append(val)
    except StopIteration as e:
        if retriever.name == "__END_OF_FILE_MARK__":
            retriever.datatype.repeat = 0
            return True, None, None
        else:
            raise e
    except Exception as e:
        return vorl(result, retriever), length, e

    # TODO: REMOVE THIS AFTER TRUE VERSION SUPPORT
    if retriever.name == "version" and retriever.datatype.var == "c4":
        version = vorl(result, retriever)
        if version != "1.40":
            print("\n\n")
            print('\n'.join([
                "#### SORRY FOR THE INCONVENIENCE ####",
                "Scenarios that are not converted to the latest version of the game (Update 42848) are not "
                "supported at this time.",
                f"Your current version is: '{version}'. The currently only supported version is: '1.40'.",
                "The reason for this is a huge rework for version support.",
                "This rework will take some time to complete, so until then, please upgrade your scenario to the "
                "newest version. You can do this by saving it again in the in-game editor.",
                "If you do not want to upgrade the scenarios, please downgrade this library to version 0.0.11. You "
                "can do so by executing the following command in cmd:",
                "",
                ">>> pip install --force-reinstall AoE2ScenarioParser==0.0.11",
                "",
                "Thank you in advance."
            ]))
            time.sleep(1)
            print("- KSneijders")
            print("\n\n")
            time.sleep(1)
            raise ValueError("Currently unsupported version. Please read the message above. Thank you.")
    elif retriever.name == "__END_OF_FILE_MARK__":
        result = b''
        try:
            while True:
                result += next(generator)
        except StopIteration:
            pass
        print("\n\n" + "\n".join([
            "The file being read has more bytes than anticipated.",
            "Please notify me (MrKirby/KSneijders) about this message!",
            "This will help with understanding more parts of scenario files! Thanks in advance!",
            "You can contact me using:",
            "- Discord: MrKirby#5063",
            "- Github: https://github.com/KSneijders/AoE2ScenarioParser/issues",
            "",
            "Please be so kind and include the map in question. Thanks again!\n\n",
            "",
            "Extra data found in the file:",
            f"\t'{result}'"
        ]))
        retriever.datatype.repeat = 1
        return result, None, None

    return vorl(result, retriever), length, None


def handle_retriever_dependency(retriever: Retriever, retrievers: List[Retriever], state, pieces):
    if state == "construct":
        retriever_on_x = retriever.on_construct
    elif state == "commit":
        retriever_on_x = retriever.on_commit
    elif state == "refresh":
        retriever_on_x = retriever.on_refresh
    else:
        raise ValueError("State must be any of: construct, commit or refresh")

    retriever_on_x_list = listify(retriever_on_x)
    for retriever_on_x in retriever_on_x_list:
        dep_action = retriever_on_x.dependency_type
        dep_target = retriever_on_x.dependency_target
        if dep_action == DependencyAction.REFRESH_SELF:
            handle_retriever_dependency(retriever, retrievers, "refresh", pieces)
        elif dep_action == DependencyAction.REFRESH:
            listified_target = listify(dep_target.target_piece)
            listified_target_attr = listify(dep_target.piece_attr_name)
            for i in range(len(listified_target)):
                retriever_list = handle_dependency_target(listified_target[i], retrievers, pieces)
                retriever_to_be_refreshed = get_retriever_by_name(retriever_list, listified_target_attr[i])
                handle_retriever_dependency(retriever_to_be_refreshed, retriever_list, "refresh", pieces)
        elif dep_action in [DependencyAction.SET_VALUE, DependencyAction.SET_REPEAT]:
            listified_target = listify(dep_target.target_piece)
            listified_target_attr = listify(dep_target.piece_attr_name)
            for i in range(len(listified_target)):
                retriever_list = handle_dependency_target(listified_target[i], retrievers, pieces)
                retriever_data = get_retriever_by_name(retriever_list, listified_target_attr[i]).data
                value = handle_dependency_eval(retriever_on_x, retriever_data)
                if dep_action == DependencyAction.SET_VALUE:
                    retriever.data = value
                elif dep_action == DependencyAction.SET_REPEAT:
                    retriever.datatype.repeat = value


def handle_dependency_target(target_piece, retrievers, pieces):
    if target_piece == "self":
        retriever_list = retrievers
    else:
        retriever_list = eval("pieces[x].retrievers", {}, {
            'pieces': pieces,
            'x': target_piece
        })
    return retriever_list


def handle_dependency_eval(retriever_on_x, value):
    eval_locals = retriever_on_x.dependency_eval.eval_locals
    values_as_variable = retriever_on_x.dependency_eval.values_as_variable
    # If value as is used, use it as keys for the value!
    if values_as_variable:
        eval_locals = {**eval_locals, **dict(zip(values_as_variable, value))}
    else:
        eval_locals['x'] = value
    return eval(retriever_on_x.dependency_eval.eval_code, {}, eval_locals)


def datatype_to_type_length(var):
    """Returns the type and length of a datatype. So: 'int32' returns 'int', 32. """
    if var[:7] == "struct:":
        return "struct", 0

    # Filter numbers out for length, filter text for type
    var_len = int(''.join(filter(str.isnumeric, var)))
    var_type = ''.join(filter(str.isalpha, var))

    if var_type == '':
        var_type = "data"

    if var_type not in types:
        raise ValueError(f"Unknown variable type '{var_type}'")

    # Divide by 8, and parse from float to int
    if var_type not in ["c", "data"]:
        var_len = int(var_len / 8)

    return var_type, var_len


def retriever_to_bytes(retriever, pieces):
    var_type, var_len = datatype_to_type_length(retriever.datatype.var)
    return_bytes = b''

    is_list = type(retriever.data) == list
    if is_list:
        retriever.datatype.repeat = len(retriever.data)

    try:
        for i in range(0, retriever.datatype.repeat):
            data = retriever.data[i] if is_list else retriever.data

            if data is None:
                # No data is found in struct. Reasoning described below.
                return None

            if var_type == "struct":
                for struct_retriever in data.retrievers:
                    result = retriever_to_bytes(struct_retriever, pieces)
                    if result is None:
                        # Return default value. When non is committed.
                        # Should only happen when a value is not transferred from and to a struct.
                        # This is because structs are recreated on file generation. When the struct does not contain
                        # a certain value because it's use is unknown, the value isn't transferred between.
                        struct_retriever.data = retriever.datatype.var.defaults(pieces)[struct_retriever.name]
                        return_bytes += retriever_to_bytes(struct_retriever, pieces)
                        continue
                    return_bytes += result
            if var_type == "u" or var_type == "s":  # int
                return_bytes += int_to_bytes(data, var_len, signed=(var_type == "s"))
            elif var_type == "f":  # float
                if var_len == 4:
                    return_bytes += float_to_bytes(data)
                else:
                    return_bytes += double_to_bytes(data)
            elif var_type == "c":  # str
                return_bytes += fixed_chars_to_bytes(data)
            elif var_type == "data":  # bytes
                return_bytes += data
            elif var_type == "str":  # str
                byte_string = str_to_bytes(data, retriever)
                return_bytes += int_to_bytes(len(byte_string), var_len, endian="little", signed=True)
                return_bytes += byte_string
    except (AttributeError, TypeError) as e:
        data_text = repr(retriever.data)
        if type(retriever.data) == list and len(retriever.data) > 5:
            data_text = f"[{retriever.data[0].__class__.__name__}] * {len(retriever.data)}"

        print(f"\n{type(e).__name__} occurred in: {retriever.name} "
              f"\n\tData: {data_text}"
              f"\n\tDatatype: {str(retriever.datatype)}")
        raise e

    if retriever.log_value:
        print(retriever, "returned", return_bytes)

    return return_bytes
