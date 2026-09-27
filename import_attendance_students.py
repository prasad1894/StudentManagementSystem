import re
import os

from pathlib import Path
from django import setup


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

setup()

from employees.models import Student, ClassSection


HTML_FILE = Path(
    "templates/employees/attendance_app.html"
)

html = HTML_FILE.read_text(
    encoding="utf-8"
)


# Find students object
match = re.search(
    r"const\s+students\s*=\s*\{(.*?)\n\s*\};",
    html,
    re.DOTALL
)

if not match:
    print("Could not find the students object.")
    raise SystemExit


students_text = match.group(1)


# Find classes
class_pattern = re.compile(
    r'"([^"]+)"\s*:\s*\[(.*?)\]',
    re.DOTALL
)

classes = class_pattern.findall(
    students_text
)


class_mapping = {
    "2nd Year CSM - A Sec": {
        "year": "2",
        "branch": "CSM",
        "section": "A",
    },

    "2nd Year CSM - B Sec": {
        "year": "2",
        "branch": "CSM",
        "section": "B",
    },

    "3rd Year CSM - A Sec": {
        "year": "3",
        "branch": "CSM",
        "section": "A",
    },

    "4th Year CSM - A Sec": {
        "year": "4",
        "branch": "CSM",
        "section": "A",
    },

    "4th Year CSM - B Sec": {
        "year": "4",
        "branch": "CSM",
        "section": "B",
    },
}


created_count = 0
updated_count = 0


for class_name, class_data in classes:

    if class_name not in class_mapping:
        print(
            f"Skipping unknown class: {class_name}"
        )
        continue


    mapping = class_mapping[class_name]


    class_section = ClassSection.objects.get(
        year=mapping["year"],
        branch=mapping["branch"],
        section=mapping["section"]
    )


    student_matches = re.findall(
        r'\{\s*roll:\s*"([^"]+)"\s*,\s*name:\s*"([^"]+)"\s*\}',
        class_data
    )


    for roll_number, name in student_matches:

        student, created = Student.objects.update_or_create(
            roll_number=roll_number,
            defaults={
                "name": name,
                "class_section": class_section,
                "admission_year": 2024,
                "is_active": True,
                "email": f"{roll_number.lower()}@attendance.local",
            }
        )


        if created:
            created_count += 1
        else:
            updated_count += 1


    print(
        f"Imported {class_name}: "
        f"{len(student_matches)} students"
    )


print()
print(
    f"Created students: {created_count}"
)

print(
    f"Updated students: {updated_count}"
)

print(
    "Student import completed successfully."
)