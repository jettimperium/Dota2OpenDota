"""Доступ к OpenDota API.

Здесь сохранена логика исходного скрипта. Добавлены только:
- таймауты для запросов матчей и статистики героев;
- отдельная функция get_heroes() для однократной загрузки справочника;
- загрузка полной карточки матча с журналами вардов;
- запрос парсинга матча на стороне OpenDota.
"""

from __future__ import annotations

import sys
import time

import requests

BASE_URL = "https://api.opendota.com/api"


def get_player_info(account_id, retries=3):
    """Получает базовую информацию о профиле игрока с повторами при сбое."""
    url = f"{BASE_URL}/players/{account_id}"
    for attempt in range(retries):
        try:
            # timeout=(соединение, чтение) — 5 сек на соединение, 15 сек на ответ
            response = requests.get(url, timeout=(5, 15))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"Попытка {attempt + 1} из {retries}: таймаут, ждём...")
            time.sleep(2 * (attempt + 1))  # пауза 2с, 4с, 6с
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении профиля: {e}")
            return None
    print("Не удалось получить ответ от OpenDota после нескольких попыток.")
    return None


def get_recent_matches(account_id, limit=20):
    """Получает последние матчи игрока."""
    url = f"{BASE_URL}/players/{account_id}/matches"
    params = {"limit": limit}
    try:
        response = requests.get(url, params=params, timeout=(5, 20))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении матчей: {e}")
        return []


def get_hero_stats(account_id):
    """Получает статистику по героям за все время."""
    url = f"{BASE_URL}/players/{account_id}/heroes"
    try:
        response = requests.get(url, timeout=(5, 20))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении статистики героев: {e}")
        return []


def get_hero_name(hero_id):
    """Преобразует ID героя в имя (используем публичный справочник)."""
    # Простой словарь для самых популярных героев или запрос к API констант
    # Для простоты здесь используем запрос к константам, если нужно точное имя
    # Но чтобы не делать лишний запрос, можно захардкодить основные или использовать API
    try:
        # Получаем список героев (кешируется на стороне OpenDota, но мы делаем запрос)
        resp = requests.get(f"{BASE_URL}/heroes", timeout=(5, 20))
        heroes = resp.json()
        for h in heroes:
            if h["id"] == hero_id:
                return h["localized_name"]
    except:
        pass
    return f"Герой ID {hero_id}"


def get_heroes():
    """Возвращает справочник героев OpenDota.

    В отличие от get_hero_name(), вызывается один раз на загрузку экрана.
    """
    try:
        response = requests.get(f"{BASE_URL}/heroes", timeout=(5, 20))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении справочника героев: {e}")
        return []


def get_match_details(match_id, retries=2):
    """Загружает полную карточку матча, включая obs_log/sen_log.

    OpenDota кладёт журналы вардов в объект каждого игрока. Для
    неразобранных матчей этих полей нет.
    """
    url = f"{BASE_URL}/matches/{int(match_id)}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=(5, 30))
            if response.status_code == 404:
                print(f"Матч {match_id} не найден в OpenDota.")
                return None
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else None
        except requests.exceptions.Timeout:
            print(f"Попытка {attempt + 1} из {retries}: таймаут карточки матча, ждём...")
            time.sleep(1.5 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении матча {match_id}: {e}")
            return None
    print(f"Не удалось загрузить матч {match_id} после нескольких попыток.")
    return None


def request_match_parse(match_id):
    """Просит OpenDota разобрать матч. Возвращает (успех, сообщение)."""
    url = f"{BASE_URL}/request/{int(match_id)}"
    try:
        response = requests.post(url, timeout=(5, 20))
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as e:
        return False, f"OpenDota недоступна: {e}"
    except ValueError:
        return False, "OpenDota вернула неожиданный ответ."

    if isinstance(payload, dict) and payload.get("job"):
        return True, "Запрос на парсинг отправлен."
    if isinstance(payload, dict) and payload.get("error"):
        return False, str(payload["error"])
    return False, "OpenDota не приняла запрос на парсинг."


def main():
    if len(sys.argv) > 1:
        account_id = sys.argv[1]
    else:
        account_id = input("Введите ID профиля игрока (Steam32, например 86745912): ").strip()

    if not account_id.isdigit():
        print("ID должен быть числом.")
        return

    account_id = int(account_id)

    print(f"\n--- Загрузка данных для ID: {account_id} ---")

    # 1. Информация об игроке
    player = get_player_info(account_id)
    if player:
        name = player.get("profile", {}).get("personaname", "Неизвестно")
        print(f"Игрок: {name}")
    else:
        print("Не удалось загрузить профиль. Проверьте ID.")
        return

    # 2. Последние 20 матчей
    print("\n--- Последние 20 матчей ---")
    matches = get_recent_matches(account_id, 20)

    if not matches:
        print("Нет данных о матчах (возможно, скрыта история).")
    else:
        wins = 0
        total_kills = 0
        total_deaths = 0
        total_assists = 0

        print(f"{'Герой':<20} {'Результат':<10} {'K/D/A':<12} {'Длительность'}")
        print("-" * 60)

        for m in matches:
            # Определение победы (radiant_win и слот игрока)
            # В player_slot: 0-4 = Radiant, 128-132 = Dire
            is_radiant = m.get("player_slot", 0) < 128
            radiant_win = m.get("radiant_win", False)
            win = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)

            if win:
                wins += 1
                result = "Победа"
            else:
                result = "Поражение"

            kills = m.get("kills", 0)
            deaths = m.get("deaths", 0)
            assists = m.get("assists", 0)

            total_kills += kills
            total_deaths += deaths
            total_assists += assists

            hero_name = get_hero_name(m.get("hero_id"))
            duration_min = m.get("duration", 0) // 60

            print(f"{hero_name:<20} {result:<10} {kills}/{deaths}/{assists:<6} {duration_min} мин")

        # Итоги по 20 матчам
        avg_kda = (total_kills + total_assists) / max(1, total_deaths)
        winrate = (wins / len(matches)) * 100
        print("-" * 60)
        print(f"Итог за 20 игр: {wins} побед / {len(matches) - wins} поражений (Винрейт: {winrate:.1f}%)")
        print(f"Средний KDA: {avg_kda:.2f}")

    # 3. Топ героев за все время
    print("\n--- Топ героев по количеству матчей (за все время) ---")
    hero_stats = get_hero_stats(account_id)

    if not hero_stats:
        print("Нет данных по героям.")
    else:
        # Сортируем по games (количество игр) по убыванию
        sorted_heroes = sorted(hero_stats, key=lambda x: x.get("games", 0), reverse=True)

        print(f"{'Герой':<20} {'Матчей':<10} {'Побед':<10} {'Винрейт'}")
        print("-" * 55)

        for h in sorted_heroes[:10]:  # Показываем топ-10
            hero_name = get_hero_name(h.get("hero_id"))
            games = h.get("games", 0)
            wins_hero = h.get("win", 0)
            wr = (wins_hero / games * 100) if games > 0 else 0
            print(f"{hero_name:<20} {games:<10} {wins_hero:<10} {wr:.1f}%")


if __name__ == "__main__":
    main()
