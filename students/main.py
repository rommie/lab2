from enum import Enum
from flask import Flask
from flask_restplus import Api, Resource, fields, reqparse

app = Flask(__name__)
api = Api(app)

# Перечисление для выбора поля сортировки
class SortingField(Enum):
    NAME = 'name'  # Для сортировки по имени
    AGE = 'age'    # Для сортировки по возрасту
    GROUP = 'group'  # Для сортировки по группе

# Перечисление для порядка сортировки
class SortOrder(Enum):
    ASC = 'asc'    # Порядок сортировки по возрастанию
    DESC = 'desc'  # Порядок сортировки по убыванию

class SubjectGrade:
    def __init__(self, subject, grade):
        self.subject = subject
        self.grade = grade

    def to_dict(self):
        return {'subject': self.subject, 'grade': self.grade}

class Student:
    # Счетчик добавленных студентов, используется для идентификаторов
    student_id_counter = 0

    def __init__(self, name, age, group, year_of_study):
        Student.student_id_counter += 1
        self.uid = Student.student_id_counter
        self.name = name
        self.age = age
        self.group = group
        self.year_of_study = year_of_study
        self.subjects_grades = []

    def add_subject_grade(self, subject, grade):
        subject_grade = SubjectGrade(subject, grade)
        self.subjects_grades.append(subject_grade)

    def to_dict(self, include_uid=True):
        student_dict = {'name': self.name, 'age': self.age,
                        'group': self.group, 'year_of_study': self.year_of_study}
        if include_uid:
            student_dict['uid'] = self.uid
        student_dict['subjects_grades'] = [sg.to_dict() for sg in self.subjects_grades]
        return student_dict

# Сортировка студентов
def sort_students(students, field: SortingField, sort_order: SortOrder):
    if field == SortingField.NAME:
        students.sort(key=lambda x: x.name, reverse=(sort_order == SortOrder.DESC))
    elif field == SortingField.AGE:
        students.sort(key=lambda x: x.age, reverse=(sort_order == SortOrder.DESC))
    elif field == SortingField.GROUP:
        students.sort(key=lambda x: x.group, reverse=(sort_order == SortOrder.DESC))

    return students

# Получение статистики по студентам
def get_subject_statistics(students):
    subject_statistics = {}

    for student in students:
        for subject_grade in student.subjects_grades:
            subject = subject_grade.subject
            grade = subject_grade.grade

            if subject not in subject_statistics:
                subject_statistics[subject] = {'grades': [grade], 'count': 1, 'average_grade': grade}
            else:
                subject_statistics[subject]['grades'].append(grade)
                subject_statistics[subject]['count'] += 1
                subject_statistics[subject]['average_grade'] = sum(subject_statistics[subject]['grades']) / len(subject_statistics[subject]['grades'])

    return subject_statistics

# Пример данных о студентах
students_data = [
    Student('Иванов Иван Иванович', 19, 'ИТ22-1', 4),
    Student('Сидоров Петр Петрович', 20, 'ИТ22-1', 4),
    Student('Петрова Анна Владимировна', 21, 'ИТ22-2', 3),
    Student('Смирнов Алексей Дмитриевич', 22, 'ИТ22-2', 3),
    Student('Козлова Екатерина Сергеевна', 20, 'ИТ22-1', 4)
]

# Добавим оценки по предметам (пятибалльная шкала) для каждого студента
students_data[0].add_subject_grade('Программирование', 4)
students_data[0].add_subject_grade('Базы данных', 5)
students_data[0].add_subject_grade('Веб-разработка', 3)

students_data[1].add_subject_grade('Программирование', 5)
students_data[1].add_subject_grade('Базы данных', 4)
students_data[1].add_subject_grade('Веб-разработка', 4)

students_data[2].add_subject_grade('Программирование', 3)
students_data[2].add_subject_grade('Веб-разработка', 4)

students_data[3].add_subject_grade('Программирование', 4)
students_data[3].add_subject_grade('Базы данных', 3)
students_data[3].add_subject_grade('Веб-разработка', 5)

students_data[4].add_subject_grade('Программирование', 5)
students_data[4].add_subject_grade('Базы данных', 4)
students_data[4].add_subject_grade('Веб-разработка', 5)


# Модели API
subject_grade_model = api.model('SubjectGrade', {
    'subject': fields.String(required=True, description='Название предмета'),
    'grade': fields.Integer(required=True, description='Оценка')
})

student_model = api.model('Student', {
    'uid': fields.Integer(readonly=True, description='Идентификатор студента'),
    'name': fields.String(required=True, description='Имя студента'),
    'age': fields.Integer(required=True, description='Возраст студента'),
    'group': fields.String(required=True, description='Группа студента'),
    'year_of_study': fields.Integer(required=True, description='Год обучения студента'),
    'subjects_grades': fields.List(fields.Nested(subject_grade_model), description='Список оценок по предметам')
})

students_list = api.model('StudentsList', {
    'count': fields.Integer(required=True, description='Количество студентов'),
    'items': fields.List(fields.Nested(student_model), required=True, description='Список студентов')
})

subject_statistics_model = api.model('SubjectStatistics', {
        'subject': fields.String(description='Название предмета'),
        'count': fields.Integer(description='Количество студентов, изучающих предмет'),
        'average_grade': fields.Float(description='Средняя оценка по предмету')
    })

overall_statistics_model = api.model('OverallStatistic', {
    'average_age': fields.Float(description='Средний возраст'),
    'student_count': fields.Integer(description='Количество студентов'),
    'subject_statistics': fields.List(fields.Nested(subject_statistics_model), description='Статистика по каждому предмету')
})

# Парсер параметров сортировки
parser = reqparse.RequestParser()
parser.add_argument('sort_by', type=SortingField, help='Сортировка по имени, возрасту или группе')
parser.add_argument('sort_order', type=SortOrder, help='Порядок сортировки: asc или desc')

students_ns = api.namespace('students', description='Операции со студентами')

@students_ns.route('/students')
class StudentsResource(Resource):
    @students_ns.doc('Список всех студентов')
    @students_ns.expect(parser)
    @students_ns.marshal_with(students_list)
    def get(self):
        """
        Список всех студентов.
        """
        args = parser.parse_args()
        sort_by = args.get('sort_by', None)
        sort_order = args.get('sort_order', None)

        sorted_students = sort_students(students_data.copy(), sort_by, sort_order)
        student_list = [student.to_dict() for student in sorted_students]
        return {'count': len(student_list), 'items': student_list}

    @students_ns.doc('Добавление нового студента')
    @students_ns.expect(student_model)
    @students_ns.marshal_with(student_model)
    def post(self):
        """
        Добавление нового студента.
        """
        new_student_data = api.payload
        new_student = Student(
            name=new_student_data['name'],
            age=new_student_data['age'],
            group=new_student_data['group'],
            year_of_study=new_student_data['year_of_study']
        )

        if 'subjects_grades' in new_student_data:
            for subject_grade_data in new_student_data['subjects_grades']:
                new_student.add_subject_grade(subject_grade_data['subject'], subject_grade_data['grade'])

        students_data.append(new_student)
        return new_student.to_dict()

@students_ns.route('/students/<int:id>')
class StudentResource(Resource):
    @students_ns.doc('Получение студента')
    @students_ns.marshal_with(student_model)
    def get(self, id):
        """
        Получение студента по идентификатору.
        """
        for student in students_data:
            if student.uid == id:
                return student.to_dict()

        api.abort(404, message=f"Студент с идентификатором {id} не найден")

    @students_ns.doc('Обновление данных студента')
    @students_ns.expect(student_model)
    @students_ns.marshal_with(student_model)
    def patch(self, id):
        """
        Обновление данных студента по идентификатору.
        """
        update_data = api.payload
        for student in students_data:
            if student.uid == id:
                # Обновление информации о студенте
                for field, value in update_data.items():
                    setattr(student, field, value)

                return student.to_dict()

        api.abort(404, message=f"Студент с идентификатором {id} не найден")

    @students_ns.doc('Удаление студента')
    @students_ns.response(204, 'Студент удален')
    def delete(self, id):
        """
        Удаление студента по идентификатору.
        """
        global students_data
        students_data = [student for student in students_data if student.uid != id]
        return '', 204

    @students_ns.route('/students/<int:id>/grades')
    class StudentGradesResource(Resource):
        @students_ns.doc('Получение оценок студента')
        @students_ns.marshal_with(subject_grade_model, as_list=True)
        def get(self, id):
            """
            Получение оценок студента.
            """

            for student in students_data:
                if student.uid == id:                    
                    return [sg.to_dict() for sg in student.subjects_grades]

            api.abort(404, message=f"Студент с идентификатором {id} не найден")

        @students_ns.doc('Добавление оценок студенту')
        @students_ns.expect(subject_grade_model)
        @students_ns.marshal_with(subject_grade_model)
        def post(self, id):
            """
            Добавление оценок студенту.
            """

            for student in students_data:
                if student.uid == id:
                    student.add_subject_grade(api.payload['subject'], api.payload['grade'])
                    return student.subjects_grades[-1].to_dict()

            api.abort(404, message=f"Студент с идентификатором {id} не найден")

@students_ns.route('/statistics')
class OverallStatisticsResource(Resource):
    @students_ns.doc('Получение общей статистики по всем студентам')
    @students_ns.marshal_with(overall_statistics_model)
    def get(self):
        """
        Получение общей статистики по всем студентам.
        """
        if not students_data:
            api.abort(404, message="Студенты не найдены")

        # Расчет среднего возраста для всех студентов
        average_age = sum(student.age for student in students_data) / len(students_data)

        # Получение статистики по предметам
        subject_statistics = get_subject_statistics(students_data)

        return {
            'average_age': average_age,
            'student_count': len(students_data),
            'subject_statistics': [{'subject': subject, **stats} for subject, stats in subject_statistics.items()]
        }

if __name__ == '__main__':
    app.run(debug=True)