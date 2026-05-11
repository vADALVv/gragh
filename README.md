<div align="center">

# 🧠 Multi-Agent Information Diffusion Simulator

<img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+"/>
<img src="https://img.shields.io/badge/torch-2.4.1-red" alt="PyTorch"/>
<img src="https://img.shields.io/badge/transformers-4.46.0-green" alt="Transformers"/>
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="MIT"/>

<br>

### 🌐 Multi-Agent Information Diffusion & Cognitive Dynamics Framework

**Мультиагентный симулятор распространения информации**  
для исследования:

🧠 когнитивной динамики  
🔥 эмоционального заражения  
🛡 AI Safety и анализа угроз  
📡 информационных каскадов  
🤖 поведения LLM-агентов  
📊 социальной динамики  

---

</div>

# 📑 Оглавление

<div align="center">

| Раздел | Описание |
|---|---|
| [📌 Обзор](#-обзор) | Концепция симулятора |
| [✨ Возможности](#-возможности) | Основные функции |
| [🧱 Архитектура](#-архитектура) | Устройство системы |
| [🛠 Установка](#-установка) | Подготовка окружения |
| [🚀 Запуск симуляции](#-запуск-симуляции) | Запуск проекта |
| [📊 Выходные данные](#-выходные-данные) | Формат результатов |
| [📋 Полное описание параметров](#-полное-описание-параметров) | Все параметры модели |
| [🧠 Расширенное использование](#-расширенное-использование) | Advanced usage |
| [📁 Структура проекта](#-структура-проекта) | Организация файлов |
| [📄 Лицензия](#-лицензия) | Условия использования |
| [🙏 Благодарности](#-благодарности) | Используемые технологии |

</div>

---

# 🌌 Общее описание

Современные информационные системы представляют собой сложные динамические сети, в которых распространение контента определяется не только структурой связей между пользователями, но и:

- эмоциональным состоянием участников;
- когнитивными особенностями;
- уровнем доверия;
- манипулятивными воздействиями;
- активностью автоматизированных агентов;
- алгоритмами искусственного интеллекта.

Данный проект реализует **исследовательскую платформу** для моделирования подобных процессов в виде мультиагентной системы.

---

# 🧠 Ключевая идея

Каждый пользователь сети моделируется как автономный агент, обладающий:

| Параметр | Интерпретация |
|---|---|
| `b` | убеждения / bias |
| `c` | устойчивость взглядов |
| `e` | эмоциональное состояние |

Поведение агента определяется:

- согласованностью сообщения с его взглядами;
- эмоциональной нагрузкой контента;
- силой социальных связей;
- текущим эмоциональным состоянием.

---

# ✨ Возможности

<div align="center">

| Возможность | Описание |
|---|---|
| 🌐 Small-World Graph | Генерация реалистичных социальных графов |
| 🔁 Information Diffusion | Моделирование распространения сообщений |
| 🧠 Cognitive Dynamics | Эволюция убеждений агентов |
| 🔥 Emotional Contagion | Эмоциональное заражение |
| 🤖 LLM Agents | Автономные AI-агенты |
| 🛡 Blue Agent | Анализ угроз и рисков |
| 📊 Interactive Visualization | HTML-визуализация графа |
| ⏳ Timeline Simulation | Таймлайн распространения |
| 💾 JSON Export | Полное сохранение симуляции |
| ⚡ GPU Support | CUDA + 4-bit quantization |

</div>

---

# 🧱 Архитектура системы

```text
                ┌─────────────────────┐
                │   graph_structure    │
                │    создание графа    │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    simulation.py     │
                │  диффузия сообщений  │
                └──────────┬───────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ Красные  │      │Пользова- │      │ LLM-     │
   │ агенты R │      │ тели U   │      │агенты L  │
   └──────────┘      └──────────┘      └──────────┘
                                       (опционально)
                           │
                           ▼
                ┌─────────────────────┐
                │    Blue Agent        │
                │ анализ рисков        │
                └──────────┬───────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   visualization.py   │
                │  HTML + JS           │
                └──────────────────────┘
```

---

# 📦 Основные модули

| Модуль | Назначение |
|---|---|
| `graph_structure.py` | Генерация social graph и инициализация агентов |
| `simulation.py` | Диффузия сообщений и динамика сети |
| `blue_agent.py` | Transformer-based анализ рисков |
| `llm_agents.py` | Генерация сообщений через LLM |
| `visualization.py` | Интерактивная визуализация |
| `run.py` | Главный pipeline симуляции |

---

# 🛠 Установка

## 📌 Требования

| Компонент | Версия |
|---|---|
| Python | 3.11+ |
| PyTorch | 2.4.1 |
| Transformers | 4.46.0 |
| CUDA | рекомендуется |
| RAM | 8+ GB |

---

## 📥 Клонирование репозитория

```bash
git clone https://github.com/yourusername/llm_attaks.git
cd llm_attaks/graph/src
```

---

## 🧪 Создание виртуального окружения

### Linux / MacOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 📦 Установка зависимостей

### requirements.txt

```bash
pip install -r requirements.txt
```

---

### Ручная установка

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

pip install \
    transformers \
    peft \
    bitsandbytes \
    networkx \
    pyvis \
    tqdm \
    numpy
```

---

# 🚀 Запуск симуляции

## ⚙️ Настройка параметров

В `run.py`:

```python
N_USERS = 7
N_RED = 3
N_LLM = 0

AVG_DEGREE = 3
T_STEPS = 4
```

---

## ▶️ Запуск

```bash
python run.py
```

---

# 📊 Выходные данные

После выполнения автоматически создаётся директория:

```text
results/
```

---

## Содержимое

| Файл | Назначение |
|---|---|
| `simulation_result.json` | Полная история симуляции |
| `network_visualization_pro.html` | Интерактивный HTML-граф |

---

# 🌐 Визуализация

## Типы узлов

<div align="center">

| Тип | Цвет | Форма |
|---|---|---|
| 👤 User | Голубой | Круг |
| 🔴 Red Agent | Красный | Квадрат |
| 🤖 LLM Agent | Жёлтый | Треугольник |

</div>

---

## Возможности интерфейса

- 🔍 Zoom
- 🖱 Drag & Drop
- ⏳ Timeline animation
- 📈 История состояний
- 🔗 Просмотр сообщений по рёбрам
- ⚙️ Настройка physics
- 🎬 Пошаговая анимация каскадов

---

# 📋 Полное описание параметров

## 7.1 Параметры графа

| Параметр | Тип | Диапазон | Default | Описание |
|---|---|---|---|---|
| `num_u` | int | ≥1 | 7 | Количество пользователей |
| `num_r` | int | ≥0 | 3 | Количество red-агентов |
| `num_l` | int | ≥0 | 0 | Количество LLM-агентов |
| `avg_degree` | int | ≥1 | 3 | Средняя степень узла |
| `SEED` | int | любое | 42 | Seed генератора |

---

## 7.2 Параметры симуляции

| Параметр | Default | Описание |
|---|---|
| `T_steps` | 4 | Количество временных шагов |
| `decay` | 0.85 | Затухание сообщений |
| `max_age` | 5 | Максимальный возраст сообщения |

---

## 7.3 RepostParams

### Вероятность репоста

```text
p = sigmoid(
    lambda0 +
    lambda1 * kappa +
    lambda2 * e +
    lambda3 * h +
    lambda4 * rel
)
```

---

### Формула согласия

```text
kappa = exp(-alpha * abs(b_m - b_i))
```

---

### Обновление убеждений

```text
b_new = b + c * beta * kappa * (b_msg - b)
```

---

# 🧠 Расширенное использование

## 🤖 LLM-агенты

Поддерживаемая модель:

```text
TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

---

## ⚡ Batch Processing

```python
results = blue_agent.process_batch(texts)
```

---

# 📁 Структура проекта

```text
graph/
├── data/
│   └── messages.json
├── src/
│   ├── graph_structure.py
│   ├── simulation.py
│   ├── blue_agent.py
│   ├── llm_agents.py
│   ├── visualization.py
│   ├── run.py
│   ├── results/
│   │   ├── simulation_result.json
│   │   └── network_visualization_pro.html
│   └── __pycache__/
└── README.md
```

---

# 📄 Лицензия

Проект распространяется под лицензией MIT.

---

# 🙏 Благодарности

<div align="center">

| Technology | Purpose |
|---|---|
| Hugging Face | Transformer ecosystem |
| PyTorch | Deep Learning |
| NetworkX | Graph processing |
| PyVis | Interactive visualization |
| Transformers | NLP models |
| BitsAndBytes | Quantization |

</div>

---

# ⚠️ Disclaimer

Проект предназначен исключительно для:

- академических исследований;
- анализа информационных каскадов;
- исследований AI Safety;
- моделирования дезинформации;
- изучения когнитивной динамики;
- анализа поведения LLM-агентов.

---

<div align="center">

## 🌌 Information is not just transmitted.  
## It evolves through cognition, emotion and social structure.

</div>
