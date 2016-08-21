from admin.settings import DEBUG


def debug(flag, text, log=False):
    if DEBUG is False:
        return

    print(flag + '\t\t' + text + '\n')
    if log:
        with open('log.txt', 'a') as f:
            f.write(flag + '\t\t' + text + '\n')
    return
