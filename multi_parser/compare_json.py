# import os
# import json
# from deepdiff import DeepDiff
#
# def compare_json_files(folder1, folder2):
#     files1 = set(f for f in os.listdir(folder1) if f.endswith('.json'))
#     files2 = set(f for f in os.listdir(folder2) if f.endswith('.json'))
#     common_files = files1.intersection(files2)
#     results = []
#
#     for file in common_files:
#         path1 = os.path.join(folder1, file)
#         path2 = os.path.join(folder2, file)
#
#         with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
#             data1 = json.load(f1)
#             data2 = json.load(f2)
#
#         diff = DeepDiff(data1, data2, ignore_order=True, verbose_level=2)
#         if diff:
#             results.append((file, diff))
#
#     return results
#
# def format_diff_readable(diff):
#     formatted = []
#     for change_type, changes in diff.items():
#         if change_type == 'values_changed':
#             for path, change in changes.items():
#                 old_value = change['old_value']
#                 new_value = change['new_value']
#                 formatted.append(f"Zmiana w {path}:")
#                 formatted.append(f"  Stara wartość: {old_value}")
#                 formatted.append(f"  Nowa wartość: {new_value}")
#                 formatted.append("")
#         elif change_type == 'dictionary_item_added':
#             for path, value in changes.items():
#                 formatted.append(f"Dodano nowy element w {path}:")
#                 formatted.append(f"  Wartość: {value}")
#                 formatted.append("")
#         elif change_type == 'dictionary_item_removed':
#             for path, value in changes.items():
#                 formatted.append(f"Usunięto element z {path}:")
#                 formatted.append(f"  Wartość: {value}")
#                 formatted.append("")
#         elif change_type == 'iterable_item_added':
#             for path, value in changes.items():
#                 formatted.append(f"Dodano nowy element do listy w {path}:")
#                 formatted.append(f"  Wartość: {value}")
#                 formatted.append("")
#         elif change_type == 'iterable_item_removed':
#             for path, value in changes.items():
#                 formatted.append(f"Usunięto element z listy w {path}:")
#                 formatted.append(f"  Wartość: {value}")
#                 formatted.append("")
#     return "\n".join(formatted)
#
# def main():
#     # folder1 = r"C:\Users\szyme\to_be_parsed\output\pptx"
#     # folder2 = r"C:\Users\szyme\to_be_parsed\output1\pptx"
#
#     #  PDF
#     folder1 = r"C:\Users\szyme\to_be_parsed\output\pdf"
#     folder2 = r"C:\Users\szyme\to_be_parsed\output1\pdf"
#
#     differences = compare_json_files(folder1, folder2)
#
#     if not differences:
#         print("Nie znaleziono różnic między plikami JSON w tych dwóch folderach.")
#     else:
#         print("\nZnalezione różnice:")
#         for file, diff in differences:
#             print(f"\nPlik: {file}")
#             print("Różnice:")
#             print(format_diff_readable(diff))
#
# if __name__ == "__main__":
#     main()

import os
import json
from deepdiff import DeepDiff

def compare_json_files(folder1, folder2):
    files1 = set(f for f in os.listdir(folder1) if f.endswith('.json'))
    files2 = set(f for f in os.listdir(folder2) if f.endswith('.json'))
    common_files = files1.intersection(files2)
    results = []

    for file in common_files:
        path1 = os.path.join(folder1, file)
        path2 = os.path.join(folder2, file)

        with open(path1, 'r', encoding='utf-8') as f1, open(path2, 'r', encoding='utf-8') as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        diff = DeepDiff(data1, data2, ignore_order=True, verbose_level=2)
        if diff:
            results.append((file, diff, data1, data2))

    return results

def calculate_difference_percentage(diff, data1, data2):
    total_items = count_items(data1) + count_items(data2)
    changed_items = count_changes(diff)
    if total_items == 0:
        return 0
    return (changed_items / total_items) * 100

def count_items(data):
    if isinstance(data, dict):
        return len(data) + sum(count_items(v) for v in data.values())
    elif isinstance(data, list):
        return len(data) + sum(count_items(item) for item in data)
    else:
        return 1

def count_changes(diff):
    return sum(len(changes) for changes in diff.values())

def format_diff_summary(diff):
    summary = []
    for change_type, changes in diff.items():
        summary.append(f"{change_type}: {len(changes)} zmian")
    return ", ".join(summary)

def compare_data_size(data1, data2):
    size1 = len(json.dumps(data1))
    size2 = len(json.dumps(data2))
    if size1 > size2:
        return "Folder 1", (size1 - size2) / size2 * 100
    elif size2 > size1:
        return "Folder 2", (size2 - size1) / size1 * 100
    else:
        return "Oba foldery", 0

def main():
    # folder1 = r"C:\Users\szyme\to_be_parsed\output\pptx"
    # folder2 = r"C:\Users\szyme\to_be_parsed\output1\pptx"

    #  PDF
    folder1 = r"C:\Users\szyme\to_be_parsed\output\pdf"
    folder2 = r"C:\Users\szyme\to_be_parsed\output1\pdf"

    differences = compare_json_files(folder1, folder2)

    if not differences:
        print("Nie znaleziono różnic między plikami JSON w tych dwóch folderach.")
    else:
        print("\nZnalezione różnice:")
        for file, diff, data1, data2 in differences:
            diff_percentage = calculate_difference_percentage(diff, data1, data2)
            larger_folder, size_diff_percentage = compare_data_size(data1, data2)
            print(f"\nPlik: {file}")
            print(f"Procent różnic: {diff_percentage:.2f}%")
            print(f"{larger_folder} zawiera więcej danych o {size_diff_percentage:.2f}%")
            print("Podsumowanie różnic:")
            print(format_diff_summary(diff))

if __name__ == "__main__":
    main()