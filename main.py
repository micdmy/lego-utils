import argparse
import json
from rebricable import Client, User, test_rate_limiter, LostParts


def load_config(config_path):
    """Load JSON configuration from the given path.

    Returns:
        (dict, None) if successful,
        (None, str) if an error occurred with a message.
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"Config file '{config_path}' not found."
    except json.JSONDecodeError as e:
        return None, f"Failed to parse JSON file '{config_path}': {e}"

def cache_lost_parts(logged_user: User):
    res, error = logged_user.get_fetch_json("lost_parts/")
    if error:
        print(f"cache_lost_parts: Error: {error}")
        return
    with open("./json_cache/lost_parts.json", 'w') as f:
        json.dump(res, f)
    return res


def main():
    parser = argparse.ArgumentParser(
        description="Load configuration from JSON file.")
    parser.add_argument('-c', '--config', default='./config.json',
                        help = 'Path to the configuration JSON file (default: ./config.json)')
    parser.add_argument('-l', '--update-lost-cache', default = True,
                        help = 'download list of lost parts from rebricable profile and save to json file (overwites old one)')
    args = parser.parse_args()

    config, error = load_config(args.config)
    if error:
        print(f"Error: {error}")
        return

    print("Loaded configuration:")
    print(json.dumps(config, indent=2))

    client = Client(config["rebricable"])
    user = User(client, config["rebricable"])
    if user.log_in() is None:
        return
    if args.update_lost_cache :
        lost_parts = cache_lost_parts(user)
    else :
        lost_parts = json.load("./json_cache/lost_parts.json")

    lost_parts = LostParts(lost_parts)
    sets_with_lost_parts = lost_parts.to_set_list()

    print("sets with lost parts:")
    print(sets_with_lost_parts)

    

    # res, error = client.get_fetch_json("lego/parts/6141/colors/25/")
    # if error:
    #     print(f"Error: {error}")
    #     return
    # print("Fetched:")
    # print(json.dumps(res, indent=2))





    #test_rate_limiter(client, "lego/colors")


if __name__ == '__main__':
    main()
#/api/v3/lego/parts/{part_num}/colors/{color_id}/
#{
#  "part_img_url": "https://cdn.rebrickable.com/media/parts/ldraw/2/6212.png",
#  "year_from": 2000,
#  "year_to": 2002,
#  "num_sets": 3,
#  "num_set_parts": 7,
#  "elements": [
#    "4141350",
#    "4189404",
#    "621228"
#  ]
#}