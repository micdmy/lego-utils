import argparse
import json
from rebricable import Client, User, test_rate_limiter


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


def main():
    parser = argparse.ArgumentParser(
        description="Load configuration from JSON file.")
    parser.add_argument('-c', '--config', default='./config.json',
                        help='Path to the configuration JSON file (default: ./config.json)')
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

    # res, error = client.get_fetch_json("lego/colors/1/")
    # if error:
    #     print(f"Error: {error}")
    #     return
    # print("Fetched:")
    # print(json.dumps(res, indent=2))

    res, error = user.get_fetch_json("lost_parts/")
    if error:
        print(f"Error: {error}")
        return
    print("Fetched:")
    print(json.dumps(res, indent=2))

    #test_rate_limiter(client, "lego/colors")


if __name__ == '__main__':
    main()
