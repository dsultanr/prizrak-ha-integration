# Prizrak Car Card

Готовая карточка для визуализации состояния автомобиля с системой Prizrak.

## Автоматическая установка

SVG файлы автоматически копируются в `/config/www/prizrak/` при установке интеграции.

## Использование карточки

1. Откройте Dashboard в режиме редактирования
2. Добавьте новую карточку → Вручную (Manual)
3. Скопируйте содержимое `prizrak-car-card.yaml`
4. Замените `95311` на ID вашего устройства
5. Сохраните

## Функции карточки

### Визуализация состояний

- **Guard ON**: Голубое свечение вокруг машины + закрытый замок
- **Guard OFF**: Серый контур + открытый замок
- **Autolaunch ON**: Белый контур + фары + стоп-сигналы + иконка двигателя
- **Открытые двери**: Желтая подсветка каждой двери

### Отображаемая информация

**По углам:**
- Верхний левый: Напряжение батареи
- Верхний правый: Температура двигателя
- Нижний левый: Уровень топлива
- Нижний правый: Температура снаружи

**По центру:**
- Температура в салоне
- Иконка замка (статус охраны)

**При автозапуске (внизу):**
- Скорость (слева)
- Обороты двигателя (справа)

## Кастомизация

Вы можете редактировать SVG файлы в `/config/www/prizrak/` для изменения:
- Формы автомобиля
- Цветов подсветки
- Размеров элементов

Все SVG имеют viewBox="0 0 400 600" для правильного наложения слоев.

## Пример с кнопками управления

```yaml
type: vertical-stack
cards:
  - type: picture-elements
    # ... содержимое prizrak-car-card.yaml ...

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
```
