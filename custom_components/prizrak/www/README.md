# Prizrak Car Card Resources

SVG файлы для визуализации автомобиля в Home Assistant.

## Автоматическая установка

SVG файлы автоматически копируются в `/config/www/prizrak/` при установке интеграции.

## Файлы

### car-full.svg
Полное изображение автомобиля (вид сверху) для центрального блока карточки.
- Размер: 120x180px
- Используется как основное изображение в `picture-elements` карточке

### car-perimeter.svg
Периметр охраны - контур автомобиля с голубой заливкой.
- Отображается поверх car-full.svg когда охрана включена
- Цвет: #4cb2f1 с прозрачностью 0.3
- Автоматически скрывается при выключенной охране

## Использование в карточке

Полный пример карточки доступен в `examples/car-card.yaml`:

```yaml
- type: picture-elements
  image: /local/prizrak/car-full.svg
  elements:
    # Guard perimeter overlay
    - type: conditional
      conditions:
        - entity: binary_sensor.prizrak_[ID]_guard
          state: "on"
      elements:
        - type: image
          image: /local/prizrak/car-perimeter.svg
```

## Требования

Для работы примера карточки необходимо установить через HACS:
1. **card-mod** - для стилизации карточек
2. **button-card** - для интерактивных кнопок управления

Подробные инструкции в `examples/README.md`.

## Кастомизация

Вы можете редактировать SVG файлы в `/config/www/prizrak/` для изменения:
- Формы автомобиля
- Цветов периметра охраны
- Размеров элементов

**Примечание:** После обновления интеграции SVG файлы будут перезаписаны. Создайте резервные копии ваших изменений.
