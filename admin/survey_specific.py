

def baseline_(data):
    def mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)
    return str(int(mean(data)))


# Include your own functions here!
# Define them above.
def survey_function(user, data, function):
    if function == "baseline":
        return baseline_(data)


