import requests


class TooManyFailedRequestsException(Exception):
    """Raised when too many requests failed in a row"""

    def __init__(self, max_no_of_tries):
        message = f"Failed to connect with the server ({max_no_of_tries} requests failed in a row)"
        super().__init__(message)


class Requester:
    __number_of_retries = 10
    __NUMBER_OF_TYPES = 18
    __NUMBER_OF_MOVES = 796
    __NUMBER_OF_ABILITIES = 267
    __NUMBER_OF_POKEMON = 898
    __moves_to_be_skipped = [785]  # empty move records in the pokemon api
    __api_address = "https://pokeapi.co/api/v2/"
    __api_type = "type/"
    __api_move = "move/"
    __api_ability = "ability/"
    __api_pokemon = "pokemon-species/"

    @classmethod
    def __request(cls, mode):
        if mode == 'type':
            address_suffix = cls.__api_type
            number_of_requests = cls.__NUMBER_OF_TYPES
        elif mode == 'move':
            address_suffix = cls.__api_move
            number_of_requests = cls.__NUMBER_OF_MOVES
        elif mode == "ability":
            address_suffix = cls.__api_ability
            number_of_requests = cls.__NUMBER_OF_ABILITIES
        else:
            return

        json_list = []
        fails_in_a_row = 0
        i = 1
        while i <= number_of_requests:
            request = requests.get(cls.__api_address + address_suffix + str(i))
            if request.status_code == 200:
                fails_in_a_row = 0
                print(f"Success {mode} {i}\t| {i * 100 // number_of_requests}%")
                json_list.append(request.json())
            else:
                fails_in_a_row += 1
                if fails_in_a_row == cls.__number_of_retries:
                    raise TooManyFailedRequestsException(fails_in_a_row)
                else:
                    print(f"Failed {mode} {i}")

                    # if it's not an empty move record try again
                    if not (mode == "move" and i in cls.__moves_to_be_skipped):
                        i -= 1
            i += 1

        return json_list

    @classmethod
    def request_pokemons(cls):
        """Separate method for requesting Pokemons. Pokemon request are more complex because each Pokemon can have
        alternate forms"""

        constructor_parameters_list = []
        fails_in_a_row = 0
        i = 1
        while i <= cls.__NUMBER_OF_POKEMON:
            request = requests.get(cls.__api_address + cls.__api_pokemon + str(i))
            if request.status_code == 200:
                fails_in_a_row = 0
                request = request.json()
                mythic = request["is_mythical"]
                legendary = request["is_legendary"]
                generation = request["generation"]["name"]
                flavor = "No description found."
                flavor_texts = request["flavor_text_entries"]
                for index in range(len(flavor_texts) - 1, -1, -1):
                    if flavor_texts[index]["language"]["name"] == "en":
                        flavor = flavor_texts[index]["flavor_text"]
                        break

                genera = "Pokemon"
                for genus in request["genera"]:
                    if genus["language"]["name"] == "en":
                        genera = genus["genus"]

                j = 0
                while j < len(request["varieties"]):  # Get every alternate form of certain pokemon species
                    inner_request = requests.get(request["varieties"][j]["pokemon"]["url"])
                    if inner_request.status_code == 200:
                        fails_in_a_row = 0
                        print(f"Success Pokemon {i}-{j}\t| {i * 100 // cls.__NUMBER_OF_POKEMON}%")
                        constructor_parameters_list.append((i, legendary, mythic, generation, flavor, genera,
                                                            inner_request.json()))
                    else:
                        fails_in_a_row += 1
                        if fails_in_a_row == cls.__number_of_retries:
                            raise TooManyFailedRequestsException(fails_in_a_row)
                        else:
                            print(f"Failed Pokemon {i}-{j}")
                            j -= 1
                    j += 1
            else:
                fails_in_a_row += 1
                if fails_in_a_row == cls.__number_of_retries:
                    raise TooManyFailedRequestsException(fails_in_a_row)
                else:
                    print(f"Failed Pokemon {i}")
                    i -= 1
            i += 1

        return constructor_parameters_list

    @classmethod
    def request_types(cls):
        return cls.__request("type")

    @classmethod
    def request_moves(cls):
        return cls.__request("move")

    @classmethod
    def request_abilities(cls):
        return cls.__request("ability")
