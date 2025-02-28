цель консольной утилиту которая помогает заполнять ворк логи, с повелением походим на git

сначала мы вносим логи в область подготовки. а затем проверим и пушим в jira 

Пример
```
# lit status 
Нет подготовленных записей для отправки.
```
Добавление записи 
```
# lit add TASK-1752 4 'Убрал из меню ссылку О компа' 
```
альтернативный вариант 
```
# lit add TASK-1752 4 'Убрал из меню ссылку О компании'  -d '12.02.2025' -t '10:00' 
```
Обязательные параметры:
code - код задачи в Jira
hours - отработанные часы 
message - тело сообщения для ворклога

Опциональные:
-d - день ха который внести лог (по умолчанию сегодня)
-t - время насалю лога (по умолчанию текущее время) [если hours 4 -t '10:00', то слот логов будет с 10:00 до 14:00]

```
# lit status 
12.02.2025
  [10:00 - 14:00] TASK-1752 4h `Убрал из меню ссылку О компании`
```

```
# lit push
```
отправляет подготовленные записи в jira 

хранить их можно в текстовом файле до отправки. что бы можно было редактировать
например в таком формате:
```
12.02.2025 [10:00 - 14:00] TASK-1752 4h `Убрал из меню ссылку О компании`
```



`lit pull` получает задачи из jira и коммиты по ним из git
`lit pull [-j] [--jira]` только задачи 
`lit pull [-g] [--gitlab]` только коммиты по задачам 


`lit edit` открывает системным текстовым редактором файл .litstore

`lit config` показывает конфиг
`lit config add <key> <value>` добавляет запись 

