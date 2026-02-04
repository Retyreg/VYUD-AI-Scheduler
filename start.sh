#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== VYUD-AI-Scheduler Quick Start ===${NC}"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не установлен. Пожалуйста, установите Docker сначала.${NC}"
    echo "Инструкции: https://docs.docker.com/engine/install/"
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose не установлен. Пожалуйста, установите Docker Compose сначала.${NC}"
    echo "Инструкции: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker установлен${NC}"
echo -e "${GREEN}✓ Docker Compose установлен${NC}"
echo ""

# Проверка .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}Файл .env не найден. Создаём из .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠ Пожалуйста, отредактируйте файл .env и добавьте ваши API ключи${NC}"
        echo -e "${YELLOW}  nano .env${NC}"
        exit 1
    else
        echo -e "${RED}Файл .env.example не найден!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Файл .env найден${NC}"
echo ""

# Создание директорий для Certbot
echo -e "${YELLOW}Создание директорий для SSL сертификатов...${NC}"
mkdir -p certbot/conf certbot/www

# Проверка наличия SSL сертификатов
if [ ! -d "certbot/conf/live/publish.vyud.tech" ]; then
    echo -e "${YELLOW}⚠ SSL сертификаты не найдены${NC}"
    echo -e "${YELLOW}Перед запуском приложения необходимо получить SSL сертификат${NC}"
    echo -e "${YELLOW}Следуйте инструкциям в DEPLOYMENT.md (Шаг 5)${NC}"
    echo ""
    echo -e "${YELLOW}Хотите запустить приложение БЕЗ SSL (только для тестирования)? (y/n)${NC}"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 0
    fi
    
    # Создание временной конфигурации Nginx без SSL
    echo -e "${YELLOW}Создание временной конфигурации Nginx без SSL...${NC}"
    cat > nginx-nossl.conf << 'EOF'
upstream streamlit {
    server app:8501;
}

server {
    listen 80;
    server_name publish.vyud.tech;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 86400;
        proxy_connect_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffering off;
    }
}
EOF
    
    # Обновление docker-compose для использования временной конфигурации
    sed -i 's|./nginx.conf|./nginx-nossl.conf|g' docker-compose.yml
fi

echo ""
echo -e "${GREEN}Сборка и запуск Docker контейнеров...${NC}"
docker-compose up -d --build

echo ""
echo -e "${GREEN}Проверка статуса контейнеров...${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}=== Приложение запущено! ===${NC}"
echo -e "Доступ к приложению:"
if [ -d "certbot/conf/live/publish.vyud.tech" ]; then
    echo -e "  HTTPS: ${GREEN}https://publish.vyud.tech${NC}"
fi
echo -e "  HTTP:  ${GREEN}http://publish.vyud.tech${NC} (или http://localhost если на локальной машине)"
echo ""
echo -e "Полезные команды:"
echo -e "  Просмотр логов:        ${YELLOW}docker-compose logs -f${NC}"
echo -e "  Остановка:             ${YELLOW}docker-compose down${NC}"
echo -e "  Перезапуск:            ${YELLOW}docker-compose restart${NC}"
echo -e "  Обновление:            ${YELLOW}git pull && docker-compose up -d --build${NC}"
echo ""
echo -e "Полная документация: ${YELLOW}DEPLOYMENT.md${NC}"
