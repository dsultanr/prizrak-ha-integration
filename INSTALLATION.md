# Инструкция по установке Prizrak HA Integration

## Вариант 1: Локальная установка

### Шаг 1: Копирование файлов
```bash
# Скопируйте папку custom_components/prizrak в директорию Home Assistant
cp -r prizrak-ha /path/to/homeassistant/custom_components/

# Например, если Home Assistant установлен в /home/homeassistant/.homeassistant:
cp -r prizrak-ha /home/homeassistant/.homeassistant/custom_components/
```

### Шаг 2: Перезапуск Home Assistant
```bash
# Перезапустите Home Assistant
sudo systemctl restart home-assistant@homeassistant

# Или через UI: Settings → System → Restart
```

### Шаг 3: Добавление интеграции
1. Откройте Home Assistant
2. Перейдите в **Settings** → **Devices & Services**
3. Нажмите **"+ ADD INTEGRATION"**
4. Найдите **"Prizrak Monitoring"**
5. Введите email и пароль от monitoring.tecel.ru
6. Нажмите **Submit**

## Вариант 2: Установка через HACS

### Предварительные требования
1. Установлен HACS в Home Assistant

### Шаги:

#### 1. Добавьте в HACS
1. Откройте HACS в Home Assistant
2. Перейдите в "Integrations"
3. Нажмите три точки (⋮) → "Custom repositories"
4. URL: `https://github.com/dsultanr/prizrak-ha-integration`
5. Category: "Integration"
6. Нажмите "Add"

#### 2. Установите интеграцию
1. Найдите "Prizrak Monitoring" в HACS
2. Нажмите "Download"
3. Перезапустите Home Assistant
4. Добавьте интеграцию через Settings → Devices & Services

## Проверка установки

### 1. Проверьте логи
```bash
# Откройте логи Home Assistant
tail -f /home/homeassistant/.homeassistant/home-assistant.log | grep prizrak
```

### 2. Проверьте наличие сенсоров
1. Перейдите в **Developer Tools** → **States**
2. Найдите сенсоры `sensor.prizrak_*`, `binary_sensor.prizrak_*`, `button.prizrak_*`

### 3. Проверьте устройства
1. Перейдите в **Settings** → **Devices & Services** → **Prizrak Monitoring**
2. Должны отображаться ваши устройства

## Удаление интеграции

### Через UI (рекомендуется)
1. Settings → Devices & Services
2. Найдите "Prizrak Monitoring"
3. Нажмите три точки (⋮) → "Delete"

### Вручную
```bash
# Удалите папку интеграции
rm -rf /path/to/homeassistant/custom_components/prizrak

# Перезапустите Home Assistant
sudo systemctl restart home-assistant@homeassistant
```

## Устранение проблем

### Интеграция не появляется в списке
1. Проверьте, что папка `custom_components/prizrak-ha` существует
2. Проверьте права доступа: `chmod -R 755 custom_components/prizrak-ha`
3. Перезапустите Home Assistant
4. Очистите кеш браузера (Ctrl+Shift+R)

### Ошибки аутентификации
1. Проверьте правильность email/пароля на monitoring.tecel.ru
2. Убедитесь, что аккаунт активен
3. Проверьте логи: Settings → System → Logs

### Сенсоры показывают "unavailable"
1. Проверьте подключение к интернету
2. Проверьте доступность monitoring.tecel.ru
3. Проверьте логи на наличие WebSocket ошибок
4. Попробуйте удалить и заново добавить интеграцию

## Дополнительная информация

- **Документация**: [README.md](README.md)
- **GitHub**: https://github.com/dsultanr/prizrak-ha-integration
- **Issues**: https://github.com/dsultanr/prizrak-ha-integration/issues
