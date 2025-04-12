import json


# ANSI-коды цвета
class bcolors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

try:
    with open("cc.json") as f:
        cc_data = json.load(f)
except OSError as e:
    print('Файл cc.json не найден, выполни команду:\n')
    print('radon cc . -j -O cc.json\n')
    exit()

try:
    with open("coverage.json") as f:
        coverage_data = json.load(f)
except OSError as e:
    print('Файл coverage.json не найден, выполни команды:\n')
    print('coverage run --branch -m unittest discover')
    print('coverage json -o coverage.json\n')
    exit()


crap_values = []  # Для сбора всех значений CRAP

for filename, methods in cc_data.items():
    if filename not in coverage_data["files"]:
        print(f"Файл {filename} не найден в отчете о покрытии. Пропускаю...")
        continue

    if filename.startswith("test_"):
        continue

    cov_percent = coverage_data["files"][filename]["summary"]["percent_covered"]
    cov = cov_percent / 100

    for method in methods:
        comp = method["complexity"]
        crap = comp ** 2 * (1 - cov) ** 3 + comp
        crap_f = f"{comp}^2 * (1 - {round(cov, 2)})^3 + {comp}"
        crap_values.append(crap)

        # Подсветка CRAP-индекса
        if crap < 10:
            color = bcolors.GREEN
        elif crap < 30:
            color = bcolors.YELLOW
        else:
            color = bcolors.RED

        print(f"{filename}::{method['name']} \t (CRAP: {color}{crap:.2f}{bcolors.ENDC}) \t {crap_f}")

# Вывод статистики
if crap_values:
    average_crap = sum(crap_values) / len(crap_values)
    max_crap = max(crap_values)

    # Цвет для среднего значения
    avg_color = (
        bcolors.GREEN if average_crap < 10 else
        bcolors.YELLOW if average_crap < 30 else
        bcolors.RED
    )

    # Цвет для максимального значения
    max_color = (
        bcolors.GREEN if max_crap < 10 else
        bcolors.YELLOW if max_crap < 30 else
        bcolors.RED
    )

    print("\n" + "=" * 20)
    print(f"  Max CRAP: {avg_color}{average_crap:.2f}{bcolors.ENDC}")
    print(f"  Avg CRAP: {max_color}{max_crap:.2f}{bcolors.ENDC}")
    print("=" * 20)
else:
    print("\nНет данных для расчета статистики CRAP")