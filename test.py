from datetime import datetime


def calc_delta_t(time, days):
    hh = time[:2]
    mm = time[3:]
    # Todo: Check correctness
    current = datetime.now()
    future = datetime(current.year, current.month, current.day + days, int(hh), int(mm))
    seconds = future - current
    return seconds.seconds

offset_1 = calc_delta_t("22:30", 0)
print(offset_1)