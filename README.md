# Интеграция Prizrak Monitoring для Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Интеграция Home Assistant для системы мониторинга автомобилей Prizrak (monitoring.tecel.ru).

## Возможности

- **Обновления в реальном времени** через WebSocket соединение
- **40+ сенсоров**, включая:
  - GPS локация (широта, долгота, высота, скорость, спутники)
  - Телеметрия (напряжение батареи, уровень топлива, температуры, обороты, одометр)
  - Безопасность (статус охраны, сигнализация)
  - GSM сигнал и баланс SIM-карты
  - Системы обогрева (сидения, стекла, зеркала, руль)
- **Бинарные сенсоры** для дверей, багажника, капота и замков
- **Кнопки управления** для охраны и автозапуска
- **Автоматическое переподключение** с мониторингом состояния соединения

## Установка

### HACS (Рекомендуется)

1. Откройте HACS в вашем Home Assistant
2. Перейдите в раздел "Интеграции"
3. Нажмите три точки в правом верхнем углу
4. Выберите "Пользовательские репозитории"
5. Добавьте URL репозитория: `https://github.com/dsultanr/prizrak-ha-integration`
6. Категория: "Интеграция"
7. Нажмите "Добавить"
8. Найдите "Prizrak Monitoring"
9. Нажмите "Загрузить"
10. Перезапустите Home Assistant

### Ручная установка

1. Скопируйте директорию `custom_components/prizrak` в директорию `custom_components` вашего Home Assistant
2. Перезапустите Home Assistant

## Настройка

1. Перейдите в **Настройки** → **Устройства и службы**
2. Нажмите **"+ ДОБАВИТЬ ИНТЕГРАЦИЮ"**
3. Найдите **"Prizrak Monitoring"**
4. Введите ваш **email и пароль от monitoring.tecel.ru**
5. Нажмите **Отправить**

Ваши устройства Prizrak появятся автоматически со всеми доступными сенсорами!

## Использование

### Страница устройства

После настройки все сенсоры и кнопки управления автоматически группируются на странице устройства:

1. Перейдите в **Настройки** → **Устройства и службы** → **Prizrak Monitoring**
2. Нажмите на ваше устройство (например, "Кодиак")
3. Вы увидите все сенсоры, кнопки и бинарные сенсоры

Home Assistant автоматически предложит добавить устройство в зону **"Garage"**.

### Добавление на Dashboard

Вы можете добавить entities на ваш dashboard несколькими способами:

**Вариант 1: Через GUI (рекомендуется)**
1. Откройте ваш Dashboard
2. Нажмите **"Редактировать"** (три точки справа вверху)
3. Нажмите **"+ Добавить карточку"**
4. Выберите карточку (например, "Entities" или "Picture Elements")
5. Добавьте нужные entities из списка

**Вариант 2: YAML конфигурация**

Пример карточки для dashboard:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Статус автомобиля
    entities:
      - entity: sensor.prizrak_95311_connection
      - entity: sensor.prizrak_95311_guard_status
      - entity: sensor.prizrak_95311_alarm_status
      - entity: sensor.prizrak_95311_battery_voltage
      - entity: sensor.prizrak_95311_gsm_signal
      - entity: sensor.prizrak_95311_last_update

  - type: horizontal-stack
    cards:
      - type: button
        name: Охрана Вкл
        entity: button.prizrak_95311_guard_on
        icon: mdi:shield-check
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.prizrak_95311_guard_on
      - type: button
        name: Охрана Выкл
        entity: button.prizrak_95311_guard_off
        icon: mdi:shield-off
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.prizrak_95311_guard_off

  - type: entities
    title: Двери и замки
    entities:
      - entity: binary_sensor.prizrak_95311_driver_door
      - entity: binary_sensor.prizrak_95311_passenger_door
      - entity: binary_sensor.prizrak_95311_rear_left_door
      - entity: binary_sensor.prizrak_95311_rear_right_door
      - entity: binary_sensor.prizrak_95311_trunk
      - entity: binary_sensor.prizrak_95311_hood
      - entity: binary_sensor.prizrak_95311_central_lock

  - type: entities
    title: Телеметрия
    entities:
      - entity: sensor.prizrak_95311_speed
      - entity: sensor.prizrak_95311_engine_rpm
      - entity: sensor.prizrak_95311_odometer
      - entity: sensor.prizrak_95311_fuel_level
      - entity: sensor.prizrak_95311_inside_temperature
      - entity: sensor.prizrak_95311_engine_temperature

  - type: map
    entities:
      - entity: sensor.prizrak_95311_latitude
    hours_to_show: 24
    aspect_ratio: "16:9"
```

**Примечание:** Замените `95311` на ID вашего устройства (можно узнать из логов или entity_id).

## Сенсоры

### GPS и местоположение
- Широта, Долгота
- Статус GPS
- Скорость GNSS
- Высота
- Количество спутников
- Азимут (направление по компасу)

### Телеметрия автомобиля
- Напряжение батареи
- Уровень топлива
- Температура в салоне
- Температура снаружи
- Температура двигателя
- Скорость
- Обороты двигателя
- Одометр

### Безопасность и статус
- Статус охраны
- Статус сигнализации
- Состояние подключения
- Зажигание
- Ручной тормоз

### Связь
- Уровень GSM сигнала
- Оператор SIM-карты
- Баланс SIM-карты

### Системы обогрева
- Обогрев водительского сиденья
- Обогрев пассажирского сиденья
- Обогрев задних сидений
- Обогрев переднего стекла
- Обогрев заднего стекла
- Обогрев зеркал
- Обогрев руля

### Бинарные сенсоры (Вкл/Выкл)
- Водительская дверь
- Пассажирская дверь
- Задняя левая дверь
- Задняя правая дверь
- Багажник
- Капот
- Центральный замок

## Кнопки управления

- **Охрана Вкл** - Включить систему охраны
- **Охрана Выкл** - Выключить систему охраны
- **Автозапуск Вкл** - Включить автозапуск двигателя
- **Автозапуск Выкл** - Выключить автозапуск двигателя

## Примеры автоматизаций

### Уведомление при открытии водительской двери

```yaml
automation:
  - alias: "Prizrak: Открыта водительская дверь"
    trigger:
      - platform: state
        entity_id: binary_sensor.my_car_driver_door
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Оповещение о машине"
          message: "Водительская дверь была открыта!"
```

### Включение охраны ночью

```yaml
automation:
  - alias: "Prizrak: Включить охрану ночью"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.my_car_guard_on
```

### Уведомление о низком заряде батареи

```yaml
automation:
  - alias: "Prizrak: Предупреждение о низком заряде батареи"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_car_battery_voltage
        below: 11.5
    action:
      - service: notify.mobile_app
        data:
          title: "Низкий заряд батареи автомобиля"
          message: "Напряжение батареи {{ states('sensor.my_car_battery_voltage') }}В"
```

### Уведомление при тревоге

```yaml
automation:
  - alias: "Prizrak: Сработала сигнализация"
    trigger:
      - platform: state
        entity_id: sensor.my_car_alarm
    condition:
      - condition: template
        value_template: "{{ states('sensor.my_car_alarm') not in ['Unknown', 'None', 'unavailable'] }}"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ ТРЕВОГА!"
          message: "Сигнализация: {{ states('sensor.my_car_alarm') }}"
          data:
            priority: high
```

### Отслеживание местоположения на карте

```yaml
# В configuration.yaml добавьте:
zone:
  - name: Дом
    latitude: 55.751244
    longitude: 37.618423
    radius: 100

automation:
  - alias: "Prizrak: Машина покинула дом"
    trigger:
      - platform: numeric_state
        entity_id: sensor.my_car_latitude
    condition:
      - condition: template
        value_template: >
          {% set lat = states('sensor.my_car_latitude') | float %}
          {% set lon = states('sensor.my_car_longitude') | float %}
          {% set distance = distance(lat, lon, 55.751244, 37.618423) %}
          {{ distance > 0.1 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Машина уехала"
          message: "Автомобиль покинул зону дома"
```

## Устранение неполадок

### Интеграция не загружается

1. Проверьте логи Home Assistant: **Настройки** → **Система** → **Логи**
2. Ищите ошибки, связанные с "prizrak"
3. Проверьте учетные данные на monitoring.tecel.ru

### Устройства не появляются

1. Подождите 30-60 секунд после добавления интеграции
2. Убедитесь, что устройства видны на monitoring.tecel.ru
3. Перезапустите Home Assistant
4. Проверьте логи на наличие ошибок подключения

### Сенсоры показывают "недоступен"

1. Проверьте интернет-соединение
2. Убедитесь, что monitoring.tecel.ru доступен
3. Проверьте логи Home Assistant на наличие ошибок WebSocket
4. Попробуйте удалить и заново добавить интеграцию

## Поддержка

- **Проблемы**: [GitHub Issues](https://github.com/dsultanr/prizrak-ha-integration/issues)
- **Обсуждения**: [GitHub Discussions](https://github.com/dsultanr/prizrak-ha-integration/discussions)

## Лицензия

Этот проект лицензирован под лицензией MIT - см. файл [LICENSE](LICENSE) для подробностей.

## Благодарности

[Поблагодарить](https://pay.cloudtips.ru/p/aa2fce54)

Создано [@dsultanr](https://github.com/dsultanr)

## Отказ от ответственности

Протестировано только на Призрак-8XL/Slim/7.6

Это неофициальная интеграция и не связана с компанией ТЭК электроникс или сервисом monitoring.tecel.ru.
