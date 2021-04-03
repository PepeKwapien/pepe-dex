import os
import pickle
import re
from datetime import timedelta
from time import time
from Levenshtein import distance

from pokemon_exceptions import NoGivenTypeException as NGTE, NoGivenMoveException as NGME, \
    NoGivenAbilityException as NGAE, NoGivenPokemonException as NGPE
from requester import Requester


def proper_word(word):
    """Converts a single string into a string that starts with a capital letter. Every character after the first one is
        lowercase"""
    return word.capitalize()


def split_then_proper_word(word_with_dashes):
    """Splits string by dashes and then converts every received word into a proper word that start with a capital letter
        and is followed by lowercase characters"""

    return " ".join([proper_word(word) for word in word_with_dashes.split('-')])


class Type:
    def __init__(self, request_json):
        damage_relations = request_json["damage_relations"]
        self.__name = proper_word(request_json["name"])
        self.__double_from = [proper_word(typ["name"]) for typ in damage_relations["double_damage_from"]]
        self.__double_to = [proper_word(typ["name"]) for typ in damage_relations["double_damage_to"]]
        self.__half_from = [proper_word(typ["name"]) for typ in damage_relations["half_damage_from"]]
        self.__half_to = [proper_word(typ["name"]) for typ in damage_relations["half_damage_to"]]
        self.__no_from = [proper_word(typ["name"]) for typ in damage_relations["no_damage_from"]]
        self.__no_to = [proper_word(typ["name"]) for typ in damage_relations["no_damage_to"]]

    @property
    def name(self):
        return self.__name

    @property
    def double_from(self):
        return self.__double_from

    @property
    def double_to(self):
        return self.__double_to

    @property
    def half_from(self):
        return self.__half_from

    @property
    def half_to(self):
        return self.__half_to

    @property
    def no_from(self):
        return self.__no_from

    @property
    def no_to(self):
        return self.__no_to

    def __eq__(self, other):
        return str(other) == self.__name

    def __str__(self):
        return self.__name


class Types:
    __types = []
    __directory = "SavedData"
    __file_name = "types.data"

    @classmethod
    def create_types(cls, json_types):
        for typ in json_types:
            cls.__types.append(Type(typ))

    @classmethod
    def save_types(cls):
        try:
            file_path = os.path.abspath(cls.__directory)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            file_path += f"\\{cls.__file_name}"
            with open(file_path, "wb") as file:
                pickle.dump(cls.__types, file)
        except OSError:
            raise

    @classmethod
    def prepare_types(cls):
        try:
            start_time = time()  # start measuring time
            file_path = os.path.abspath(cls.__directory)
            file_path += f"\\{cls.__file_name}"
            if not os.path.exists(file_path):
                cls.create_types(Requester.request_types())
                cls.save_types()
            else:
                with open(file_path, "rb") as file:
                    cls.__types = pickle.load(file)
            print(f"Types loaded in: {timedelta(seconds=time() - start_time)}")  # print measured time
        except OSError:
            raise

    @classmethod
    def get_type(cls, name):
        name = proper_word(name)
        types_found = [typ for typ in cls.__types if typ.name == name]
        if len(types_found) > 0:
            return types_found[0]
        else:
            raise NGTE(name)

    @classmethod
    def get_types_string_list(cls):
        return sorted([typ.name for typ in cls.__types])

    @classmethod
    def print_types(cls):
        print("Available types:")
        for typ in cls.__types:
            print(typ)

    @classmethod
    def calculate_defence(cls, list_of_types):
        type_points = {}
        for typ in cls.__types:
            type_points[typ.name] = 0
        for typ in list_of_types:
            try:
                current_type = Types.get_type(proper_word(typ))
                for inner_type in current_type.no_from:
                    type_points[inner_type] += 2
                for inner_type in current_type.half_from:
                    type_points[inner_type] += 1
                for inner_type in current_type.double_from:
                    type_points[inner_type] -= 1
            except NGTE:
                print(f"No such type as {typ}")
        terrible = []
        bad = []
        good = []
        great = []
        for typ in type_points:
            value = type_points[typ]
            if value <= -2:
                terrible.append(typ)
            elif -2 < value < 0:
                bad.append(typ)
            elif 0 < value < 2:
                good.append(typ)
            elif 2 <= value:
                great.append(typ)

        terrible.sort(key=lambda t: t)
        bad.sort(key=lambda t: t)
        good.sort(key=lambda t: t)
        great.sort(key=lambda t: t)

        return terrible, bad, good, great

    @classmethod
    def calculate_offence(cls, list_of_types):
        type_points = {}
        for typ in cls.__types:
            type_points[typ.name] = 0
        for typ in list_of_types:
            try:
                current_type = Types.get_type(proper_word(typ))
                for inner_type in current_type.no_to:
                    type_points[inner_type] -= 2
                for inner_type in current_type.half_to:
                    type_points[inner_type] -= 1
                for inner_type in current_type.double_to:
                    type_points[inner_type] += 1
            except NGTE:
                print(f"No such type as {typ}")
        terrible = []
        bad = []
        good = []
        great = []
        for typ in type_points:
            value = type_points[typ]
            if value <= -2:
                terrible.append(typ)
            elif -2 < value < 0:
                bad.append(typ)
            elif 0 < value < 2:
                good.append(typ)
            elif 2 <= value:
                great.append(typ)

        terrible.sort(key=lambda t: t)
        bad.sort(key=lambda t: t)
        good.sort(key=lambda t: t)
        great.sort(key=lambda t: t)

        return terrible, bad, good, great


class Move:
    def __init__(self, request_json):
        # there are moves like vine-whip, flying-press
        self.__name = split_then_proper_word(request_json["name"])

        # some moves are bound to hit
        self.__accuracy = request_json["accuracy"] if request_json["accuracy"] is not None else "-"

        try:
            # dynamax moves don't have assigned damage class
            self.__class = proper_word(request_json["damage_class"]["name"])
        except TypeError:
            print(f"No damage class {self.__name}")
            self.__class = "Dynamax"

        self.__desc = "No description found."
        flavor_texts = request_json["flavor_text_entries"]
        for index in range(len(flavor_texts) - 1, -1, -1):  # searching for newest flavor text in English
            if flavor_texts[index]["language"]["name"] == "en":
                self.__desc = flavor_texts[index]["flavor_text"]
                break

        # some moves have chance for an additional effect
        self.__effect_chance = request_json["effect_chance"] if request_json["effect_chance"] is not None else 0

        # power of some moves depends on different factors
        self.__power = request_json["power"] if request_json["power"] is not None else "-"

        # dynamax moves don't have specified amount of power points
        self.__pp = request_json["pp"] if request_json["pp"] is not None else "-"

        self.__priority = request_json["priority"]
        self.__type = Types.get_type(request_json["type"]["name"])

    @property
    def pp(self):
        return self.__pp

    @property
    def power(self):
        return self.__power

    @property
    def accuracy(self):
        return self.__accuracy

    @property
    def effect_chance(self):
        return self.__effect_chance

    @property
    def priority(self):
        return self.__priority

    @property
    def description(self):
        return self.__desc

    @property
    def type(self):
        return self.__type.name

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, new_name):
        self.__name = new_name

    @property
    def move_class(self):
        return self.__class

    @move_class.setter
    def move_class(self, new_class):
        self.__class = new_class

    def __eq__(self, other):
        return str(other) == self.__name

    def __str__(self):
        return f"{self.__name}"


class Moves:
    __moves = []
    __directory = "SavedData"
    __file_name = "moves.data"

    @classmethod
    def create_moves(cls, json_moves):
        for move in json_moves:
            cls.__moves.append(Move(move))
        cls.__fix_z_moves()

    @classmethod
    def __fix_z_moves(cls):
        # z-moves have only 1 power point
        z_moves = [move for move in cls.__moves if move.pp == 1]
        for move in z_moves:
            move.move_class = "Z-move"

        # z-moves are doubled and have names ending with either word physical or special
        z_moves = [move for move in z_moves if re.match(r"^.*\s(Physical|Special)$", move.name) is not None]

        z_moves_physical = z_moves[::2]
        z_moves_special = z_moves[1::2]

        # physical z-moves have description - get rid of 'Physical' suffix
        for move in z_moves_physical:
            name = move.name.split()
            name = name[:len(name) - 1]
            move.name = " ".join(name)

        # special z-moves don't have description - redundant copies
        for move in z_moves_special:
            cls.__moves.remove(move)

    @classmethod
    def save_moves(cls):
        try:
            file_path = os.path.abspath(cls.__directory)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            file_path += f"\\{cls.__file_name}"
            with open(file_path, "wb") as file:
                pickle.dump(cls.__moves, file)
        except OSError:
            raise

    @classmethod
    def prepare_moves(cls):
        try:
            start = time()  # start measuring time
            file_path = os.path.abspath(cls.__directory)
            file_path += f"\\{cls.__file_name}"
            if not os.path.exists(file_path):
                cls.create_moves(Requester.request_moves())
                cls.save_moves()
            else:
                with open(file_path, "rb") as file:
                    cls.__moves = pickle.load(file)
            print(f"Moves loaded in: {timedelta(seconds=time() - start)}")  # print measured time
        except OSError:
            raise

    @classmethod
    def get_move(cls, name):
        name = split_then_proper_word(name)
        move_found = [move for move in cls.__moves if move.name == name]
        if len(move_found) > 0:
            return move_found[0]
        else:
            raise NGME(name)

    @classmethod
    def get_moves(cls):
        return cls.__moves

    @classmethod
    def print_moves(cls):
        print("Available moves:")
        for move in cls.__moves:
            print(move)

    @classmethod
    def print_moves_with_description(cls):
        print("Available moves and their corresponding description:")
        for move in cls.__moves:
            print(f"{move.name} - {move.description}")


class Ability:
    def __init__(self, request_json):

        # there are abilities like sheer-will or rain-dish
        self.__name = split_then_proper_word(request_json["name"])
        self.__desc = None

        # descriptions of effects have priority because they describe their in-battle and out-of-battle effects
        for desc in request_json["effect_entries"]:
            if desc["language"]["name"] == "en":
                self.__desc = desc["effect"]
                break
        if self.__desc is None:
            flavor_texts = request_json["flavor_text_entries"]
            for index in range(len(flavor_texts) - 1, -1, -1):
                if flavor_texts[index]["language"]["name"] == "en":
                    self.__desc = flavor_texts[index]["flavor_text"]
                    break
        if self.__desc is None:
            self.__desc = "No description found."

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__desc

    @description.setter
    def description(self, desc):
        self.__desc = desc

    def __eq__(self, other):
        return str(other) == self.__name

    def __str__(self):
        return self.__name


class Abilities:
    __abilities = []
    __directory = "SavedData"
    __file_name = "abilities.data"

    @classmethod
    def create_abilities(cls, json_abilities):
        # names of all abilities created during this method call
        names = []
        for ability in json_abilities:
            new_ability = Ability(ability)
            if new_ability.name not in names:
                cls.__abilities.append(new_ability)
                names.append(new_ability.name)
            else:
                # if there is another ability with the exact same name their descriptions will merge
                for previous_ability in cls.__abilities:
                    if previous_ability == new_ability:
                        previous_ability.description += f"/\n{new_ability.description}"
                        break

    @classmethod
    def save_abilities(cls):
        try:
            file_path = os.path.abspath(cls.__directory)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            file_path += f"\\{cls.__file_name}"
            with open(file_path, "wb") as file:
                pickle.dump(cls.__abilities, file)
        except OSError:
            raise

    @classmethod
    def prepare_abilities(cls):
        try:
            start = time()  # start measuring time
            file_path = os.path.abspath(cls.__directory)
            file_path += f"\\{cls.__file_name}"
            if not os.path.exists(file_path):
                cls.create_abilities(Requester.request_abilities())
                cls.save_abilities()
            else:
                with open(file_path, "rb") as file:
                    cls.__abilities = pickle.load(file)
            print(f"Abilities loaded in: {timedelta(seconds=time() - start)}")  # print measured time
        except OSError:
            raise

    @classmethod
    def get_ability(cls, name):
        name = split_then_proper_word(name)
        found_abilities = [ability for ability in cls.__abilities if ability.name == name]
        if len(found_abilities) > 0:
            return found_abilities[0]
        else:
            raise NGAE(name)

    @classmethod
    def print_abilities(cls):
        print("Available abilities:")
        for ability in cls.__abilities:
            print(ability)

    @classmethod
    def print_abilities_with_description(cls):
        print("Available abilities with their description:")
        for ability in cls.__abilities:
            print(f"{ability.name} - {ability.description}")


class Pokemon:
    def __init__(self, dex_number, legendary, mythic, generation, flavor_text, genera, request_text):
        # there are pokemons like mr-mime or articuno-galar
        self.__name = split_then_proper_word(request_text["name"])

        # number assigned to a pokemon by pokemon creators
        self.__dex_number = dex_number
        self.__desc = flavor_text

        # number assigned to a pokemon by an api
        self.__order = request_text["id"]
        self.__legendary = legendary
        self.__mythic = mythic

        # number in roman numeral identifying generation eg. VII
        generation = generation.split("-")[1].upper()
        self.__generation = generation
        self.__height = request_text["height"]
        self.__weight = request_text["weight"]
        self.__sprites = request_text["sprites"]
        self.__genera = genera

        self.__stats = []
        api_stats = request_text["stats"]
        for stat in api_stats:
            # stats are tuples (name of the stat, value of the stat)
            self.__stats.append((stat["stat"]["name"], stat["base_stat"]))

        self.__abilities = []
        api_abilities = request_text["abilities"]
        for ability in api_abilities:
            self.__abilities.append((Abilities.get_ability(ability["ability"]["name"]), ability["is_hidden"]))

        self.__moves = []
        moves = [move["move"]["name"] for move in request_text["moves"]]
        for m in moves:
            self.__moves.append(Moves.get_move(m))

        self.__types = []
        types = [typ["type"]["name"] for typ in request_text["types"]]
        for typ in types:
            self.__types.append(Types.get_type(typ))

    @property
    def name(self):
        return self.__name

    @property
    def generation(self):
        return self.__generation

    @property
    def genera(self):
        return self.__genera

    @property
    def dex_number(self):
        return self.__dex_number

    @property
    def order(self):
        return self.__order

    @property
    def description(self):
        return self.__desc

    @property
    def legendary(self):
        return self.__legendary

    @property
    def mythical(self):
        return self.__mythic

    @property
    def height(self):
        return self.__height

    @property
    def weight(self):
        return self.__weight

    @property
    def stats(self):
        return self.__stats

    @property
    def moves(self):
        return self.__moves

    @property
    def types(self):
        return self.__types

    @property
    def abilities(self):
        return self.__abilities

    @property
    def sprites(self):
        return self.__sprites

    def __eq__(self, other):
        return str(other) == self.__name

    def __str__(self):
        return f"{self.__name}"


class Pokemons:
    __pokemons = []
    __directory = "SavedData"
    __file_name = "pokemons.data"

    @classmethod
    def create_pokemons(cls, pokemons):
        for pokemon in pokemons:
            cls.__pokemons.append(
                Pokemon(pokemon[0], pokemon[1], pokemon[2], pokemon[3], pokemon[4], pokemon[5], pokemon[6]))

    @classmethod
    def save_pokemons(cls):
        try:
            file_path = os.path.abspath(cls.__directory)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            file_path += f"\\{cls.__file_name}"
            with open(file_path, "wb") as file:
                pickle.dump(cls.__pokemons, file)
        except OSError:
            raise

    @classmethod
    def prepare_pokemons(cls):
        try:
            start = time()
            file_path = os.path.abspath(cls.__directory)
            file_path += f"\\{cls.__file_name}"
            if not os.path.exists(file_path):
                cls.create_pokemons(Requester.request_pokemons())
                cls.save_pokemons()
            else:
                with open(file_path, "rb") as file:
                    cls.__pokemons = pickle.load(file)
            print(f"Pokemons loaded in: {timedelta(seconds=time() - start)}")
        except OSError:
            raise

    @classmethod
    def get_filtered_pokemons(cls, name=None, primary=None, secondary=None, generation=None, order=0):
        if order == 0:
            filtered_pokemons = sorted(cls.__pokemons, key=lambda pok: (pok.dex_number, pok.order))
        else:
            filtered_pokemons = sorted(cls.__pokemons, key=lambda pok: pok.name)

        if name is not None:
            name = name.lower()
            filtered_pokemons = [pokemon for pokemon in filtered_pokemons if name in pokemon.name.lower() or distance(
                name, pokemon.name.lower()) < 4]
        if primary is not None:
            filtered_pokemons = [pokemon for pokemon in filtered_pokemons if
                                 len(pokemon.types) > 0 and pokemon.types[0].name == primary]
        if secondary is not None:
            filtered_pokemons = [pok for pok in filtered_pokemons if
                                 len(pok.types) > 1 and pok.types[1].name == secondary]
        if generation is not None:
            filtered_pokemons = [pok for pok in filtered_pokemons if pok.generation == generation]

        return filtered_pokemons

    @classmethod
    def get_pokemon(cls, name):
        found_pokemons = [p for p in cls.__pokemons if p.name == proper_word(name)]
        if len(found_pokemons) > 0:
            return found_pokemons[0]
        else:
            raise NGPE(name)

    @classmethod
    def print_pokemons(cls):
        for pok in cls.__pokemons:
            print(pok)


if __name__ == '__main__':
    Abilities.prepare_abilities()
    Abilities.print_abilities_with_description()
