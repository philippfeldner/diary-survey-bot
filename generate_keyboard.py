with open('data/keyboard_presets.py', 'r') as f:
    data = f.readlines()

for i in range(0, len(data)):
    data[i] = '["' + data[i][:-1] + '"],\n'

with open('data/keyboard_presets.py', 'w') as f:
    f.writelines(data)
