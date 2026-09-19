
# py_picture_cube

GUI aplikace v Pythonu pro zadání a pozdější výpočet skládání obrazkové Rubikovy kostky 3×3×3.

Aplikace umožňuje zadat všech 54 polí kostky. Každé pole má:

- číslo strany `1–6`
- natočení `0° / 90° / 180° / 270°`

Kostku lze prostorově otáčet pouze pro lepší pohled. Otáčení kamery nemění matematický stav kostky.

## Python

Doporučená verze:

```text
Python 3.12.10



py -3.12 -m venv .venv

.\.venv\Scripts\Activate.ps1

python --version


python -m pip install --upgrade pip
python -m pip install -r requirements.txt