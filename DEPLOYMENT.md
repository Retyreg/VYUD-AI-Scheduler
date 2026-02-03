# 🚀 Руководство по развертыванию VYUD-AI-Scheduler

Это руководство описывает пошаговый процесс развертывания Streamlit приложения на Ubuntu сервере с использованием Docker, Nginx и SSL сертификатов от Let's Encrypt.

## 📋 Предварительные требования

- Ubuntu Server (20.04 или новее)
- Доступ к серверу через SSH с правами sudo
- Домен publish.vyud.tech с A-записью, указывающей на IP вашего сервера
- Открытые порты: 80 (HTTP) и 443 (HTTPS)

## 🔧 Шаг 1: Подготовка сервера

Подключитесь к серверу и обновите систему:

```bash
# Обновление пакетов
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y git curl nano
```

## 🐳 Шаг 2: Установка Docker и Docker Compose

### Установка Docker

```bash
# Удаление старых версий (если есть)
sudo apt remove docker docker-engine docker.io containerd runc

# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Применение изменений групп (или перелогиньтесь)
newgrp docker

# Проверка установки
docker --version
```

### Установка Docker Compose

```bash
# Загрузка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Установка прав на выполнение
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker-compose --version
```

## 📦 Шаг 3: Клонирование репозитория

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование репозитория
git clone https://github.com/Retyreg/VYUD-AI-Scheduler.git

# Переход в директорию проекта
cd VYUD-AI-Scheduler
```

## ⚙️ Шаг 4: Настройка переменных окружения

Создайте файл `.env` с вашими API ключами:

```bash
# Создание файла .env
nano .env
```

Добавьте следующие переменные (замените на ваши реальные значения):

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_PROFILE_ID=your_linkedin_profile_id_here
GROQ_API_KEY=your_groq_api_key_here
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X).

## 🔐 Шаг 5: Получение SSL сертификата (Let's Encrypt)

### Временная настройка Nginx для Certbot

Сначала нужно получить SSL сертификат. Для этого временно изменим конфигурацию Nginx:

```bash
# Создание директорий для Certbot
mkdir -p certbot/conf certbot/www

# Создание временной конфигурации Nginx
cat > nginx-temp.conf << 'EOF'
server {
    listen 80;
    server_name publish.vyud.tech;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'Server is running';
        add_header Content-Type text/plain;
    }
}
EOF
```

### Временный запуск Nginx для получения сертификата

```bash
# Запуск Nginx в Docker для Certbot
docker run --rm -d \
  --name nginx-temp \
  -p 80:80 \
  -v $(pwd)/nginx-temp.conf:/etc/nginx/conf.d/default.conf \
  -v $(pwd)/certbot/www:/var/www/certbot \
  nginx:alpine

# Проверка, что Nginx запущен
docker ps | grep nginx-temp
```

### Получение SSL сертификата

```bash
# Запуск Certbot для получения сертификата
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d publish.vyud.tech

# Остановка временного Nginx
docker stop nginx-temp
```

**Важно:** Замените `your-email@example.com` на ваш реальный email.

## 🚀 Шаг 6: Запуск приложения

Теперь, когда у нас есть SSL сертификат, запустим полный стек:

```bash
# Сборка и запуск контейнеров
docker-compose up -d --build

# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### Проверка работы приложения

```bash
# Проверка логов приложения
docker-compose logs app

# Проверка логов Nginx
docker-compose logs nginx

# Проверка health check
curl http://localhost:8501/_stcore/health
```

## 🌐 Шаг 7: Проверка доступности

Откройте браузер и перейдите по адресу:
- HTTP: http://publish.vyud.tech (должен редиректить на HTTPS)
- HTTPS: https://publish.vyud.tech

Вы должны увидеть интерфейс Streamlit приложения.

## 🔄 Управление приложением

### Основные команды Docker Compose

```bash
# Просмотр статуса контейнеров
docker-compose ps

# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f app
docker-compose logs -f nginx

# Остановка всех контейнеров
docker-compose down

# Перезапуск всех контейнеров
docker-compose restart

# Перезапуск конкретного контейнера
docker-compose restart app

# Обновление приложения (после git pull)
git pull
docker-compose up -d --build

# Очистка неиспользуемых образов
docker system prune -a
```

## 🔄 Автоматическое обновление SSL сертификата

SSL сертификат будет автоматически обновляться благодаря контейнеру `certbot` в docker-compose.yml. Certbot проверяет необходимость обновления каждые 12 часов.

Проверить статус сертификата можно командой:

```bash
docker-compose exec certbot certbot certificates
```

## 📊 Мониторинг

### Проверка использования ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
df -h

# Логи системы
journalctl -u docker -f
```

## 🛠️ Устранение неполадок

### Приложение не запускается

```bash
# Проверьте логи
docker-compose logs app

# Проверьте переменные окружения
docker-compose exec app env | grep -E "TELEGRAM|LINKEDIN|GROQ"

# Пересоздайте контейнеры
docker-compose down
docker-compose up -d --build
```

### Nginx не проксирует запросы

```bash
# Проверьте логи Nginx
docker-compose logs nginx

# Проверьте конфигурацию Nginx
docker-compose exec nginx nginx -t

# Перезагрузите Nginx
docker-compose restart nginx
```

### SSL сертификат не работает

```bash
# Проверьте наличие сертификатов
ls -la certbot/conf/live/publish.vyud.tech/

# Проверьте логи Certbot
docker-compose logs certbot

# Попробуйте получить сертификат вручную
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d publish.vyud.tech
```

### WebSocket не работает

Убедитесь, что в nginx.conf присутствуют следующие директивы:
```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Файрволл**: Настройте UFW для разрешения только необходимых портов:

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
sudo ufw status
```

2. **Обновления**: Регулярно обновляйте систему и Docker образы:

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Docker образов
docker-compose pull
docker-compose up -d
```

3. **Резервное копирование**: Настройте резервное копирование базы данных:

```bash
# Создание бэкапа базы данных
cp posts.db posts.db.backup-$(date +%Y%m%d-%H%M%S)

# Автоматический бэкап (добавьте в crontab)
0 2 * * * cd ~/VYUD-AI-Scheduler && cp posts.db posts.db.backup-$(date +\%Y\%m\%d) && find . -name "posts.db.backup-*" -mtime +7 -delete
```

4. **Защита .env файла**:

```bash
chmod 600 .env
```

## 📝 Дополнительная информация

- **Порты**: Приложение работает на порту 8501 внутри контейнера
- **Домен**: publish.vyud.tech
- **SSL**: Автоматическое обновление через Let's Encrypt
- **Перезапуск**: Все контейнеры настроены на автоматический перезапуск (restart: always)

## 🆘 Получение помощи

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус контейнеров: `docker-compose ps`
3. Проверьте конфигурацию Nginx: `docker-compose exec nginx nginx -t`
4. Откройте issue в репозитории GitHub

## 📚 Полезные ссылки

- [Документация Docker](https://docs.docker.com/)
- [Документация Docker Compose](https://docs.docker.com/compose/)
- [Документация Streamlit](https://docs.streamlit.io/)
- [Документация Let's Encrypt](https://letsencrypt.org/docs/)
- [Документация Nginx](https://nginx.org/ru/docs/)
