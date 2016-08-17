import random

schedule_points = dict()
schedule_points["RANDOM_1"] = ["08:00", "12:00"]


def calc_block_time(time_t):
    try:
        interval = schedule_points[time_t]
    except KeyError:
        return 0

    hh_start = int(interval[0][:2])
    hh_end = int(interval[1][:2])
    mm_begin = int(interval[0][3:])
    mm_end = int(interval[1][3:])

    if hh_start < hh_end:
        value_hh = random.randint(hh_start, hh_end)
        if value_hh == hh_start:
            value_mm = random.randint(mm_begin + 10, 59)  # Todo: Catch more special cases later
        elif value_hh == hh_end:
            value_mm = random.randint(0, mm_end)
        else:
            value_mm = random.randint(0, 59)

    elif hh_start == hh_end:
        value_hh = hh_start
        value_mm = random.randint(mm_begin + 10, mm_end - 10)
    else:
        value_hh = random.choice[random.randint(hh_start, 23), random.randint(0, hh_end)]
        if value_hh == hh_start:
            value_mm = random.randint(mm_begin + 10, 59)  # Todo: Catch more special cases later
        elif value_hh == hh_end:
            value_mm = random.randint(0, mm_end)
        else:
            value_mm = random.randint(0, 59)

    return str(value_hh).zfill(2) + ':' + str(value_mm).zfill(2)

time_t = calc_block_time("RANDOM_1")
print(time_t)