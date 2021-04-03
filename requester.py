import requests
import threading
from concurrent.futures import ThreadPoolExecutor


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
    __temporary_container = []
    __container_lock = threading.Lock()

    @classmethod
    def __thread_request(cls, lower_bound, upper_bound, mode, max_num, address):
        fails_in_a_row = 0
        while lower_bound <= upper_bound:
            request = requests.get(address + str(lower_bound))
            if request.status_code == 200:
                fails_in_a_row = 0
                cls.__container_lock.acquire()
                cls.__temporary_container.append(request.json())
                print(f"Success {mode} {lower_bound} - {len(cls.__temporary_container) * 100 // max_num}%")
                cls.__container_lock.release()
            else:
                fails_in_a_row += 1
                if fails_in_a_row == cls.__number_of_retries:
                    raise TooManyFailedRequestsException(fails_in_a_row)
                else:
                    print(f"Failed {mode}: {lower_bound}")

                    # if it's not an empty move record try again
                    if not (mode == "move" and lower_bound in cls.__moves_to_be_skipped):
                        lower_bound -= 1
            lower_bound += 1

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

        cls.__temporary_container = []

        with ThreadPoolExecutor(max_workers=2) as tpe:
            lower_bound1 = 1
            upper_bound1 = number_of_requests // 2
            lower_bound2 = upper_bound1 + 1
            tpe.submit(cls.__thread_request, lower_bound1, upper_bound1, mode, number_of_requests,
                       cls.__api_address + address_suffix)
            tpe.submit(cls.__thread_request, lower_bound2, number_of_requests, mode, number_of_requests,
                       cls.__api_address + address_suffix)

        return cls.__temporary_container

    @classmethod
    def __thread_request_pokemons(cls, lower_bound, upper_bound):
        fails_in_a_row = 0
        while lower_bound <= upper_bound:
            request = requests.get(cls.__api_address + cls.__api_pokemon + str(lower_bound))
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
                        cls.__container_lock.acquire()
                        cls.__temporary_container.append((lower_bound, legendary, mythic, generation, flavor, genera,
                                                          inner_request.json()))
                        print(f"Success Pokemon {lower_bound}-{j}\t")
                        cls.__container_lock.release()
                    else:
                        fails_in_a_row += 1
                        if fails_in_a_row == cls.__number_of_retries:
                            raise TooManyFailedRequestsException(fails_in_a_row)
                        else:
                            print(f"Failed Pokemon {lower_bound}-{j}")
                            j -= 1
                    j += 1
            else:
                fails_in_a_row += 1
                if fails_in_a_row == cls.__number_of_retries:
                    raise TooManyFailedRequestsException(fails_in_a_row)
                else:
                    print(f"Failed Pokemon Species {lower_bound}")
                    lower_bound -= 1
            lower_bound += 1

    @classmethod
    def request_pokemons(cls):
        """Separate method for requesting Pokemons. Pokemon request are more complex because each Pokemon can have
        alternate forms"""

        cls.__temporary_container = []

        with ThreadPoolExecutor(max_workers=2) as tpe:
            lower_bound1 = 1
            upper_bound1 = cls.__NUMBER_OF_POKEMON // 2
            lower_bound2 = upper_bound1 + 1
            tpe.submit(cls.__thread_request_pokemons, lower_bound1, upper_bound1)
            tpe.submit(cls.__thread_request_pokemons, lower_bound2, cls.__NUMBER_OF_POKEMON)

        return cls.__temporary_container

    @classmethod
    def request_types(cls):
        return cls.__request("type")

    @classmethod
    def request_moves(cls):
        return cls.__request("move")

    @classmethod
    def request_abilities(cls):
        return cls.__request("ability")
