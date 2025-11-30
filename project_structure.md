
# Структура проекта Telegram-бота "Bru Cup"

Этот документ описывает структуру проекта, основанную на принципах Чистой Архитектуры (Clean Architecture) и SOLID. Такой подход позволяет создавать гибкое, масштабируемое и тестируемое приложение.

## Основные принципы

- **Разделение ответственностей (Separation of Concerns):** Проект разделен на слои, каждый из которых имеет свою четкую зону ответственности.
- **Инверсия зависимостей (Dependency Inversion):** Зависимости направлены от внешних слоев к внутренним. Внутренние слои ничего не знают о внешних.

## Структура директорий

```
bru_cup_bot/
├── src/
│   ├── api/                  # Presentation Layer (Telegram bot)
│   │   ├── handlers/         # Request handlers (grouped by feature)
│   │   │   ├── admin/
│   │   │   ├── errors/
│   │   │   ├── loyalty/
│   │   │   └── ordering/
│   │   ├── middlewares/      # Custom middlewares
│   │   ├── routers.py        # Assembly of all routers
│   │   └── __init__.py
│   │
│   ├── application/          # Application Layer (Use Cases)
│   │   ├── services/         # Services that orchestrate business logic
│   │   │   ├── user_service.py
│   │   │   ├── order_service.py
│   │   │   └── ...
│   │   └── __init__.py
│   │
│   ├── domain/               # Domain Layer (Entities & Core Logic)
│   │   ├── entities/         # Core business objects (e.g., User, Order, Product)
│   │   │   ├── user.py
│   │   │   ├── order.py
│   │   │   └── product.py
│   │   ├── repositories/     # Abstract repository interfaces
│   │   │   ├── user_repository.py
│   │   │   ├── order_repository.py
│   │   │   └── ...
│   │   └── __init__.py
│   │
│   └── infrastructure/       # Infrastructure Layer
│       ├── database/         # Database-related code
│       │   ├── repositories/ # Concrete repository implementations
│       │   │   ├── user_repository.py
│       │   │   └── order_repository.py
│       │   ├── models/       # ORM models (e.g., SQLAlchemy)
│       │   └── __init__.py
│       ├── cache/            # Caching (e.g., Redis for FSM)
│       └── __init__.py
│
├── tests/                    # Tests
│   ├── unit/
│   ├── integration/
│   └── __init__.py
│
├── migrations/               # Database migrations (e.g., Alembic)
│
├── .env                      # Environment variables
├── .gitignore
├── requirements.txt
├── docker-compose.yml        # For database and other services
└── main.py                   # Application entry point
```

## Описание слоев

### 1. `src/domain` (Domain Layer)

Самый внутренний и независимый слой. Он содержит бизнес-логику и сущности, которые не зависят от деталей реализации (базы данных, фреймворков).

- **`entities/`**: Определения основных бизнес-сущностей (например, `User`, `Order`, `Product`). Это простые Python-классы без какой-либо логики, специфичной для фреймворков.
- **`repositories/`**: Абстрактные интерфейсы (абстрактные базовые классы) для доступа к данным. Например, `AbstractUserRepository` определяет методы, такие как `get_by_id`, `add`, но не содержит их реализации.

### 2. `src/application` (Application Layer)

Этот слой содержит бизнес-сценарии (use cases) приложения. Он координирует `domain`-сущности для выполнения задач.

- **`services/`**: Сервисы, которые инкапсулируют логику конкретных операций. Например, `OrderService` будет содержать метод `create_order`, который принимает данные заказа, выполняет проверку и использует репозитории для сохранения заказа. Сервисы зависят от абстракций репозиториев из `domain` слоя.

### 3. `src/api` (Presentation Layer)

Внешний слой, отвечающий за взаимодействие с пользователем. В нашем случае это Telegram Bot API.

- **`handlers/`**: Обработчики сообщений и колбэков от Telegram (Aiogram). Они принимают данные от пользователя, вызывают соответствующие сервисы из `application` слоя и отправляют ответ пользователю.
- **`middlewares/`**: Промежуточное ПО для обработки входящих запросов (например, для аутентификации администратора).
- **`routers.py`**: Файл для агрегации всех роутеров из `handlers`.

### 4. `src/infrastructure` (Infrastructure Layer)

Этот слой содержит реализации для внешних зависимостей: базы данных, внешние API, кеш и т.д.

- **`database/`**: Все, что связано с базой данных (MySQL).
    - **`repositories/`**: Конкретные реализации репозиториев, определенных в `domain` слое. Например, `MySQLUserRepository` реализует `AbstractUserRepository` с использованием SQLAlchemy или другой ORM.
    - **`models/`**: Модели ORM (например, SQLAlchemy), которые отражают структуру таблиц в базе данных.
- **`cache/`**: Реализация кеширования, например, для машины состояний (FSM) в Aiogram с использованием Redis.

## Другие важные файлы и директории

- **`main.py`**: Точка входа в приложение. Здесь инициализируется бот, настраиваются зависимости (Dependency Injection) и запускается polling.
- **`tests/`**: Директория для тестов.
    - `unit/`: Модульные тесты для каждого слоя в изоляции.
    - `integration/`: Интеграционные тесты, проверяющие взаимодействие между слоями.
- **`migrations/`**: Директория для миграций базы данных (например, с использованием Alembic).
- **`.env`**: Файл для хранения конфигурационных переменных (токен бота, данные для подключения к БД и т.д.).
- **`requirements.txt`**: Список зависимостей Python.
- **`docker-compose.yml`**: Для удобного запуска окружения (например, базы данных MySQL и Redis).

## Как это работает вместе (Пример: создание заказа)

1.  **Пользователь** нажимает кнопку "Сделать заказ" в Telegram.
2.  **`api/handlers/ordering/`** ловит это событие. Он собирает необходимые данные (например, из состояния FSM).
3.  **Handler** вызывает метод `create_order` у **`application/services/order_service.py`**.
4.  **`OrderService`** выполняет бизнес-логику: создает `Order` **(entity)**, проверяет данные и вызывает метод `add` у **`domain/repositories/order_repository.py`** (абстрактного).
5.  DI-контейнер передает в `OrderService` конкретную реализацию репозитория — **`infrastructure/database/repositories/order_repository.py`**.
6.  **`MySQLOrderRepository`** с помощью ORM-модели сохраняет новый заказ в базу данных MySQL.
7.  Результат возвращается по цепочке обратно в **handler**, который отправляет пользователю подтверждение.
