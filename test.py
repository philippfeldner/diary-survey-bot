

with open('test.json', 'r') as f:
    data = f.read()

data = data.replace('\n  }', ',\n"commands": []\n}')

with open('test.json', 'w') as f:
    f.write(data)

