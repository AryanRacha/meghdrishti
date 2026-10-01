from app.services.threat_detector import HAZARDS, grade


def test_rain_grades_follow_imd() -> None:
    assert grade(HAZARDS["rain"], 70.0) == ("heavy", 1)
    assert grade(HAZARDS["rain"], 115.6) == ("very_heavy", 2)
    assert grade(HAZARDS["rain"], 250.0) == ("extremely_heavy", 3)


def test_wind_grades() -> None:
    assert grade(HAZARDS["wind"], 45.0) == ("strong_wind", 1)
    assert grade(HAZARDS["wind"], 62.0) == ("gale", 2)
    assert grade(HAZARDS["wind"], 95.0) == ("storm", 3)


def test_heat_watch_below_floor_still_level_one() -> None:
    # The relative watch threshold can sit above the 30 °C floor; grading starts at level 1
    assert grade(HAZARDS["temp"], 33.0) == ("heat_watch", 1)
    assert grade(HAZARDS["temp"], 41.0) == ("heatwave", 2)
    assert grade(HAZARDS["temp"], 46.0) == ("severe_heatwave", 3)
