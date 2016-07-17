def handler():
    # Todo
    return


def get_bot_token(name):
    try:
        key = open(name).read()
    except IOError as e:
        raise e
    return key
