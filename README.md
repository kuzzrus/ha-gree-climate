# Gree Airy для Home Assistant

[![Последний релиз](https://img.shields.io/github/v/release/kuzzrus/ha-gree-climate?sort=semver)](https://github.com/kuzzrus/ha-gree-climate/releases)
[![Лицензия](https://img.shields.io/github/license/kuzzrus/ha-gree-climate)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Compatible-Home_Assistant_2026.3+-blue.svg)](https://www.home-assistant.io)

[![Проверка](https://github.com/kuzzrus/ha-gree-climate/actions/workflows/validate.yaml/badge.svg)](https://github.com/kuzzrus/ha-gree-climate/actions/workflows/validate.yaml)
[![Линтер](https://github.com/kuzzrus/ha-gree-climate/actions/workflows/lint.yml/badge.svg)](https://github.com/kuzzrus/ha-gree-climate/actions/workflows/lint.yml)

Интеграция Gree для Home Assistant с отдельным руководством по настройке Gree Airy. Она управляет кондиционерами Gree и устройствами других брендов, которые используют протокол Gree. Поддерживается работа через локальную сеть и облако Gree.

Этот репозиторий является изменённым форком
[HomeAssistant-GreeClimateComponent](https://github.com/RobHofmann/HomeAssistant-GreeClimateComponent).
За основу взята ветка `5.0-dev`, коммит `2865cdefc60800931c5cfb1bcf30fc450601fdec`.
Разработка этого форка началась 6 октября 2026 года.

## Документация

Полная документация находится в каталоге **[docs](docs/README.md)**:

- **[Документация пользователя](docs/README.md#user-documentation)**: установка, настройка, сущности, действия и устранение неполадок
- **[Документация разработчика](docs/README.md#developer-documentation)**: архитектура, протокол, конфигурационные записи и разработка

Быстрые ссылки:
[установка](docs/installation.md) · [Gree Airy](docs/gree-airy.md) · [настройка](docs/configuration.md) · [сущности](docs/entities.md) · [примеры автоматизаций](docs/automation-examples.md) · [устранение неполадок](docs/troubleshooting.md) · [поддерживаемые устройства](supported-devices.md) · [релизы](https://github.com/kuzzrus/ha-gree-climate/releases)

## Возможности интеграции

В Home Assistant уже есть встроенная интеграция `gree`, которая работает только через локальную сеть. Эта интеграция предлагает больше возможностей.

- **Локальное управление и облачное подключение.** По умолчанию устройства управляются по UDP в локальной сети. Облако Gree можно использовать для недоступных локально устройств, а также для получения имён и ключей шифрования во время настройки. Подробнее в разделе [способы подключения](docs/connection-methods.md).
- **Функции с пульта.** X-Fan, Health, Sleep, умный обогрев до 8 °C, энергосбережение, Anti Direct Blow, Fresh Air, управление влажностью, подсветка и яркость дисплея, звуковой сигнал, Turbo и Quiet. Функции представлены переключателями, списками выбора или режимами вентилятора. Подробнее в разделе [сущности](docs/entities.md).
- **Положения жалюзи.** Двенадцать вертикальных и семь горизонтальных режимов: фиксированные положения и частичные диапазоны качания.
- **Датчики.** Температура в помещении и снаружи, влажность и обнаружение неисправностей, если устройство передаёт эти данные. Внешний датчик может заменить показания самого кондиционера в климатической сущности. Это меняет только данные в Home Assistant. Сам кондиционер продолжает использовать встроенный датчик.
- **Работа между VLAN.** Для обнаружения можно указать дополнительные сети или адреса устройств. Опрос выполняется одноадресными запросами. Подробнее в разделе [локальное обнаружение](docs/configuration.md#local-discovery).
- **Системы VRF.** Контроллер с несколькими внутренними блоками обнаруживается и настраивается как отдельные устройства.
- **Поддержка разных прошивок.** Версия шифрования определяется автоматически. Допустимый размер запроса измеряется при привязке, поэтому работают и устройства, которые не принимают большие запросы. Изменившийся IP-адрес обновляется через DHCP или повторное обнаружение.
- **Удобная настройка.** Можно использовать интерфейс Home Assistant с повторной настройкой или блок `gree_custom:` в YAML. Подробнее в разделе [настройка](docs/configuration.md).
- **Диагностика.** Доступны выгрузка диагностических данных, уведомления о проблемах и два действия для чтения необработанных свойств устройства. Подробнее в разделе [действия](docs/actions.md).

## Быстрый запуск

### Шаг 1. Установка через HACS

Для установки требуется [HACS](https://hacs.xyz/). Нажмите кнопку ниже или добавьте
`https://github.com/kuzzrus/ha-gree-climate` как пользовательский репозиторий интеграции.

[![Открыть репозиторий в HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kuzzrus&repository=ha-gree-climate&category=integration)

1. Нажмите **Download**.
2. Перезапустите Home Assistant.

### Шаг 2. Добавление интеграции

[![Добавить интеграцию Gree Climate](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=gree_custom)

Также можно открыть **Настройки** > **Устройства и службы** > **Добавить интеграцию** и найти **Gree Climate**.

1. Выберите **Local network**, **Gree Cloud account** или оба способа подключения.
2. Выберите устройства из списка.
3. Проверьте параметры подключения и доступные функции каждого устройства. Настройки по умолчанию подходят для большинства кондиционеров.

### Шаг 3. Готово

Устройства появятся в разделе **Настройки** > **Устройства и службы** > **Gree Climate**. Для каждого устройства будут созданы климатическая сущность, датчики и переключатели. Описание доступно в разделе [сущности](docs/entities.md), а готовые идеи находятся в [примерах автоматизаций](docs/automation-examples.md).

**[Полное руководство по установке](docs/installation.md)** · **[Полное руководство по настройке](docs/configuration.md)**

## Помощь и поддержка

- **[Discord исходного проекта](https://discord.gg/JPcBkvRhTS)**: вопросы и общение с пользователями исходной интеграции. Ошибки этого форка следует сообщать в данном репозитории.
- **[Устранение неполадок](docs/troubleshooting.md)**: отладочное журналирование, уведомления о проблемах, частые ошибки и правила оформления отчёта об ошибке.
- **[Gree Airy](docs/gree-airy.md)**: настройка, соответствие функций и ограничения прошивки Wi-Fi.
- **[Ключ шифрования](docs/encryption-key.md)**: что делать, если интеграция не может получить ключ устройства автоматически.
- **[Поддерживаемые устройства](supported-devices.md)**: проверенные модели и инструкция по добавлению своей.
- **[Сообщить об ошибке](https://github.com/kuzzrus/ha-gree-climate/issues/new/choose)**: сначала прочитайте раздел [устранение неполадок](docs/troubleshooting.md), где указаны необходимые сведения.

## Участие в разработке

Предложения и исправления приветствуются. Начните с [правил участия](CONTRIBUTING.md) и [документации разработчика](docs/README.md#developer-documentation).

- **[Разработка](docs/development.md)**: devcontainer, линтеры, тесты, отладочные журналы и релизы.
- **[Архитектура](docs/architecture.md)**: расположение кода и жизненный цикл устройства.
- **[Описание протокола](docs/protocol.md)**: обмен данными с реальными устройствами.
- **[AGENTS.md](AGENTS.md)**: начальная инструкция для программных агентов.

Качество кода проверяется Ruff, Pylint, Mypy, тестами pytest для протокольного слоя и испытаниями на реальных устройствах.

## Лицензия

Проект распространяется по лицензии GNU General Public License v3.0. Подробнее в файле [LICENSE](LICENSE).

## Благодарности

Проект основан на работе авторов и участников следующих проектов:

- [HomeAssistant-GreeClimateComponent](https://github.com/RobHofmann/HomeAssistant-GreeClimateComponent): исходная интеграция и основа этого форка.
- [greeclimate-js](https://github.com/davo22/greeclimate-js): библиотека TypeScript для управления сплит-системами на основе протокола Gree.
- [greeclimate](https://github.com/davo22/greeclimate): асинхронная библиотека Python 3 для управления кондиционерами и тепловыми насосами Gree.
- [gree-remote](https://github.com/tomikaa87/gree-remote): описание протокола дистанционного управления кондиционерами Gree.
- [greeclimate](https://github.com/cmroche/greeclimate): пакет Python для управления сплит-системами Gree.
- [gree-api-client](https://github.com/luc10/gree-api-client): клиент Gree API на Python.
- [Документация разработчика Home Assistant](https://developers.home-assistant.io): официальные рекомендации и правила разработки.
