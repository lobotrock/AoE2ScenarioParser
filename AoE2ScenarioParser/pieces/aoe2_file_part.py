from typing import Dict, TYPE_CHECKING

from AoE2ScenarioParser.helper import parser, helper
from AoE2ScenarioParser.helper.datatype import DataType
from AoE2ScenarioParser.helper.retriever import get_retriever_by_name, Retriever

if TYPE_CHECKING:
    from AoE2ScenarioParser.pieces.structs.aoe2_struct import AoE2StructModel


class AoE2FilePart:
    dependencies = {}

    def __init__(self, name, retrievers):
        self.name = name
        self.retrievers = retrievers
        self.byte_length = -1
        self.struct_models: Dict[str, AoE2StructModel] = {}

        for retriever in retrievers:
            if retriever.name in self.__class__.dependencies.keys():
                for key, value in self.__class__.dependencies[retriever.name].items():
                    setattr(retriever, key, value)

    @classmethod
    def from_structure(cls, piece_name, structure):
        retrievers = []
        for name, attr in structure.get('retrievers', {}).items():
            datatype = DataType(var=attr.get('type'), repeat=attr.get('repeat', 1))
            retrievers.append(Retriever(
                name=name,
                datatype=datatype
            ))
        return cls(piece_name, retrievers)

    @classmethod
    def from_data(cls, name, retrievers, data, pieces):
        part = cls(name, retrievers)
        part.set_data(data, pieces)
        return cls

    def __getattr__(self, item):
        """Providing a default way to access retriever data labeled 'name'"""
        if 'retrievers' not in self.__dict__:
            return super().__getattribute__(item)
        else:
            retriever = get_retriever_by_name(self.retrievers, item)
            if retriever is None:
                return super().__getattribute__(item)
            else:
                return retriever.data

    def __setattr__(self, name, value):
        """Trying to edit retriever data labeled 'name' if available"""
        if 'retrievers' not in self.__dict__:
            super().__setattr__(name, value)
        else:
            retriever = get_retriever_by_name(self.retrievers, name)
            if retriever is None:
                super().__setattr__(name, value)
            else:
                retriever.data = value

    def set_data_from_generator(self, generator, pieces):
        """
        Fill data from all retrievers with data from the given generator. Generator is expected to return bytes.
        Bytes will be parsed based on the retrievers. The total length of bytes read to fill this piece is also stored
        in this piece as `byte_length`.

        Args:
            generator (Generator[bytes, None, None] ): A generator from a binary scenario file
            pieces (OrderedDictType[str, AoE2Piece]): A list of pieces to reference when the retrievers have
                dependencies to orf rom them.
        """
        total_length = 0
        for _, retriever in enumerate(self.retrievers):
            parser.handle_retriever_dependency(retriever, self.retrievers, "construct", pieces)

            if retriever.datatype.type == "struct":
                retriever.data = []
                struct_name = retriever.datatype.var[7:]  # 7 == len("struct:") | Remove struct naming prefix
                for _ in range(retriever.datatype.repeat):
                    struct = self.struct_models.get(struct_name).clone_as_struct()
                    struct.set_data_from_generator(generator, pieces)
                    retriever.data.append(struct)

                    total_length += struct.byte_length
            else:
                retrieved_bytes = parser.retrieve_bytes(generator, retriever)
                retriever.data = parser.parse_bytes(retriever, retrieved_bytes)

                total_length += sum([len(raw_bytes) for raw_bytes in retrieved_bytes])

        self.byte_length = total_length

    def set_data(self, data, pieces):
        if len(data) == len(self.retrievers):
            for i in range(len(data)):
                self.retrievers[i].data = data[i]

                if hasattr(self.retrievers[i], 'on_construct'):
                    parser.handle_retriever_dependency(self.retrievers[i], self.retrievers, "construct", pieces)
        else:
            print(f"\nError in: {self.__class__.__name__}")
            print(f"Data: ({len(data)}) "
                  f"{helper.pretty_print_list([f'{i}: {str(x)}' for i, x in enumerate(data)])}")
            print(f"Retrievers: ({len(self.retrievers)}) "
                  f"{helper.pretty_print_list([f'{i}: {str(x)}' for i, x in enumerate(self.retrievers)])}")
            raise ValueError("Data list isn't the same size as the DataType list")

    def _entry_to_string(self, name, data, datatype):
        return "\t" + name + ": " + data + " (" + datatype + ")\n"

    def get_header_string(self):
        return "######################## " + self.name + " ######################## [FILEPART]"

    def get_byte_structure_as_string(self, pieces, skip_retrievers=None):
        if skip_retrievers is None:
            skip_retrievers = []

        byte_structure = "\n" + self.get_header_string()

        for retriever in self.retrievers:
            if retriever.name in skip_retrievers:
                continue
            byte_structure += "\n"

            listed_retriever_data = helper.listify(retriever.data)
            struct_header_set = False
            for struct in listed_retriever_data:
                if not struct_header_set:
                    byte_structure += f"\n{'#' * 27} {retriever.name} ({retriever.datatype.to_simple_string()})"
                    struct_header_set = True
                byte_structure += struct.get_byte_structure_as_string(pieces)
            # Struct Header was set. Retriever was struct, data retrieved using recursion. Next retriever.
            if struct_header_set:
                byte_structure += f"{'#' * 27} End of: {retriever.name} ({retriever.datatype.to_simple_string()})\n"
                continue

            retriever_data_bytes = parser.retriever_to_bytes(retriever, pieces)
            if retriever_data_bytes is None:
                return byte_structure
            else:
                retriever_data_bytes = retriever_data_bytes.hex()

            retriever_short_string: str = retriever.get_short_str()
            retriever_hex = helper.create_textual_hex(
                retriever_data_bytes, space_distance=2, enter_distance=24
            )

            split_hex = retriever_hex.split("\n")
            split_hex_length = len(split_hex)

            split_data_string = retriever_short_string.replace('\x00', ' ').splitlines()
            data_lines = []
            for x in split_data_string:
                if len(x) > 120:
                    data_lines += [f'\t{x}' for x in helper.insert_char(x, '\r\n', 120).splitlines()]
                else:
                    data_lines.append(x)
            split_data_length = len(data_lines)

            lines = max(split_hex_length, split_data_length)

            combined_strings = []
            for i in range(0, lines):
                hex_part = split_hex[i] if i < split_hex_length else ""
                data_part = data_lines[i] if i < split_data_length else ""
                combined_strings.append(helper.add_suffix_chars(hex_part, " ", 28) + data_part)

            byte_structure += "\n".join(combined_strings)

        return byte_structure + "\n"

    def __str__(self):
        represent = self.name + ": \n"

        for i, val in enumerate(self.retrievers):
            if type(self.retrievers[i].data) is list and len(self.retrievers[i].data) > 0:
                if isinstance(self.retrievers[i].data[0], AoE2FilePart):
                    represent += "\t" + val.name + ": [\n"
                    for x in self.retrievers[i].data:
                        represent += "\t\t" + str(x)
                    represent += "\t]\n"
                else:
                    represent += self._entry_to_string(
                        val.name,
                        str(self.retrievers[i].data),
                        str(val.datatype.to_simple_string())
                    )
            else:
                if self.retrievers[i].data is not None:
                    data = self.retrievers[i].data
                else:
                    data = "None"
                represent += self._entry_to_string(val.name, str(data), str(val.datatype.to_simple_string()))

        return represent