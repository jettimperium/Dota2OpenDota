from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

RANK_NAMES = (
    "Herald",
    "Guardian",
    "Crusader",
    "Archon",
    "Legend",
    "Ancient",
    "Divine",
    "Immortal",
)
ROMAN = ("", "I", "II", "III", "IV", "V")
MONTHS_RU = ("янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def plural_ru(number: int, forms: tuple[str, str, str]) -> str:
    n = abs(int(number)) % 100
    if 11 <= n <= 19:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def games_text(count: int) -> str:
    return f"{count} {plural_ru(count, ('матч', 'матча', 'матчей'))}"


def wins_text(count: int) -> str:
    return f"{count} {plural_ru(count, ('победа', 'победы', 'побед'))}"


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def format_match_time(seconds: int) -> str:
    """Время матча, включая отрицательные варды до появления крипов."""
    seconds = int(seconds)
    if seconds < 0:
        return f"-{format_duration(-seconds)}"
    return format_duration(seconds)


def format_date(timestamp: int, with_year: bool = True) -> str:
    if not timestamp:
        return "—"
    dt = datetime.fromtimestamp(int(timestamp))
    if with_year:
        return dt.strftime("%d.%m.%Y")
    return f"{dt.day:02d} {MONTHS_RU[dt.month - 1]}"


def rank_label(rank_tier: int, leaderboard_rank: int | None = None) -> str:
    if rank_tier and 1 <= rank_tier // 10 <= 8:
        medal_index = (rank_tier // 10) - 1
        star = rank_tier % 10
        medal = RANK_NAMES[medal_index]
        if medal == "Immortal":
            if leaderboard_rank:
                return f"Immortal · #{leaderboard_rank}"
            return "Immortal"
        if 1 <= star <= 5:
            return f"{medal} {ROMAN[star]}"
        return medal
    return "Ранг не указан"


def initials(name: str) -> str:
    words = [item for item in name.replace("_", " ").split() if item]
    if not words:
        return "D2"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def hero_slug(hero_name: str) -> str:
    return (hero_name or "").removeprefix("npc_dota_hero_")


def hero_icon_url(slug: str) -> str:
    if not slug:
        return ""
    return (
        "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/"
        f"dota_react/heroes/{slug}.png"
    )


def entity_display_name(name: str) -> str:
    """npc_dota_hero_spirit_breaker -> Spirit Breaker."""
    raw = (name or "").strip()
    if raw.startswith("npc_dota_hero_"):
        raw = raw[len("npc_dota_hero_") :]
    display = raw.replace("_", " ").strip()
    return display.title() if display else "—"


@dataclass(slots=True)
class ProfileSummary:
    account_id: int
    name: str
    avatar_url: str
    country_code: str
    rank_label: str
    rank_tier: int
    leaderboard_rank: int | None
    mmr_estimate: int | None


@dataclass(slots=True)
class MatchItem:
    match_id: int
    hero_id: int
    hero_name: str
    hero_slug: str
    win: bool
    kills: int
    deaths: int
    assists: int
    duration: int
    start_time: int
    gpm: int
    xpm: int
    kda: float
    is_radiant: bool

    @property
    def kda_text(self) -> str:
        return f"{self.kills}/{self.deaths}/{self.assists}"

    @property
    def date_text(self) -> str:
        return format_date(self.start_time)


@dataclass(slots=True)
class WardPlacement:
    kind: str
    x: float
    y: float
    placed_at: int
    removed_at: int | None = None
    attackername: str = ""
    key: str = ""

    @property
    def is_observer(self) -> bool:
        return self.kind == "observer"

    @property
    def kind_title(self) -> str:
        return "Наблюдатель" if self.is_observer else "Сентри"

    @property
    def lifetime(self) -> int:
        # Observer Ward живёт 6 минут, Sentry Ward — 4 минуты.
        return 360 if self.is_observer else 240

    @property
    def expires_at(self) -> int:
        return self.placed_at + self.lifetime

    @property
    def ended_at(self) -> int:
        return self.removed_at if self.removed_at is not None else self.expires_at

    @property
    def was_removed(self) -> bool:
        return self.removed_at is not None

    def is_active_at(self, seconds: int) -> bool:
        return self.placed_at <= seconds < self.ended_at


@dataclass(slots=True)
class MatchWards:
    match_id: int
    duration: int
    parsed: bool
    player_found: bool
    wards: list[WardPlacement] = field(default_factory=list)

    @property
    def observer_count(self) -> int:
        return sum(1 for ward in self.wards if ward.is_observer)

    @property
    def sentry_count(self) -> int:
        return sum(1 for ward in self.wards if not ward.is_observer)

    @property
    def total(self) -> int:
        return len(self.wards)


@dataclass(slots=True)
class HeroItem:
    hero_id: int
    name: str
    slug: str
    games: int
    wins: int
    losses: int
    winrate: float


@dataclass(slots=True)
class DashboardData:
    account_id: int
    profile: ProfileSummary
    matches: list[MatchItem] = field(default_factory=list)
    heroes: list[HeroItem] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    winrate: float = 0.0
    avg_kda: float = 0.0
    avg_kills: float = 0.0
    avg_deaths: float = 0.0
    avg_assists: float = 0.0
    avg_gpm: int = 0
    avg_xpm: int = 0
    avg_duration: int = 0
    form: list[bool] = field(default_factory=list)
    total_hero_games: int = 0
    total_hero_wins: int = 0
    hero_overall_winrate: float = 0.0

    @property
    def favorite_hero(self) -> HeroItem | None:
        return self.heroes[0] if self.heroes else None


def _build_hero_map(heroes_raw: list[dict]) -> dict[int, dict]:
    result: dict[int, dict] = {}
    for hero in heroes_raw or []:
        hero_id = safe_int(hero.get("id"))
        if hero_id:
            result[hero_id] = hero
    return result


def build_dashboard(
    account_id: int,
    player_raw: dict,
    matches_raw: list[dict] | None,
    hero_stats_raw: list[dict] | None,
    heroes_raw: list[dict] | None,
) -> DashboardData:
    hero_map = _build_hero_map(heroes_raw or [])
    profile_raw = player_raw.get("profile") or {}
    name = profile_raw.get("personaname") or f"Игрок {account_id}"
    avatar_url = (
        profile_raw.get("avatarfull")
        or profile_raw.get("avatarmedium")
        or profile_raw.get("avatar")
        or ""
    )
    leaderboard_rank = player_raw.get("leaderboard_rank")
    try:
        leaderboard_rank = int(leaderboard_rank) if leaderboard_rank else None
    except (TypeError, ValueError):
        leaderboard_rank = None
    mmr_estimate = safe_int((player_raw.get("mmr_estimate") or {}).get("estimate"), default=0) or None
    rank_tier = safe_int(player_raw.get("rank_tier"), default=0)

    profile = ProfileSummary(
        account_id=account_id,
        name=name,
        avatar_url=avatar_url,
        country_code=(profile_raw.get("loccountrycode") or "").upper(),
        rank_label=rank_label(rank_tier, leaderboard_rank),
        rank_tier=rank_tier,
        leaderboard_rank=leaderboard_rank,
        mmr_estimate=mmr_estimate,
    )

    matches: list[MatchItem] = []
    for raw in matches_raw or []:
        hero_id = safe_int(raw.get("hero_id"))
        hero = hero_map.get(hero_id, {})
        hero_name = hero.get("localized_name") or f"Герой ID {hero_id}"
        is_radiant = safe_int(raw.get("player_slot"), 0) < 128
        radiant_win = bool(raw.get("radiant_win", False))
        win = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)
        kills = safe_int(raw.get("kills"))
        deaths = safe_int(raw.get("deaths"))
        assists = safe_int(raw.get("assists"))
        matches.append(
            MatchItem(
                match_id=safe_int(raw.get("match_id")),
                hero_id=hero_id,
                hero_name=hero_name,
                hero_slug=hero_slug(hero.get("name", "")),
                win=win,
                kills=kills,
                deaths=deaths,
                assists=assists,
                duration=safe_int(raw.get("duration")),
                start_time=safe_int(raw.get("start_time")),
                gpm=safe_int(raw.get("gold_per_min")),
                xpm=safe_int(raw.get("xp_per_min")),
                kda=(kills + assists) / max(1, deaths),
                is_radiant=is_radiant,
            )
        )

    matches.sort(key=lambda item: item.start_time, reverse=True)
    matches = matches[:20]

    wins = sum(1 for match in matches if match.win)
    losses = len(matches) - wins
    winrate = (wins / len(matches) * 100) if matches else 0.0
    total_kills = sum(match.kills for match in matches)
    total_deaths = sum(match.deaths for match in matches)
    total_assists = sum(match.assists for match in matches)
    avg_kda = (total_kills + total_assists) / max(1, total_deaths)
    match_count = max(1, len(matches))
    avg_kills = total_kills / match_count
    avg_deaths = total_deaths / match_count
    avg_assists = total_assists / match_count
    gpm_values = [match.gpm for match in matches if match.gpm > 0]
    xpm_values = [match.xpm for match in matches if match.xpm > 0]
    avg_gpm = round(sum(gpm_values) / len(gpm_values)) if gpm_values else 0
    avg_xpm = round(sum(xpm_values) / len(xpm_values)) if xpm_values else 0
    avg_duration = round(sum(match.duration for match in matches) / len(matches)) if matches else 0
    form = [match.win for match in list(reversed(matches[:10]))]

    heroes: list[HeroItem] = []
    for raw in hero_stats_raw or []:
        hero_id = safe_int(raw.get("hero_id"))
        games = safe_int(raw.get("games"))
        if not hero_id or games <= 0:
            continue
        hero = hero_map.get(hero_id, {})
        wins_count = safe_int(raw.get("win"))
        heroes.append(
            HeroItem(
                hero_id=hero_id,
                name=hero.get("localized_name") or f"Герой ID {hero_id}",
                slug=hero_slug(hero.get("name", "")),
                games=games,
                wins=wins_count,
                losses=max(0, games - wins_count),
                winrate=(wins_count / games * 100) if games else 0.0,
            )
        )
    heroes.sort(key=lambda item: (item.games, item.winrate), reverse=True)

    total_hero_games = sum(hero.games for hero in heroes)
    total_hero_wins = sum(hero.wins for hero in heroes)
    hero_overall_winrate = (total_hero_wins / total_hero_games * 100) if total_hero_games else 0.0

    return DashboardData(
        account_id=account_id,
        profile=profile,
        matches=matches,
        heroes=heroes,
        wins=wins,
        losses=losses,
        winrate=winrate,
        avg_kda=avg_kda,
        avg_kills=avg_kills,
        avg_deaths=avg_deaths,
        avg_assists=avg_assists,
        avg_gpm=avg_gpm,
        avg_xpm=avg_xpm,
        avg_duration=avg_duration,
        form=form,
        total_hero_games=total_hero_games,
        total_hero_wins=total_hero_wins,
        hero_overall_winrate=hero_overall_winrate,
    )


def build_match_wards(account_id: int, match_raw: dict | None) -> MatchWards:
    """Достаёт из полной карточки матча варды конкретного игрока.

    OpenDota отдаёт obs_log/sen_log только для разобранных матчей.
    Координаты x/y лежат в сетке 0..255 и совпадают с мини-картой Dota 2.
    """
    if not isinstance(match_raw, dict):
        return MatchWards(match_id=0, duration=0, parsed=False, player_found=False)

    account_id = safe_int(account_id)
    match_id = safe_int(match_raw.get("match_id"))
    duration = safe_int(match_raw.get("duration"))
    od_data = match_raw.get("od_data")
    has_parsed = bool(od_data.get("has_parsed")) if isinstance(od_data, dict) else False
    players = match_raw.get("players")
    if not isinstance(players, list):
        players = []

    player = None
    for candidate in players:
        if isinstance(candidate, dict) and safe_int(candidate.get("account_id")) == account_id:
            player = candidate
            break
    if player is None:
        return MatchWards(
            match_id=match_id,
            duration=duration,
            parsed=has_parsed,
            player_found=False,
        )

    wards: list[WardPlacement] = []
    for kind, log_key, left_key in (
        ("observer", "obs_log", "obs_left_log"),
        ("sentry", "sen_log", "sen_left_log"),
    ):
        logs = player.get(log_key)
        left_logs = player.get(left_key)
        if not isinstance(logs, list):
            logs = []
        if not isinstance(left_logs, list):
            left_logs = []

        left_by_handle: dict[int, dict] = {}
        for left in left_logs:
            if not isinstance(left, dict):
                continue
            handle = safe_int(left.get("ehandle"))
            if handle:
                left_by_handle[handle] = left

        for entry in logs:
            if not isinstance(entry, dict):
                continue
            x = safe_float(entry.get("x"), default=-1.0)
            y = safe_float(entry.get("y"), default=-1.0)
            if not (0.0 <= x <= 256.0 and 0.0 <= y <= 256.0):
                continue
            placed_at = safe_int(entry.get("time"))
            handle = safe_int(entry.get("ehandle"))
            left = left_by_handle.get(handle) if handle else None
            removed_at = safe_int(left.get("time")) if left else None
            if removed_at is not None and removed_at <= placed_at:
                removed_at = None
            attackername = str((left or {}).get("attackername") or "")
            wards.append(
                WardPlacement(
                    kind=kind,
                    x=x,
                    y=y,
                    placed_at=placed_at,
                    removed_at=removed_at,
                    attackername=attackername,
                    key=str(entry.get("key") or ""),
                )
            )

    wards.sort(key=lambda ward: (ward.placed_at, ward.kind))
    return MatchWards(
        match_id=match_id,
        duration=duration,
        parsed=bool(has_parsed or wards),
        player_found=True,
        wards=wards,
    )
