import argparse
import json
from rebricable import Client, User, test_rate_limiter, LostParts, filter_sets_not_figurines


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

def cache_lost_sets(lost_sets):
    with open("./json_cache/lost_sets.json", 'w') as f:
        json.dump(lost_sets, f)



def main():
    parser = argparse.ArgumentParser(
        description="Load configuration from JSON file.")
    parser.add_argument('-c', '--config', default='../config.json',
                        help = 'Path to the configuration JSON file (default: ./config.json)')
    parser.add_argument('-l', '--update-lost-cache', action="store_true" ,
                        help = 'download list of lost parts from rebricable profile and save to json file (overwites old one)')
    parser.add_argument('-s', '--update-lost-sets', action="store_true",
                        help = 'prepare json_cache/lost_sets.json from lost cache (either updated or cached)')
    parser.add_argument('-b', '--update_lost_by_set', action="store_true",
                        help = 'prepare json_cache/lost_lego_parts_by_set.json from lost cache (either updated or cached)')
    parser.add_argument('-f', '--filter_by_available_in_shop', action="store_true",
                        help = '')
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
        with open("./json_cache/lost_parts.json", 'r') as f:
            lost_parts = json.load(f)

    lost_parts = LostParts(lost_parts)
    sets_with_lost_parts = lost_parts.to_set_list()
    if args.update_lost_sets:
        cache_lost_sets(sets_with_lost_parts)
    


    #print("sets with lost parts:")
    #print(filter_sets_not_figurines(sets_with_lost_parts))

    by_set = lost_parts.to_part_by_set_dict()

    if args.update_lost_by_set: 
        # print(by_set)
        with open("./json_cache/lost_lego_parts_by_set.json", 'w') as f:
            json.dump(by_set, f)
    
    if args.filter_by_available_in_shop:
        f = open("./json_cache/lost_lego_part_by_set.json")
        available = json.load(f)
        for av_set, av_parts in available:
            lo_parts = by_set[av_set] # if not found something wrong, because available should be subset of by_set
            for av_part in av_parts: #iterate available parts list in set:
                lego_id = av_part["lego_id"]
                if lego_id in lo_parts: # available part is one of lost parts



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