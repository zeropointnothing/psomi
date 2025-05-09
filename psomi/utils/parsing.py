from psomi.utils.data import User, Character

def parse_message(user: User, message: str) -> list[dict[str, str | Character]]:
    """
    Processes a message and returns a dictionary with the character info.
    """

    brackets = []
    final = []

    for character in [i for si in user.proxy_groups for i in si]: # flatten all characters into one list
        prefix, suffix = character.prefix.split("text")

        prefix = None if prefix == "" else prefix
        suffix = None if suffix == "" else suffix

        brackets.append({
            "character": character,
            "prefix": prefix,
            "suffix": suffix
        })


    lines = message.split('\n')
    for i, line in enumerate(lines):
        if not line:
            continue

        for character in brackets:
            # Check for prefix:text:suffix messages.
            if character["prefix"] and line.startswith(character["prefix"]):
                start = i

                if character["suffix"] and line.endswith(character["suffix"]):
                    final.append({"message": [line], "character": character["character"]})
                    continue
                for x, seek_line in enumerate(lines[i:]):
                    if character["suffix"] and seek_line.endswith(character["suffix"]):
                        final.append({"message": lines[start:start+x+1], "character": character["character"]})
                        continue

            # Check for normal prefix messages.
            if (character["prefix"] and not character["suffix"]) and line.startswith(character["prefix"]):
                start = i
                parse = False

                for x, seek_line in enumerate(lines[i:]):
                    end = x

                    # Don't parse a line that's been parsed by above method.
                    if seek_line in [parsed["message"] for parsed in final]:
                        break
                    # Allow for multiple characters to respond in one message.
                    elif seek_line.startswith(tuple([prefix for prefix in [_["prefix"] for _ in brackets if _["prefix"]] if prefix != character["prefix"]])):
                        end -= 1
                        parse = True
                        break
                    else:
                        parse = True
                if parse:
                    final.append({"message": lines[start:start+end+1], "character": character["character"]})

    return final