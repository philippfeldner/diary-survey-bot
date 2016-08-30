# Keywords:
#
# BLOCK settings:
# MANDATORY         : Marks the block as mandatory. The next block is only getting scheduled when the current
#                     block is complete or a question contains the command: Q_ON
#
# Commands:
# FORCE_KB_REPLY    : The user has to choose an option from the Keyboard to proceed.
#                     does no answer all questions.
# Q_ON              : See BLOCK settings - MANDATORY
#
# COUNTRY           : Signals, that the user will respond with his country:  Relevant for database.
# AGE               : Signals, that the user will respond with his age:      Relevant for database.
# GENDER            : Signals, that the user will respond with his gender:   Relevant for database.
# TIMEZONE          : Signals, that the user will respond with his timezone: Relevant for database.


# List of chat_ids that are admins
ADMINS = ['0x0', '0x0']

# Debug mode on/off
DEBUG = True

# For testing purposes. Sets all block scheduling to x seconds.
# To deactivate set it to False (0)
QUICK_TEST = 0

# Default language if something goes wrong.
DEFAULT_LANGUAGE = 'de'

# Default timezone if something goes wrong.
DEFAULT_TIMEZONE = 'Europe/Vienna'

# Scheduling intervals for question blocks.
SCHEDULE_INTERVALS = {
                        "RANDOM_1": ["08:00", "12:00"],
                        "RANDOM_2": ["13:00", "15:00"],
                        "RANDOM_3": ["16:00", "20:00"]
                     }

INFO_TEXT = {
                "de": "pokemon@uni-graz.at",
                "en": "pokemon@uni-graz.at",
                "fr": "pokemon@uni-graz.at",
                "es": "pokemon@uni-graz.at"
            }





